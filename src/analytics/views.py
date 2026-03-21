# src/analytics/views.py
# ─────────────────────────────────────────────────────────────────────────────
# CoopData – Analytics & Dashboard views (Eswatini / SUCOSA II)
# TOR §3.4 – real-time visual dashboards, exportable reports, trend analysis
# ─────────────────────────────────────────────────────────────────────────────
import json
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView, TemplateView, View

from cooperatives.models import (
    Cooperative,
    LoanAccount,
    Member,
    SACCOFinancialSummary,
    TrainingRecord,
)
from users.models import AuditLog

from .models import (
    BenchmarkThreshold,
    DataQualityAlert,
    ExportJob,
    KPI,
    ReportConfiguration,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _scope_cooperatives(user):
    """Return a Cooperative queryset scoped to the requesting user's role."""
    qs = Cooperative.objects.all()
    if user.role == "sacco_manager":
        return qs.filter(contact_person=user)
    if user.role == "regional_officer" and user.region:
        return qs.filter(region=user.region)
    return qs


def _latest_summaries(cooperatives_qs):
    """Return the most recent verified SACCOFinancialSummary for each cooperative."""
    coop_ids = cooperatives_qs.values_list("id", flat=True)
    seen: set = set()
    result = []
    for s in SACCOFinancialSummary.objects.filter(
        cooperative_id__in=coop_ids, is_verified=True
    ).order_by("cooperative_id", "-period_end"):
        if s.cooperative_id not in seen:
            seen.add(s.cooperative_id)
            result.append(s)
    return result


# ═════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Role-aware landing dashboard.
    Government/Apex: system-wide aggregates.
    Regional Officer: region-level aggregates.
    SACCO Manager: single cooperative KPIs.
    TOR §3.4 – real-time visual dashboards and KPIs.
    """
    template_name = "analytics/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        coops = _scope_cooperatives(user)
        summaries = _latest_summaries(coops)

        # ── Headline stats ────────────────────────────────────────────────────
        ctx["total_cooperatives"] = coops.filter(status="active").count()
        ctx["total_members"] = Member.objects.filter(
            cooperative__in=coops, is_active=True
        ).count()
        ctx["female_members"] = Member.objects.filter(
            cooperative__in=coops, is_active=True, gender="female"
        ).count()
        ctx["youth_members"] = Member.objects.filter(
            cooperative__in=coops, is_active=True, is_youth=True
        ).count()
        ctx["marginalized_members"] = Member.objects.filter(
            cooperative__in=coops, is_active=True, is_marginalized=True
        ).count()

        # ── Aggregated financial KPIs (average across latest summaries) ───────
        if summaries:
            def _avg(field):
                vals = [
                    getattr(s, field)
                    for s in summaries
                    if getattr(s, field) is not None
                ]
                return round(sum(vals) / len(vals), 4) if vals else None

            ctx["avg_delinquency_rate"] = _avg("kpi_delinquency_rate") * 100 if _avg("kpi_delinquency_rate") is not None else None
            ctx["avg_liquidity_ratio"] = _avg("kpi_liquidity_ratio") * 100 if _avg("kpi_liquidity_ratio") is not None else None
            ctx["avg_capital_adequacy"] = _avg("kpi_capital_adequacy") * 100 if _avg("kpi_capital_adequacy") is not None else None
            ctx["avg_oss"] = _avg("kpi_operational_self_sufficiency") * 100 if _avg("kpi_operational_self_sufficiency") is not None else None

            total_glp = sum(
                s.gross_loan_portfolio for s in summaries if s.gross_loan_portfolio
            )
            total_par30 = sum(s.par_30_days for s in summaries if s.par_30_days)
            ctx["total_gross_loan_portfolio"] = total_glp
            ctx["total_par30"] = total_par30

        # ── Trend data for Chart.js (last 6 periods) ──────────────────────────
        ctx["trend_data"] = _build_trend_data(coops)

        # ── Unresolved data quality alerts ────────────────────────────────────
        ctx["open_alert_count"] = DataQualityAlert.objects.filter(
            is_resolved=False,
            cooperative_id__in=coops.values_list("id", flat=True),
        ).count()

        # ── Pending sync conflicts ────────────────────────────────────────────
        from sync.models import SyncConflict
        ctx["pending_conflicts"] = SyncConflict.objects.filter(
            resolved_at__isnull=True
        ).count()

        # ── Recent audit events (admins/government only) ──────────────────────
        if user.role in ("system_admin", "government", "apex_body"):
            ctx["recent_audits"] = AuditLog.objects.order_by("-timestamp")[:10]

        # ── Cooperative breakdown by type ─────────────────────────────────────
        ctx["type_breakdown"] = list(
            coops.values("type").annotate(count=Count("id")).order_by("-count")
        )
        # ── Region breakdown ──────────────────────────────────────────────────
        ctx["region_breakdown"] = list(
            coops.values("region__name").annotate(count=Count("id")).order_by("-count")
        )

        return ctx


def _build_trend_data(cooperatives_qs):
    """Return JSON-serialisable dict for Chart.js trend line (6 periods)."""
    coop_ids = list(cooperatives_qs.values_list("id", flat=True))
    recent = (
        SACCOFinancialSummary.objects
        .filter(cooperative_id__in=coop_ids, is_verified=True, period_type="quarterly")
        .order_by("period_end")
        .values(
            "period_end",
            "kpi_delinquency_rate",
            "kpi_liquidity_ratio",
            "kpi_capital_adequacy",
        )
    )
    # Aggregate per period_end
    buckets: dict = {}
    for r in recent:
        key = str(r["period_end"])
        if key not in buckets:
            buckets[key] = {"par": [], "liq": [], "cap": []}
        if r["kpi_delinquency_rate"]:
            buckets[key]["par"].append(float(r["kpi_delinquency_rate"]))
        if r["kpi_liquidity_ratio"]:
            buckets[key]["liq"].append(float(r["kpi_liquidity_ratio"]))
        if r["kpi_capital_adequacy"]:
            buckets[key]["cap"].append(float(r["kpi_capital_adequacy"]))

    labels = sorted(buckets.keys())[-6:]
    avg = lambda lst: round(sum(lst) / len(lst) * 100, 2) if lst else None

    return {
        "labels": labels,
        "delinquency": [avg(buckets[l]["par"]) for l in labels],
        "liquidity": [avg(buckets[l]["liq"]) for l in labels],
        "capital": [avg(buckets[l]["cap"]) for l in labels],
    }


# ═════════════════════════════════════════════════════════════════════════════
# KPI DEEP-DIVE
# ═════════════════════════════════════════════════════════════════════════════

class KPIListView(LoginRequiredMixin, TemplateView):
    """All KPIs with latest values for scoped cooperatives."""
    template_name = "analytics/kpi_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = KPI.objects.filter(is_active=True).order_by("display_order")
        return ctx


class CooperativeKPIDashboardView(LoginRequiredMixin, DetailView):
    """
    Full KPI scorecard for a single cooperative.
    Shows latest KPIs, 6-period trend chart, benchmark traffic lights.
    TOR §3.4 – KPIs by cooperative.
    """
    model = Cooperative
    template_name = "analytics/cooperative_kpi_dashboard.html"
    context_object_name = "cooperative"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        coop = self.object
        summaries = (
            SACCOFinancialSummary.objects
            .filter(cooperative=coop, is_verified=True)
            .order_by("-period_end")[:8]
        )
        ctx["summaries"] = summaries
        ctx["latest"] = summaries[0] if summaries else None
        ctx["kpis"] = KPI.objects.filter(is_active=True).order_by("display_order")
        ctx["benchmarks"] = {
            bt.kpi_id: bt
            for bt in BenchmarkThreshold.objects.filter(is_default=True)
        }
        # Trend JSON for Chart.js
        labels = [str(s.period_end) for s in reversed(list(summaries))]
        ctx["trend_json"] = json.dumps({
            "labels": labels,
            "par30": [
                float(s.kpi_delinquency_rate * 100) if s.kpi_delinquency_rate else None
                for s in reversed(list(summaries))
            ],
            "liquidity": [
                float(s.kpi_liquidity_ratio * 100) if s.kpi_liquidity_ratio else None
                for s in reversed(list(summaries))
            ],
            "capital": [
                float(s.kpi_capital_adequacy * 100) if s.kpi_capital_adequacy else None
                for s in reversed(list(summaries))
            ],
        })
        # Comparison: how does this coop rank vs peers in same region?
        peer_summaries = _latest_summaries(
            Cooperative.objects.filter(region=coop.region, status="active").exclude(pk=coop.pk)
        )
        if peer_summaries and ctx["latest"]:
            def rank(field):
                val = getattr(ctx["latest"], field)
                if val is None:
                    return None
                peers = [getattr(s, field) for s in peer_summaries if getattr(s, field)]
                above = sum(1 for p in peers if p < val)  # lower = better for PAR
                return above + 1
            ctx["par_rank"] = rank("kpi_delinquency_rate")
            ctx["peer_count"] = len(peer_summaries)

        return ctx


# ═════════════════════════════════════════════════════════════════════════════
# DATA QUALITY ALERTS
# ═════════════════════════════════════════════════════════════════════════════

class DataQualityAlertListView(LoginRequiredMixin, ListView):
    model = DataQualityAlert
    template_name = "analytics/alert_list.html"
    context_object_name = "alerts"
    paginate_by = 30

    def get_queryset(self):
        qs = DataQualityAlert.objects.select_related("rule", "resolved_by")
        user = self.request.user
        coops = _scope_cooperatives(user)
        qs = qs.filter(cooperative_id__in=coops.values_list("id", flat=True))
        resolved = self.request.GET.get("resolved")
        if resolved == "0":
            qs = qs.filter(is_resolved=False)
        elif resolved == "1":
            qs = qs.filter(is_resolved=True)
        severity = self.request.GET.get("severity")
        if severity:
            qs = qs.filter(rule__severity=severity)
        return qs.order_by("-alert_date")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["open_count"] = self.get_queryset().filter(is_resolved=False).count()
        return ctx


class DataQualityAlertResolveView(LoginRequiredMixin, View):
    """POST: mark an alert as resolved."""

    def post(self, request, pk):
        alert = get_object_or_404(DataQualityAlert, pk=pk)
        alert.is_resolved = True
        alert.resolved_by = request.user
        alert.resolved_date = timezone.now()
        alert.resolution_notes = request.POST.get("notes", "")
        alert.save(update_fields=["is_resolved", "resolved_by", "resolved_date", "resolution_notes"])
        messages.success(request, _("Alert resolved."))
        return redirect("analytics:alert_list")


# ═════════════════════════════════════════════════════════════════════════════
# REPORT CONFIGURATION & EXPORT
# ═════════════════════════════════════════════════════════════════════════════

class ReportListView(LoginRequiredMixin, ListView):
    model = ReportConfiguration
    template_name = "analytics/report_list.html"
    context_object_name = "reports"

    def get_queryset(self):
        user = self.request.user
        qs = ReportConfiguration.objects.all()
        # Filter by allowed roles
        if not user.is_superuser:
            qs = qs.filter(
                Q(allowed_roles__contains=user.role)
                | Q(allowed_roles=[])
            )
        return qs.order_by("name")


class ReportRunView(LoginRequiredMixin, View):
    """
    POST: queue a report generation job (Celery).
    GET: show report parameters form.
    TOR §3.4 – exportable reports PDF / Excel / Word.
    """

    def get(self, request, pk):
        report = get_object_or_404(ReportConfiguration, pk=pk)
        from django.shortcuts import render
        return render(request, "analytics/report_run.html", {"report": report})

    def post(self, request, pk):
        report = get_object_or_404(ReportConfiguration, pk=pk)
        fmt = request.POST.get("format", report.default_format)
        job = ExportJob.objects.create(
            report_config=report,
            requested_by=request.user,
            format=fmt,
            parameters_snapshot=report.parameters,
        )
        from integrations.tasks import generate_export
        generate_export.delay(job.pk)
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.ACTION_EXPORT,
            description=f"Requested export: {report.name} [{fmt}]",
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        messages.info(
            request,
            _(f"Report queued. You'll be notified when it's ready."),
        )
        return redirect("analytics:export_job_list")


class ExportJobListView(LoginRequiredMixin, ListView):
    model = ExportJob
    template_name = "analytics/export_job_list.html"
    context_object_name = "jobs"
    paginate_by = 20

    def get_queryset(self):
        return ExportJob.objects.filter(
            requested_by=self.request.user
        ).order_by("-requested_at")


# ═════════════════════════════════════════════════════════════════════════════
# CHART DATA ENDPOINTS (AJAX / REST)
# ═════════════════════════════════════════════════════════════════════════════

class SystemKPIChartDataView(LoginRequiredMixin, View):
    """
    JSON endpoint consumed by Chart.js on the dashboard.
    Returns aggregated KPI trend data for the scoped cooperatives.
    """

    def get(self, request):
        coops = _scope_cooperatives(request.user)
        data = _build_trend_data(coops)
        return JsonResponse(data)


class MemberDemographicsChartView(LoginRequiredMixin, View):
    """JSON: member breakdown by gender and age_group for Chart.js pie/bar."""

    def get(self, request):
        coops = _scope_cooperatives(request.user)
        members = Member.objects.filter(cooperative__in=coops, is_active=True)
        gender_data = list(
            members.values("gender").annotate(count=Count("id"))
        )
        age_data = list(
            members.values("age_group").annotate(count=Count("id"))
        )
        return JsonResponse({"gender": gender_data, "age_group": age_data})


class LoanPortfolioChartView(LoginRequiredMixin, View):
    """JSON: PAR30 / PAR90 / standard breakdown for doughnut chart."""

    def get(self, request):
        coops = _scope_cooperatives(request.user)
        loans = LoanAccount.objects.filter(
            member__cooperative__in=coops, status=LoanAccount.STATUS_ACTIVE
        )
        total = loans.aggregate(t=Sum("outstanding_balance"))["t"] or 0
        par30 = loans.filter(days_in_arrears__gte=30).aggregate(
            t=Sum("outstanding_balance")
        )["t"] or 0
        par90 = loans.filter(days_in_arrears__gte=90).aggregate(
            t=Sum("outstanding_balance")
        )["t"] or 0
        current = total - par30
        return JsonResponse({
            "labels": ["Current", "PAR 30–90 days", "PAR 90+ days"],
            "values": [float(current), float(par30 - par90), float(par90)],
            "total": float(total),
        })