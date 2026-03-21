# src/analytics/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    BenchmarkThreshold, DataQualityAlert, DataValidationRule,
    ExportJob, KPI, ReportConfiguration,
)


class BenchmarkInline(admin.TabularInline):
    model = BenchmarkThreshold
    extra = 1


@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "category", "unit", "higher_is_better", "is_active", "display_order")
    list_filter = ("category", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [BenchmarkInline]


@admin.register(ReportConfiguration)
class ReportConfigurationAdmin(admin.ModelAdmin):
    list_display = ("name", "scope", "default_format", "is_scheduled", "last_generated_at")
    list_filter = ("scope", "default_format", "is_scheduled")
    search_fields = ("name",)


@admin.register(DataValidationRule)
class DataValidationRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "applies_to_model", "applies_to_field", "severity", "is_active")
    list_filter = ("severity", "is_active")


@admin.register(DataQualityAlert)
class DataQualityAlertAdmin(admin.ModelAdmin):
    list_display = ("rule", "cooperative_id", "record_id", "alert_date", "is_resolved")
    list_filter = ("is_resolved", "rule__severity")
    search_fields = ("message",)
    date_hierarchy = "alert_date"
    actions = ["mark_resolved"]

    @admin.action(description=_("Mark selected alerts as resolved"))
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_resolved=True, resolved_by=request.user, resolved_date=timezone.now())


@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    list_display = ("report_config", "format", "status", "requested_by", "requested_at", "completed_at")
    list_filter = ("status", "format")
    readonly_fields = ("requested_at", "completed_at", "file_url", "error_message")