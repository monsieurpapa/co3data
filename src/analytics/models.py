# src/analytics/models.py
# ─────────────────────────────────────────────────────────────────────────────
# CO3DATA – Analytics, KPI, Reporting models
#
# KPI/ReportConfiguration/BenchmarkThreshold/DataValidationRule/ExportJob are
# generic and domain-agnostic (configurable via admin, not hardcoded to a
# specific sector) — the actual KPI catalogue for coffee/cocoa cooperatives
# (yield/hectare, cherry volume, youth/gender participation, board composition)
# is seed data, not model structure.
# ─────────────────────────────────────────────────────────────────────────────

from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User
import uuid


# ─────────────────────────────────────────────────────────────────────────────
# KPI Catalogue
# ─────────────────────────────────────────────────────────────────────────────

class KPI(models.Model):
    """
    Defines a Key Performance Indicator.
    Seed data (management command) populates coffee/cocoa KPIs — yield per
    hectare, cherry volume, sales value, youth/gender participation, board
    composition — configurable rather than hardcoded to a specific sector.
    """

    CATEGORY_FINANCIAL = "financial"
    CATEGORY_OPERATIONAL = "operational"
    CATEGORY_SOCIAL = "social"
    CATEGORY_GOVERNANCE = "governance"

    CATEGORY_CHOICES = (
        (CATEGORY_FINANCIAL, _("Financial")),
        (CATEGORY_OPERATIONAL, _("Operational")),
        (CATEGORY_SOCIAL, _("Social / Inclusion")),
        (CATEGORY_GOVERNANCE, _("Governance")),
    )

    # Slugs for the seeded coffee/cocoa KPI catalogue.
    SLUG_YIELD_PER_HECTARE = "kpi_yield_per_hectare"
    SLUG_CHERRY_VOLUME = "kpi_cherry_volume_kg"
    SLUG_SALES_VALUE = "kpi_sales_value"
    SLUG_YOUTH_PART = "kpi_youth_participation_rate"
    SLUG_FEMALE_PART = "kpi_female_participation_rate"

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, db_index=True
    )
    description = models.TextField(blank=True)
    unit = models.CharField(
        max_length=30,
        blank=True,
        help_text=_("e.g. % (percentage), FC, USD, kg, ratio"),
    )
    # Source field on a model, if computed centrally (e.g. ProductionRecord.quantity_kg)
    source_field = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Model field name where pre-computed value is stored"),
    )
    # Formula description (human-readable, for documentation/training)
    formula_description = models.TextField(
        blank=True,
        help_text=_("Plain-language description of how this KPI is calculated"),
    )
    higher_is_better = models.BooleanField(
        default=True,
        help_text=_("False for KPIs where a lower value is healthier (e.g. delinquency)"),
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=100)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("KPI")
        verbose_name_plural = _("KPIs")
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} [{self.get_category_display()}]"


# ─────────────────────────────────────────────────────────────────────────────
# Benchmark Thresholds  (TOR §3.1 – performance benchmarking)
# ─────────────────────────────────────────────────────────────────────────────

class BenchmarkThreshold(models.Model):
    """
    Configurable traffic-light thresholds for a KPI.
    Green / Amber / Red bands allow dashboards to colour-code KPI cards
    and trigger data quality alerts automatically.
    """

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    kpi = models.ForeignKey(
        KPI, on_delete=models.CASCADE, related_name="thresholds"
    )
    label = models.CharField(
        max_length=50,
        help_text=_("e.g. 'ITC Benchmark', 'National Cooperative Standard'"),
    )
    green_min = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
        help_text=_("Value at or above which performance is GREEN"),
    )
    green_max = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
    )
    amber_min = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    amber_max = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    red_threshold = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
        help_text=_("Value at or below (for higher-is-better) which performance is RED"),
    )
    is_default = models.BooleanField(
        default=False,
        help_text=_("Apply this threshold to all cooperatives by default"),
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = _("Benchmark Threshold")
        verbose_name_plural = _("Benchmark Thresholds")

    def __str__(self):
        return f"{self.kpi.name} – {self.label}"


# ─────────────────────────────────────────────────────────────────────────────
# Report Configuration  (TOR §3.4 – role-based exportable reports)
# ─────────────────────────────────────────────────────────────────────────────

class ReportConfiguration(models.Model):
    """
    Saved report template.
    Supports scheduled generation (Celery Beat) and role-restricted visibility.
    TOR §3.4 – exportable reports (PDF, Excel, Word).
    """

    FORMAT_PDF = "pdf"
    FORMAT_EXCEL = "xlsx"
    FORMAT_WORD = "docx"

    FORMAT_CHOICES = (
        (FORMAT_PDF, _("PDF")),
        (FORMAT_EXCEL, _("Excel (.xlsx)")),
        (FORMAT_WORD, _("Word (.docx)")),
    )

    SCOPE_SYSTEM = "system"          # All cooperatives (government / apex view)
    SCOPE_COOPERATIVE = "cooperative"  # Single cooperative
    SCOPE_REGION = "region"

    SCOPE_CHOICES = (
        (SCOPE_SYSTEM, _("System-wide")),
        (SCOPE_COOPERATIVE, _("Single Cooperative")),
        (SCOPE_REGION, _("Region")),
    )

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # Report parameters: filters, grouping, selected KPIs, date range, etc.
    parameters = models.JSONField(
        blank=True,
        null=True,
        help_text=_(
            "JSON: {kpis:[...], filters:{region, sector, gender, age_group}, "
            "period_type, comparison_periods}"
        ),
    )
    scope = models.CharField(max_length=15, choices=SCOPE_CHOICES, default=SCOPE_SYSTEM)
    default_format = models.CharField(
        max_length=5, choices=FORMAT_CHOICES, default=FORMAT_PDF
    )
    # Roles that can view / run this report
    allowed_roles = models.JSONField(
        default=list,
        help_text=_("List of role slugs, e.g. ['government','apex_body']"),
    )
    # Scheduled export
    is_scheduled = models.BooleanField(default=False)
    schedule_cron = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Cron expression, e.g. '0 6 1 * *' = 1st of every month at 06:00"),
    )
    last_generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Report Configuration")
        verbose_name_plural = _("Report Configurations")
        ordering = ["name"]

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────────────────────
# Export Job  (TOR §3.4 – async report generation tracking)
# ─────────────────────────────────────────────────────────────────────────────

class ExportJob(models.Model):
    """
    Tracks an async (Celery) report generation job.
    Allows users to download generated reports from their dashboard.
    """

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_DONE = "done"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = (
        (STATUS_PENDING, _("Pending")),
        (STATUS_RUNNING, _("Running")),
        (STATUS_DONE, _("Done")),
        (STATUS_FAILED, _("Failed")),
    )

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    report_config = models.ForeignKey(
        ReportConfiguration,
        on_delete=models.CASCADE,
        related_name="export_jobs",
        null=True,
        blank=True,
    )
    requested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    format = models.CharField(max_length=5, choices=ReportConfiguration.FORMAT_CHOICES)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    file_url = models.URLField(blank=True, help_text=_("Cloudinary or S3 URL of generated file"))
    error_message = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    # Parameters snapshot at the time of generation
    parameters_snapshot = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = _("Export Job")
        verbose_name_plural = _("Export Jobs")
        ordering = ["-requested_at"]

    def __str__(self):
        return (
            f"{self.report_config} | {self.format.upper()} | "
            f"{self.get_status_display()}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Data Validation Rules  (TOR §3.1 – data quality, transparency, consistency)
# ─────────────────────────────────────────────────────────────────────────────

class DataValidationRule(models.Model):
    """
    Configurable rule applied to a model field to enforce data quality.
    Supports severity levels: error (blocks save) or warning (alerts only).
    """

    SEVERITY_ERROR = "error"
    SEVERITY_WARNING = "warning"

    SEVERITY_CHOICES = (
        (SEVERITY_ERROR, _("Error – blocks submission")),
        (SEVERITY_WARNING, _("Warning – flags for review")),
    )

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    # e.g. 'kpi_delinquency_rate > 0.25' → triggers alert
    rule_expression = models.TextField(
        help_text=_(
            "Safe Python expression, e.g. 'value > 0' or 'par_30_days / gross_loan_portfolio > 0.25'"
        )
    )
    applies_to_model = models.CharField(
        max_length=100,
        help_text=_("e.g. 'cooperatives.ProductionRecord'"),
    )
    applies_to_field = models.CharField(max_length=100, blank=True, null=True)
    severity = models.CharField(
        max_length=10, choices=SEVERITY_CHOICES, default=SEVERITY_WARNING
    )
    error_message_template = models.TextField(
        blank=True,
        help_text=_(
            "Human-readable message shown to users when rule is violated. "
            "Use {field} and {value} placeholders."
        ),
    )
    auto_fix_hint = models.TextField(
        blank=True,
        help_text=_("Suggested corrective action for the data entry officer"),
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Data Validation Rule")
        verbose_name_plural = _("Data Validation Rules")

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.name}"


class DataQualityAlert(models.Model):
    """
    An instance of a validation rule violation for a specific cooperative record.
    """

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    rule = models.ForeignKey(
        DataValidationRule, on_delete=models.CASCADE, related_name="alerts"
    )
    cooperative_id = models.PositiveIntegerField(
        help_text=_("ID of the Cooperative that owns the offending record")
    )
    content_type_label = models.CharField(max_length=100)
    record_id = models.PositiveIntegerField(
        help_text=_("PK of the record that triggered the alert")
    )
    field_name = models.CharField(max_length=100, blank=True)
    offending_value = models.TextField(blank=True)
    message = models.TextField()
    alert_date = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False, db_index=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_alerts",
    )
    resolved_date = models.DateTimeField(blank=True, null=True)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Data Quality Alert")
        verbose_name_plural = _("Data Quality Alerts")
        ordering = ["-alert_date"]

    def __str__(self):
        status = "✓" if self.is_resolved else "✗"
        return f"{status} Alert – {self.rule.name} (record #{self.record_id})"