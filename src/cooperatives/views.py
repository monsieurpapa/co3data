# src/cooperatives/views.py
# ─────────────────────────────────────────────────────────────────────────────
# CoopData – Cooperative module views (Eswatini / SUCOSA II)
# ─────────────────────────────────────────────────────────────────────────────
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView,
)

from users.models import AuditLog

from .forms import (
    BoardMemberForm,
    CooperativeForm,
    LoanAccountForm,
    MemberForm,
    SACCOFinancialSummaryForm,
    SavingsAccountForm,
    TrainingRecordForm,
)
from .models import (
    BoardMember,
    Cooperative,
    LoanAccount,
    Member,
    SACCOFinancialSummary,
    SavingsAccount,
    TrainingRecord,
)


# ── Role permission mixin ─────────────────────────────────────────────────────

class RoleRequiredMixin(LoginRequiredMixin):
    """
    Restrict view access to users with specific roles.
    Set `allowed_roles` on the view class.
    """
    allowed_roles: list = []

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and self.allowed_roles:
            if request.user.role not in self.allowed_roles and not request.user.is_superuser:
                messages.error(request, _("You do not have permission to perform this action."))
                return redirect("cooperatives:cooperative_list")
        return super().dispatch(request, *args, **kwargs)


def _log(request, action, obj=None, before=None, after=None, description=""):
    AuditLog.objects.create(
        user=request.user,
        action=action,
        description=description or str(obj),
        content_type_label=type(obj).__name__ if obj else "",
        object_id=str(obj.pk) if obj else "",
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        before_state=before,
        after_state=after,
    )


WRITE_ROLES = [
    "system_admin", "regional_officer", "sacco_manager", "field_agent",
]
GOVERNMENT_ROLES = ["system_admin", "government", "apex_body", "regional_officer"]


# ═════════════════════════════════════════════════════════════════════════════
# COOPERATIVE
# ═════════════════════════════════════════════════════════════════════════════

class CooperativeListView(LoginRequiredMixin, ListView):
    model = Cooperative
    template_name = "cooperatives/cooperative_list.html"
    context_object_name = "cooperatives"
    paginate_by = 20

    def get_queryset(self):
        qs = Cooperative.objects.select_related("region", "contact_person").annotate(
            member_count=Count("members", filter=Q(members__is_active=True))
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(registration_number__icontains=q))
        region = self.request.GET.get("region")
        if region:
            qs = qs.filter(region_id=region)
        coop_type = self.request.GET.get("type")
        if coop_type:
            qs = qs.filter(type=coop_type)
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        # Regional officers see only their region
        user = self.request.user
        if user.role == "regional_officer" and user.region:
            qs = qs.filter(region=user.region)
        # SACCO managers see only their cooperative
        if user.role == "sacco_manager":
            qs = qs.filter(contact_person=user)
        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["type_choices"] = Cooperative.COOPERATIVE_TYPES
        ctx["status_choices"] = Cooperative.STATUS_CHOICES
        from users.models import Region
        ctx["regions"] = Region.objects.filter(country_code="SZ").order_by("name")
        return ctx


class CooperativeDetailView(LoginRequiredMixin, DetailView):
    model = Cooperative
    template_name = "cooperatives/cooperative_detail.html"
    context_object_name = "cooperative"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        coop = self.object
        ctx["members"] = coop.members.filter(is_active=True).order_by("last_name")[:10]
        ctx["member_count"] = coop.members.filter(is_active=True).count()
        ctx["latest_summary"] = (
            coop.financial_summaries.filter(is_verified=True).order_by("-period_end").first()
        )
        ctx["board"] = coop.board_members.filter(is_active=True).select_related("member")
        ctx["trainings"] = coop.training_records.order_by("-training_date")[:5]
        ctx["open_alerts"] = coop.financial_summaries.filter(
            # proxy via analytics — count unresolved alerts for this coop
        )
        return ctx


class CooperativeCreateView(RoleRequiredMixin, CreateView):
    model = Cooperative
    form_class = CooperativeForm
    template_name = "cooperatives/cooperative_form.html"
    allowed_roles = WRITE_ROLES

    def form_valid(self, form):
        response = super().form_valid(form)
        _log(self.request, AuditLog.ACTION_CREATE, self.object,
             description=f"Created cooperative: {self.object.name}")
        messages.success(self.request, _("Cooperative created successfully."))
        return response

    def get_success_url(self):
        return reverse_lazy("cooperatives:cooperative_detail", kwargs={"pk": self.object.pk})


class CooperativeUpdateView(RoleRequiredMixin, UpdateView):
    model = Cooperative
    form_class = CooperativeForm
    template_name = "cooperatives/cooperative_form.html"
    allowed_roles = WRITE_ROLES

    def form_valid(self, form):
        before = {f: str(getattr(self.object, f)) for f in form.changed_data}
        response = super().form_valid(form)
        after = {f: str(getattr(self.object, f)) for f in form.changed_data}
        _log(self.request, AuditLog.ACTION_UPDATE, self.object,
             before=before, after=after,
             description=f"Updated cooperative: {self.object.name}")
        messages.success(self.request, _("Cooperative updated successfully."))
        return response

    def get_success_url(self):
        return reverse_lazy("cooperatives:cooperative_detail", kwargs={"pk": self.object.pk})


class CooperativeDeleteView(RoleRequiredMixin, DeleteView):
    model = Cooperative
    template_name = "cooperatives/cooperative_confirm_delete.html"
    success_url = reverse_lazy("cooperatives:cooperative_list")
    allowed_roles = ["system_admin"]

    def form_valid(self, form):
        _log(self.request, AuditLog.ACTION_DELETE, self.object,
             description=f"Deleted cooperative: {self.object.name}")
        messages.success(self.request, _("Cooperative deleted."))
        return super().form_valid(form)


# ═════════════════════════════════════════════════════════════════════════════
# MEMBER
# ═════════════════════════════════════════════════════════════════════════════

class MemberListView(LoginRequiredMixin, ListView):
    model = Member
    template_name = "cooperatives/member_list.html"
    context_object_name = "members"
    paginate_by = 25

    def get_queryset(self):
        qs = Member.objects.select_related("cooperative", "cooperative__region")
        user = self.request.user
        # Scope by user role
        if user.role == "sacco_manager":
            qs = qs.filter(cooperative__contact_person=user)
        elif user.role == "regional_officer" and user.region:
            qs = qs.filter(cooperative__region=user.region)
        # Filter by cooperative
        coop_id = self.kwargs.get("cooperative_pk") or self.request.GET.get("cooperative")
        if coop_id:
            qs = qs.filter(cooperative_id=coop_id)
        # Search
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q)
                | Q(member_id__icontains=q) | Q(national_id__icontains=q)
            )
        gender = self.request.GET.get("gender")
        if gender:
            qs = qs.filter(gender=gender)
        age_group = self.request.GET.get("age_group")
        if age_group:
            qs = qs.filter(age_group=age_group)
        is_youth = self.request.GET.get("is_youth")
        if is_youth == "1":
            qs = qs.filter(is_youth=True)
        is_marginalized = self.request.GET.get("is_marginalized")
        if is_marginalized == "1":
            qs = qs.filter(is_marginalized=True)
        return qs.filter(is_active=True).order_by("last_name", "first_name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["gender_choices"] = Member._meta.get_field("gender").choices
        ctx["age_group_choices"] = Member._meta.get_field("age_group").choices
        coop_id = self.kwargs.get("cooperative_pk") or self.request.GET.get("cooperative")
        if coop_id:
            ctx["cooperative"] = get_object_or_404(Cooperative, pk=coop_id)
        return ctx


class MemberDetailView(LoginRequiredMixin, DetailView):
    model = Member
    template_name = "cooperatives/member_detail.html"
    context_object_name = "member"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        member = self.object
        ctx["loans"] = member.loan_accounts.order_by("-disbursement_date")
        ctx["savings"] = member.savings_accounts.filter(is_active=True)
        ctx["active_loans"] = member.loan_accounts.filter(
            status=LoanAccount.STATUS_ACTIVE
        ).aggregate(total=Sum("outstanding_balance"))["total"] or 0
        return ctx


class MemberCreateView(RoleRequiredMixin, CreateView):
    model = Member
    form_class = MemberForm
    template_name = "cooperatives/member_form.html"
    allowed_roles = WRITE_ROLES

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        coop_pk = self.kwargs.get("cooperative_pk")
        if coop_pk:
            kwargs["cooperative"] = get_object_or_404(Cooperative, pk=coop_pk)
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        _log(self.request, AuditLog.ACTION_CREATE, self.object,
             description=f"Created member: {self.object}")
        messages.success(self.request, _("Member registered successfully."))
        return response

    def get_success_url(self):
        return reverse_lazy("cooperatives:member_detail", kwargs={"pk": self.object.pk})


class MemberUpdateView(RoleRequiredMixin, UpdateView):
    model = Member
    form_class = MemberForm
    template_name = "cooperatives/member_form.html"
    allowed_roles = WRITE_ROLES

    def form_valid(self, form):
        before = {f: str(getattr(self.object, f)) for f in form.changed_data}
        response = super().form_valid(form)
        after = {f: str(getattr(self.object, f)) for f in form.changed_data}
        _log(self.request, AuditLog.ACTION_UPDATE, self.object,
             before=before, after=after)
        messages.success(self.request, _("Member updated successfully."))
        return response

    def get_success_url(self):
        return reverse_lazy("cooperatives:member_detail", kwargs={"pk": self.object.pk})


# ═════════════════════════════════════════════════════════════════════════════
# FINANCIAL SUMMARY
# ═════════════════════════════════════════════════════════════════════════════

class FinancialSummaryListView(LoginRequiredMixin, ListView):
    model = SACCOFinancialSummary
    template_name = "cooperatives/financial_summary_list.html"
    context_object_name = "summaries"
    paginate_by = 20

    def get_queryset(self):
        qs = SACCOFinancialSummary.objects.select_related(
            "cooperative", "submitted_by"
        )
        user = self.request.user
        if user.role == "sacco_manager":
            qs = qs.filter(cooperative__contact_person=user)
        elif user.role == "regional_officer" and user.region:
            qs = qs.filter(cooperative__region=user.region)
        coop_id = self.kwargs.get("cooperative_pk") or self.request.GET.get("cooperative")
        if coop_id:
            qs = qs.filter(cooperative_id=coop_id)
        period_type = self.request.GET.get("period_type")
        if period_type:
            qs = qs.filter(period_type=period_type)
        return qs.order_by("-period_end")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["period_choices"] = SACCOFinancialSummary.PERIOD_CHOICES
        coop_id = self.kwargs.get("cooperative_pk")
        if coop_id:
            ctx["cooperative"] = get_object_or_404(Cooperative, pk=coop_id)
        return ctx


class FinancialSummaryDetailView(LoginRequiredMixin, DetailView):
    model = SACCOFinancialSummary
    template_name = "cooperatives/financial_summary_detail.html"
    context_object_name = "summary"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        s = self.object
        # Build KPI card data for template
        ctx["kpi_cards"] = [
            {
                "label": _("Delinquency Rate (PAR30)"),
                "value": s.kpi_delinquency_rate,
                "format": "percent",
                "higher_is_better": False,
            },
            {
                "label": _("Liquidity Ratio"),
                "value": s.kpi_liquidity_ratio,
                "format": "percent",
                "higher_is_better": True,
            },
            {
                "label": _("Capital Adequacy"),
                "value": s.kpi_capital_adequacy,
                "format": "percent",
                "higher_is_better": True,
            },
            {
                "label": _("Return on Assets (ROA)"),
                "value": s.kpi_roa,
                "format": "percent",
                "higher_is_better": True,
            },
            {
                "label": _("Operational Self-Sufficiency"),
                "value": s.kpi_operational_self_sufficiency,
                "format": "percent",
                "higher_is_better": True,
            },
            {
                "label": _("Youth Participation"),
                "value": s.kpi_youth_participation_rate,
                "format": "percent",
                "higher_is_better": True,
            },
            {
                "label": _("Female Participation"),
                "value": s.kpi_female_participation_rate,
                "format": "percent",
                "higher_is_better": True,
            },
            {
                "label": _("Cost per Borrower (SZL)"),
                "value": s.kpi_cost_per_borrower,
                "format": "currency",
                "higher_is_better": False,
            },
        ]
        return ctx


class FinancialSummaryCreateView(RoleRequiredMixin, CreateView):
    model = SACCOFinancialSummary
    form_class = SACCOFinancialSummaryForm
    template_name = "cooperatives/financial_summary_form.html"
    allowed_roles = WRITE_ROLES

    def get_initial(self):
        initial = super().get_initial()
        coop_pk = self.kwargs.get("cooperative_pk")
        if coop_pk:
            initial["cooperative"] = coop_pk
        return initial

    def form_valid(self, form):
        form.instance.submitted_by = self.request.user
        response = super().form_valid(form)
        # Trigger KPI computation via Celery
        from integrations.tasks import compute_financial_kpis
        compute_financial_kpis.delay(self.object.pk)
        _log(self.request, AuditLog.ACTION_CREATE, self.object,
             description=f"Submitted financial summary: {self.object}")
        messages.success(
            self.request,
            _("Financial data submitted. KPIs will be computed shortly."),
        )
        return response

    def get_success_url(self):
        return reverse_lazy(
            "cooperatives:financial_summary_detail", kwargs={"pk": self.object.pk}
        )


class FinancialSummaryVerifyView(RoleRequiredMixin, UpdateView):
    """
    Allows government/apex roles to verify a submitted financial summary.
    Sets is_verified=True and records the verifier.
    """
    model = SACCOFinancialSummary
    fields: list = []  # no editable fields – just verification action
    template_name = "cooperatives/financial_summary_verify.html"
    allowed_roles = GOVERNMENT_ROLES

    def form_valid(self, form):
        self.object.is_verified = True
        self.object.verified_by = self.request.user
        self.object.save(update_fields=["is_verified", "verified_by"])
        _log(self.request, AuditLog.ACTION_UPDATE, self.object,
             description=f"Verified financial summary #{self.object.pk}")
        messages.success(self.request, _("Financial summary verified."))
        return redirect(
            "cooperatives:financial_summary_detail", pk=self.object.pk
        )


# ═════════════════════════════════════════════════════════════════════════════
# BOARD MEMBER
# ═════════════════════════════════════════════════════════════════════════════

class BoardMemberCreateView(RoleRequiredMixin, CreateView):
    model = BoardMember
    form_class = BoardMemberForm
    template_name = "cooperatives/board_member_form.html"
    allowed_roles = WRITE_ROLES

    def get_initial(self):
        initial = super().get_initial()
        coop_pk = self.kwargs.get("cooperative_pk")
        if coop_pk:
            initial["cooperative"] = coop_pk
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        _log(self.request, AuditLog.ACTION_CREATE, self.object,
             description=f"Added board member: {self.object}")
        messages.success(self.request, _("Board member added."))
        return response

    def get_success_url(self):
        return reverse_lazy(
            "cooperatives:cooperative_detail",
            kwargs={"pk": self.object.cooperative_id},
        )


# ═════════════════════════════════════════════════════════════════════════════
# TRAINING RECORD
# ═════════════════════════════════════════════════════════════════════════════

class TrainingRecordListView(LoginRequiredMixin, ListView):
    model = TrainingRecord
    template_name = "cooperatives/training_list.html"
    context_object_name = "trainings"
    paginate_by = 20

    def get_queryset(self):
        qs = TrainingRecord.objects.select_related("cooperative")
        coop_pk = self.kwargs.get("cooperative_pk") or self.request.GET.get("cooperative")
        if coop_pk:
            qs = qs.filter(cooperative_id=coop_pk)
        user = self.request.user
        if user.role == "sacco_manager":
            qs = qs.filter(cooperative__contact_person=user)
        elif user.role == "regional_officer" and user.region:
            qs = qs.filter(cooperative__region=user.region)
        return qs.order_by("-training_date")


class TrainingRecordCreateView(RoleRequiredMixin, CreateView):
    model = TrainingRecord
    form_class = TrainingRecordForm
    template_name = "cooperatives/training_form.html"
    allowed_roles = WRITE_ROLES

    def get_initial(self):
        initial = super().get_initial()
        coop_pk = self.kwargs.get("cooperative_pk")
        if coop_pk:
            initial["cooperative"] = coop_pk
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Training record added."))
        return response

    def get_success_url(self):
        return reverse_lazy(
            "cooperatives:cooperative_detail",
            kwargs={"pk": self.object.cooperative_id},
        )


# ═════════════════════════════════════════════════════════════════════════════
# LOAN ACCOUNT
# ═════════════════════════════════════════════════════════════════════════════

class LoanAccountListView(LoginRequiredMixin, ListView):
    model = LoanAccount
    template_name = "cooperatives/loan_list.html"
    context_object_name = "loans"
    paginate_by = 25

    def get_queryset(self):
        qs = LoanAccount.objects.select_related("member", "member__cooperative")
        user = self.request.user
        if user.role == "sacco_manager":
            qs = qs.filter(member__cooperative__contact_person=user)
        elif user.role == "regional_officer" and user.region:
            qs = qs.filter(member__cooperative__region=user.region)
        coop_id = self.request.GET.get("cooperative")
        if coop_id:
            qs = qs.filter(member__cooperative_id=coop_id)
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        delinquent = self.request.GET.get("delinquent")
        if delinquent == "1":
            qs = qs.filter(days_in_arrears__gt=0)
        return qs.order_by("-disbursement_date")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = LoanAccount.STATUS_CHOICES
        return ctx


class LoanAccountCreateView(RoleRequiredMixin, CreateView):
    model = LoanAccount
    form_class = LoanAccountForm
    template_name = "cooperatives/loan_form.html"
    allowed_roles = WRITE_ROLES

    def form_valid(self, form):
        response = super().form_valid(form)
        _log(self.request, AuditLog.ACTION_CREATE, self.object,
             description=f"Created loan: {self.object.loan_id}")
        messages.success(self.request, _("Loan account created."))
        return response

    def get_success_url(self):
        return reverse_lazy(
            "cooperatives:member_detail", kwargs={"pk": self.object.member_id}
        )


# ═════════════════════════════════════════════════════════════════════════════
# SAVINGS ACCOUNT
# ═════════════════════════════════════════════════════════════════════════════

class SavingsAccountCreateView(RoleRequiredMixin, CreateView):
    model = SavingsAccount
    form_class = SavingsAccountForm
    template_name = "cooperatives/savings_form.html"
    allowed_roles = WRITE_ROLES

    def form_valid(self, form):
        response = super().form_valid(form)
        _log(self.request, AuditLog.ACTION_CREATE, self.object,
             description=f"Created savings account: {self.object.account_number}")
        messages.success(self.request, _("Savings account created."))
        return response

    def get_success_url(self):
        return reverse_lazy(
            "cooperatives:member_detail", kwargs={"pk": self.object.member_id}
        )