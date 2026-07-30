# src/analytics/views.py
import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, TemplateView, View

from cooperatives.models import Cooperative, Member, ProductionRecord
from questionnaires.models import Submission
from users.models import AuditLog

from .models import DataQualityAlert, ExportJob, KPI, ReportConfiguration
from .services import KPIService


# ═════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════

class DashboardView(LoginRequiredMixin, TemplateView):
    """Role-aware landing dashboard, scoped to the user's accessible cooperatives."""
    template_name = "analytics/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        coops = user.get_accessible_cooperatives()
        coop_ids = coops.values_list("id", flat=True)

        members = Member.objects.filter(cooperative__in=coops, is_active=True)
        production = ProductionRecord.objects.filter(member__cooperative__in=coops)
        alerts = DataQualityAlert.objects.filter(cooperative_id__in=coop_ids)
        submissions = Submission.objects.filter(submitted_by__cooperative__in=coops)

        ctx["total_cooperatives"] = coops.count()
        ctx["total_members"] = members.count()
        ctx["female_members"] = members.filter(gender="female").count()
        ctx["youth_members"] = members.filter(age_group="youth").count()
        ctx["marginalized_members"] = members.filter(is_marginalized=True).count()

        # ── Youth participation per cooperative ────────────────────────────────
        youth_counts = []
        for coop in KPIService.get_cooperatives_with_youth_data(coops):
            pct = (coop.youth_members_count / coop.total_members_count * 100) if coop.total_members_count else 0
            youth_counts.append({"coop_name": coop.name, "youth_participation": round(pct, 2)})
        ctx["youth_counts"] = youth_counts

        # ── Average yield per hectare ────────────────────────────────────────
        total_yield, coops_with_yield = 0, 0
        for coop in KPIService.get_cooperatives_with_yield_data(coops):
            if coop.total_farm_size_ha and coop.total_farm_size_ha > 0:
                coop_yield = float(coop.total_production_kg or 0) / float(coop.total_farm_size_ha)
                if coop_yield > 0:
                    total_yield += coop_yield
                    coops_with_yield += 1
        ctx["avg_yield"] = round(total_yield / coops_with_yield, 2) if coops_with_yield else 0

        # ── Cherry delivery volume this month ───────────────────────────────
        month_start = timezone.now().date().replace(day=1)
        deliveries_this_month = production.filter(
            record_type=ProductionRecord.RECORD_TYPE_CHERRY, purchase_date__gte=month_start
        )
        ctx["cherry_kg_this_month"] = deliveries_this_month.aggregate(t=Sum("quantity_kg"))["t"] or 0
        ctx["cherry_value_fc_this_month"] = deliveries_this_month.aggregate(t=Sum("total_price_fc"))["t"] or 0

        # ── Recent production / deliveries ──────────────────────────────────
        ctx["recent_production"] = production.filter(
            record_type=ProductionRecord.RECORD_TYPE_GENERIC
        ).select_related("farm__member__cooperative").order_by("-harvest_date")[:10]
        ctx["recent_deliveries"] = production.filter(
            record_type=ProductionRecord.RECORD_TYPE_CHERRY
        ).select_related("member", "station").order_by("-id")[:10]

        # ── Data quality alerts ─────────────────────────────────────────────
        ctx["quality_alerts"] = alerts.select_related("rule").filter(is_resolved=False).order_by("-alert_date")[:5]
        ctx["open_alert_count"] = alerts.filter(is_resolved=False).count()

        # ── Recent submissions ───────────────────────────────────────────────
        ctx["recent_submissions"] = submissions.select_related("questionnaire", "submitted_by").order_by("-submitted_at")[:5]
        ctx["total_submissions"] = submissions.count()

        # ── Pending sync conflicts ───────────────────────────────────────────
        from sync.models import SyncConflict
        ctx["pending_conflicts"] = SyncConflict.objects.filter(resolved_at__isnull=True).count()

        # ── Recent audit events (admins/government/apex only) ──────────────
        if user.is_superuser or user.role in (user.ROLE_ADMIN, user.ROLE_GOVERNMENT, user.ROLE_APEX_BODY):
            ctx["recent_audits"] = AuditLog.objects.order_by("-timestamp")[:10]

        # ── Breakdown by type / region ───────────────────────────────────────
        ctx["type_breakdown"] = list(coops.values("type").annotate(count=Count("id")).order_by("-count"))
        ctx["region_breakdown"] = list(coops.values("region__name").annotate(count=Count("id")).order_by("-count"))

        ctx["trend_data"] = _build_trend_data(coops)

        return ctx


def _build_trend_data(cooperatives_qs):
    """Return JSON-serialisable dict for Chart.js: cherry delivery volume, last 6 months."""
    member_ids = Member.objects.filter(cooperative__in=cooperatives_qs).values_list("id", flat=True)
    today = timezone.now().date()
    months = []
    for i in range(5, -1, -1):
        month_date = (today.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        months.append(month_date)

    labels, volumes, values = [], [], []
    for i, month_start in enumerate(months):
        month_end = (months[i + 1] - timedelta(days=1)) if i + 1 < len(months) else today
        qs = ProductionRecord.objects.filter(
            record_type=ProductionRecord.RECORD_TYPE_CHERRY,
            member_id__in=member_ids,
            purchase_date__gte=month_start,
            purchase_date__lte=month_end,
        )
        agg = qs.aggregate(kg=Sum("quantity_kg"), fc=Sum("total_price_fc"))
        labels.append(month_start.strftime("%b %Y"))
        volumes.append(float(agg["kg"] or 0))
        values.append(float(agg["fc"] or 0))

    return {"labels": labels, "volume_kg": volumes, "value_fc": values}


# ═════════════════════════════════════════════════════════════════════════════
# KPI CATALOGUE
# ═════════════════════════════════════════════════════════════════════════════

class KPIListView(LoginRequiredMixin, TemplateView):
    """All active KPIs (catalogue is admin-configurable, not hardcoded)."""
    template_name = "analytics/kpi_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = KPI.objects.filter(is_active=True).order_by("display_order")
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
        coops = self.request.user.get_accessible_cooperatives()
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
        if not user.is_superuser:
            qs = qs.filter(Q(allowed_roles__contains=user.role) | Q(allowed_roles=[]))
        return qs.order_by("name")


class ReportRunView(LoginRequiredMixin, View):
    """GET: show report parameters form. POST: queue a report generation job (Celery)."""

    def get(self, request, pk):
        report = get_object_or_404(ReportConfiguration, pk=pk)
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
        from core.tasks import generate_export
        generate_export.delay(job.pk)
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.ACTION_EXPORT,
            description=f"Requested export: {report.name} [{fmt}]",
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        messages.info(request, _("Report queued. You'll be notified when it's ready."))
        return redirect("analytics:export_job_list")


class ExportJobListView(LoginRequiredMixin, ListView):
    model = ExportJob
    template_name = "analytics/export_job_list.html"
    context_object_name = "jobs"
    paginate_by = 20

    def get_queryset(self):
        return ExportJob.objects.filter(requested_by=self.request.user).order_by("-requested_at")


# ═════════════════════════════════════════════════════════════════════════════
# CHART DATA ENDPOINTS (AJAX)
# ═════════════════════════════════════════════════════════════════════════════

class SystemKPIChartDataView(LoginRequiredMixin, View):
    """JSON endpoint consumed by Chart.js on the dashboard: cherry delivery trend."""

    def get(self, request):
        coops = request.user.get_accessible_cooperatives()
        return JsonResponse(_build_trend_data(coops))


class MemberDemographicsChartView(LoginRequiredMixin, View):
    """JSON: member breakdown by gender and age_group for Chart.js pie/bar."""

    def get(self, request):
        coops = request.user.get_accessible_cooperatives()
        members = Member.objects.filter(cooperative__in=coops, is_active=True)
        gender_data = list(members.values("gender").annotate(count=Count("id")))
        age_data = list(members.values("age_group").annotate(count=Count("id")))
        return JsonResponse({"gender": gender_data, "age_group": age_data})
