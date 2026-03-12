from django.contrib import admin
from .models import KPI, ReportConfiguration, DataValidationRule, DataQualityAlert

@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')

@admin.register(ReportConfiguration)
class ReportConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')

@admin.register(DataValidationRule)
class DataValidationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'applies_to_model', 'is_active')

@admin.register(DataQualityAlert)
class DataQualityAlertAdmin(admin.ModelAdmin):
    list_display = ('rule', 'cooperative', 'alert_date', 'is_resolved')
    list_filter = ('is_resolved',)
