# src/cooperatives/admin.py
# ─────────────────────────────────────────────────────────────────────────────
# CoopData – Django Admin registrations for the cooperatives app
# ─────────────────────────────────────────────────────────────────────────────
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    BoardMember,
    Cooperative,
    LoanAccount,
    Member,
    SACCOFinancialSummary,
    SavingsAccount,
    TrainingRecord,
)


class MemberInline(admin.TabularInline):
    model = Member
    extra = 0
    fields = ("first_name", "last_name", "member_id", "gender", "age_group", "is_youth", "is_marginalized", "is_active")
    show_change_link = True


class BoardMemberInline(admin.TabularInline):
    model = BoardMember
    extra = 0
    fields = ("position", "member", "gender", "is_youth", "term_start", "is_active")


class TrainingInline(admin.TabularInline):
    model = TrainingRecord
    extra = 0
    fields = ("title", "training_date", "duration_hours", "total_participants", "female_participants", "youth_participants")


@admin.register(Cooperative)
class CooperativeAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "status", "region", "member_count_display", "mambu_encoded_key")
    list_filter = ("type", "status", "region")
    search_fields = ("name", "registration_number", "mambu_encoded_key")
    inlines = [BoardMemberInline, TrainingInline]
    fieldsets = (
        (None, {"fields": ("name", "registration_number", "type", "status", "sector")}),
        (_("Location & Contact"), {"fields": ("region", "physical_address", "postal_address", "phone", "email", "website", "contact_person")}),
        (_("Registration"), {"fields": ("establishment_date", "registration_date", "apex_body")}),
        (_("Mambu Integration"), {"fields": ("mambu_encoded_key", "mambu_last_synced")}),
    )
    readonly_fields = ("mambu_last_synced",)

    @admin.display(description=_("Members"))
    def member_count_display(self, obj):
        return obj.members.filter(is_active=True).count()


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("__str__", "cooperative", "gender", "age_group", "is_youth", "is_marginalized", "is_active")
    list_filter = ("gender", "age_group", "is_youth", "is_marginalized", "is_active", "cooperative__region")
    search_fields = ("first_name", "last_name", "member_id", "national_id")
    list_select_related = ("cooperative", "cooperative__region")


@admin.register(SACCOFinancialSummary)
class SACCOFinancialSummaryAdmin(admin.ModelAdmin):
    list_display = (
        "cooperative", "period_type", "period_start", "period_end",
        "total_members", "kpi_delinquency_rate", "kpi_capital_adequacy",
        "is_verified",
    )
    list_filter = ("period_type", "is_verified", "cooperative__region")
    search_fields = ("cooperative__name",)
    readonly_fields = (
        "submitted_by", "submitted_at",
        "kpi_delinquency_rate", "kpi_liquidity_ratio", "kpi_capital_adequacy",
        "kpi_roa", "kpi_cost_per_borrower", "kpi_portfolio_yield",
        "kpi_operational_self_sufficiency", "kpi_youth_participation_rate",
        "kpi_female_participation_rate", "kpi_training_hours_per_member",
    )
    actions = ["recompute_kpis", "verify_summaries"]

    @admin.action(description=_("Recompute KPIs for selected summaries"))
    def recompute_kpis(self, request, queryset):
        from integrations.tasks import compute_financial_kpis
        count = 0
        for s in queryset:
            compute_financial_kpis.delay(s.pk)
            count += 1
        self.message_user(request, _(f"Queued KPI computation for {count} summaries."))

    @admin.action(description=_("Mark selected summaries as verified"))
    def verify_summaries(self, request, queryset):
        updated = queryset.update(is_verified=True, verified_by=request.user)
        self.message_user(request, _(f"{updated} summaries marked as verified."))


@admin.register(LoanAccount)
class LoanAccountAdmin(admin.ModelAdmin):
    list_display = ("loan_id", "member", "principal_amount", "outstanding_balance", "days_in_arrears", "status")
    list_filter = ("status", "member__cooperative__region")
    search_fields = ("loan_id", "member__first_name", "member__last_name", "mambu_encoded_key")


@admin.register(SavingsAccount)
class SavingsAccountAdmin(admin.ModelAdmin):
    list_display = ("account_number", "member", "account_type", "balance", "is_active")
    list_filter = ("account_type", "is_active")
    search_fields = ("account_number", "member__first_name", "member__last_name")


@admin.register(BoardMember)
class BoardMemberAdmin(admin.ModelAdmin):
    list_display = ("cooperative", "position", "member", "gender", "is_youth", "is_active")
    list_filter = ("position", "gender", "is_youth", "is_active")


@admin.register(TrainingRecord)
class TrainingRecordAdmin(admin.ModelAdmin):
    list_display = ("title", "cooperative", "training_date", "duration_hours", "total_participants", "female_participants", "youth_participants")
    list_filter = ("cooperative__region",)
    date_hierarchy = "training_date"