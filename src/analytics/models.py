from django.db import models
from django.utils.translation import gettext_lazy as _
from cooperatives.models import Cooperative
from users.models import User

class KPI(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    calculation_formula = models.TextField(help_text=_("Python code snippet or description of how the KPI is calculated"))
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Key Performance Indicator")
        verbose_name_plural = _("Key Performance Indicators")

    def __str__(self):
        return self.name

class ReportConfiguration(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parameters = models.JSONField(blank=True, null=True)
    viewable_by_roles = models.ManyToManyField(User, related_name="viewable_reports", blank=True)

    class Meta:
        verbose_name = _("Report Configuration")
        verbose_name_plural = _("Report Configurations")

    def __str__(self):
        return self.name

class DataValidationRule(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    rule_expression = models.TextField(help_text=_("Python code snippet or expression for validation"))
    applies_to_model = models.CharField(max_length=100, help_text=_("e.g., 'cooperatives.ProductionRecord'"))
    applies_to_field = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Data Validation Rule")
        verbose_name_plural = _("Data Validation Rules")

    def __str__(self):
        return self.name

class DataQualityAlert(models.Model):
    rule = models.ForeignKey(DataValidationRule, on_delete=models.CASCADE, related_name="alerts")
    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE, related_name="data_quality_alerts")
    record_id = models.PositiveIntegerField(help_text=_("ID of the record that triggered the alert"))
    message = models.TextField()
    alert_date = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="resolved_alerts")
    resolved_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _("Data Quality Alert")
        verbose_name_plural = _("Data Quality Alerts")
        ordering = ["-alert_date"]

    def __str__(self):
        return f"Alert for {self.cooperative.name} - {self.rule.name}"
