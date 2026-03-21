# src/cooperatives/models.py
# ─────────────────────────────────────────────────────────────────────────────
# CoopData – Cooperatives & SACCO financial models
# Aligned with DGRV / MCIT Eswatini TOR (SUCOSA II)
#
# Key changes vs original:
#   • Cooperative.type updated for Eswatini context (SACCO primary, removed
#     coffee/cocoa which were Central-Africa focused)
#   • Added SACCOFinancialSummary – period-based snapshot for KPI calculation
#     (delinquency rate, liquidity, capital adequacy, PAR — TOR §3.1)
#   • Added LoanPortfolio / LoanAccount – core SACCO lending data
#   • Added SavingsAccount – member savings & shares tracking
#   • Added BoardMember – board composition tracking (TOR §3.1 KPI)
#   • Added TrainingRecord – training hours KPI (TOR §3.1)
#   • Mandatory gender/youth/marginalized coding throughout (TOR §3.1)
# ─────────────────────────────────────────────────────────────────────────────

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import Region, User
import uuid

# ── Shared choice constants ───────────────────────────────────────────────────

GENDER_CHOICES = (
    ("male", _("Male")),
    ("female", _("Female")),
    ("other", _("Other / Prefer not to say")),
)

AGE_GROUP_CHOICES = (
    ("youth", _("Youth (18–35)")),
    ("adult", _("Adult (36–60)")),
    ("senior", _("Senior (61+)")),
    ("under18", _("Under 18")),
)


# ─────────────────────────────────────────────────────────────────────────────
# Cooperative
# ─────────────────────────────────────────────────────────────────────────────

class Cooperative(models.Model):
    """
    Central entity representing a registered cooperative or SACCO in Eswatini.
    """

    TYPE_SACCO = "sacco"
    TYPE_AGRI = "agricultural"
    TYPE_CONSUMER = "consumer"
    TYPE_HOUSING = "housing"
    TYPE_MULTIPURPOSE = "multipurpose"
    TYPE_WORKER = "worker"
    TYPE_OTHER = "other"

    COOPERATIVE_TYPES = (
        (TYPE_SACCO, _("SACCO (Savings & Credit Cooperative)")),
        (TYPE_AGRI, _("Agricultural Cooperative")),
        (TYPE_CONSUMER, _("Consumer Cooperative")),
        (TYPE_HOUSING, _("Housing Cooperative")),
        (TYPE_MULTIPURPOSE, _("Multi-Purpose Cooperative")),
        (TYPE_WORKER, _("Worker / Producer Cooperative")),
        (TYPE_OTHER, _("Other")),
    )

    STATUS_ACTIVE = "active"
    STATUS_DORMANT = "dormant"
    STATUS_DEREGISTERED = "deregistered"
    STATUS_PENDING = "pending"

    STATUS_CHOICES = (
        (STATUS_ACTIVE, _("Active")),
        (STATUS_DORMANT, _("Dormant")),
        (STATUS_DEREGISTERED, _("Deregistered")),
        (STATUS_PENDING, _("Pending Registration")),
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    name = models.CharField(max_length=255, unique=True)
    registration_number = models.CharField(
        max_length=100, unique=True, blank=True, null=True
    )
    type = models.CharField(
        max_length=30, choices=COOPERATIVE_TYPES, db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        db_index=True,
    )
    sector = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Economic sector, e.g. agriculture, finance, retail"),
    )

    # ── Location ──────────────────────────────────────────────────────────────
    region = models.ForeignKey(
        Region, on_delete=models.PROTECT, related_name="cooperatives"
    )
    physical_address = models.TextField(blank=True, null=True)
    postal_address = models.TextField(blank=True, null=True)

    # ── Contacts ──────────────────────────────────────────────────────────────
    contact_person = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="managed_cooperatives",
    )
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # ── Registration ──────────────────────────────────────────────────────────
    establishment_date = models.DateField(blank=True, null=True)
    registration_date = models.DateField(blank=True, null=True)
    apex_body = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="member_cooperatives",
        help_text=_("Parent Apex body or Federation, if any"),
    )

    # ── Mambu integration (TOR §3.2) ──────────────────────────────────────────
    mambu_encoded_key = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text=_("Mambu branch/centre encoded key for API sync"),
    )
    mambu_last_synced = models.DateTimeField(blank=True, null=True)

    # ── Meta ──────────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Cooperative")
        verbose_name_plural = _("Cooperatives")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} [{self.get_type_display()}]"


# ─────────────────────────────────────────────────────────────────────────────
# Member
# ─────────────────────────────────────────────────────────────────────────────

class Member(models.Model):
    """
    Individual cooperative / SACCO member.
    Mandatory gender, youth, and marginalized coding (TOR §3.1).
    """

    cooperative = models.ForeignKey(
        Cooperative, on_delete=models.CASCADE, related_name="members"
    )
    # Identity
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    member_id = models.CharField(max_length=50)
    national_id = models.CharField(max_length=50, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    # TOR §3.1 – mandatory inclusion coding
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, db_index=True)
    age_group = models.CharField(
        max_length=10, choices=AGE_GROUP_CHOICES, db_index=True
    )
    is_youth = models.BooleanField(default=False, db_index=True)
    is_marginalized = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_("Persons with disabilities, widows, displaced persons, etc."),
    )
    is_board_member = models.BooleanField(default=False)
    # Contact
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    physical_address = models.TextField(blank=True, null=True)
    # Status
    date_joined = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    exit_date = models.DateField(blank=True, null=True)
    exit_reason = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Member")
        verbose_name_plural = _("Members")
        unique_together = ("cooperative", "member_id")
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.member_id})"


# ─────────────────────────────────────────────────────────────────────────────
# Board Composition (TOR §3.1 KPI – board composition)
# ─────────────────────────────────────────────────────────────────────────────

class BoardMember(models.Model):
    """Tracks board / committee composition for KPI reporting (TOR §3.1)."""

    POSITION_CHOICES = (
        ("chairperson", _("Chairperson")),
        ("vice_chairperson", _("Vice-Chairperson")),
        ("secretary", _("Secretary")),
        ("treasurer", _("Treasurer")),
        ("member", _("Board Member")),
        ("supervisor", _("Supervisory Committee Member")),
    )

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    cooperative = models.ForeignKey(
        Cooperative, on_delete=models.CASCADE, related_name="board_members"
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="board_positions",
    )
    position = models.CharField(max_length=30, choices=POSITION_CHOICES)
    term_start = models.DateField()
    term_end = models.DateField(blank=True, null=True)
    # For KPI: gender & youth of board members
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    is_youth = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Board Member")
        verbose_name_plural = _("Board Members")

    def __str__(self):
        return f"{self.cooperative} – {self.get_position_display()}"


# ─────────────────────────────────────────────────────────────────────────────
# Training Record (TOR §3.1 KPI – training hours)
# ─────────────────────────────────────────────────────────────────────────────

class TrainingRecord(models.Model):
    """Records training events and participation for KPI tracking."""

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    cooperative = models.ForeignKey(
        Cooperative, on_delete=models.CASCADE, related_name="training_records"
    )
    title = models.CharField(max_length=255)
    training_date = models.DateField()
    duration_hours = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        validators=[MinValueValidator(Decimal("0.5"))],
    )
    provider = models.CharField(max_length=255, blank=True)
    topic = models.CharField(max_length=255, blank=True)
    # Participants
    total_participants = models.PositiveIntegerField(default=0)
    female_participants = models.PositiveIntegerField(default=0)
    youth_participants = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Training Record")
        verbose_name_plural = _("Training Records")
        ordering = ["-training_date"]

    def __str__(self):
        return f"{self.title} ({self.training_date})"


# ─────────────────────────────────────────────────────────────────────────────
# SACCO Financial Summary (periodic snapshot – basis for KPIs)
# TOR §3.1 – KPIs: revenue, delinquency rate, liquidity ratios, capital
# ─────────────────────────────────────────────────────────────────────────────

class SACCOFinancialSummary(models.Model):
    """
    Period-end financial snapshot for a SACCO.
    Stores the raw numbers from which all financial KPIs are computed
    (delinquency rate, PAR, liquidity ratio, ROA, capital adequacy, etc.).

    One record per cooperative per reporting period.
    """

    PERIOD_MONTHLY = "monthly"
    PERIOD_QUARTERLY = "quarterly"
    PERIOD_ANNUAL = "annual"

    PERIOD_CHOICES = (
        (PERIOD_MONTHLY, _("Monthly")),
        (PERIOD_QUARTERLY, _("Quarterly")),
        (PERIOD_ANNUAL, _("Annual")),
    )

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    cooperative = models.ForeignKey(
        Cooperative, on_delete=models.CASCADE, related_name="financial_summaries"
    )
    period_type = models.CharField(max_length=15, choices=PERIOD_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()
    submitted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_summaries",
    )

    # ── Balance Sheet items ───────────────────────────────────────────────────
    total_assets = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_liabilities = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_equity = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    share_capital = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    retained_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    # Savings / deposits
    total_savings = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_deposits = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # ── Loan Portfolio ────────────────────────────────────────────────────────
    gross_loan_portfolio = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    loans_disbursed_period = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text=_("Total loans disbursed during this period"),
    )
    loan_repayments_received = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    # Portfolio at Risk (PAR) values – TOR KPI: delinquency rate
    par_30_days = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text=_("Outstanding balance of loans overdue > 30 days"),
    )
    par_90_days = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text=_("Outstanding balance of loans overdue > 90 days"),
    )
    write_offs_period = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    loan_loss_provisions = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # ── Income Statement ──────────────────────────────────────────────────────
    interest_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    fee_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    operating_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    interest_expense = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_surplus = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # ── Membership snapshot ───────────────────────────────────────────────────
    total_members = models.PositiveIntegerField(default=0)
    active_borrowers = models.PositiveIntegerField(default=0)
    active_savers = models.PositiveIntegerField(default=0)
    new_members_period = models.PositiveIntegerField(default=0)
    female_members = models.PositiveIntegerField(default=0)
    youth_members = models.PositiveIntegerField(default=0)

    # ── Computed KPI fields (populated by Celery task after submission) ───────
    # Stored so dashboards don't need to recompute every time
    kpi_delinquency_rate = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True,
        help_text=_("PAR30 / Gross Loan Portfolio"),
    )
    kpi_liquidity_ratio = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True,
        help_text=_("Liquid Assets / Total Deposits"),
    )
    kpi_capital_adequacy = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True,
        help_text=_("Total Equity / Total Assets"),
    )
    kpi_roa = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True,
        help_text=_("Net Surplus / Average Total Assets"),
    )
    kpi_cost_per_borrower = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text=_("Operating Expenses / Active Borrowers"),
    )
    kpi_portfolio_yield = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True,
        help_text=_("Interest Income / Average Gross Loan Portfolio"),
    )
    kpi_operational_self_sufficiency = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True,
        help_text=_("Total Income / (Operating + Loan Loss + Interest Expenses)"),
    )
    kpi_youth_participation_rate = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True,
        help_text=_("Youth Members / Total Members"),
    )
    kpi_female_participation_rate = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True,
    )
    kpi_training_hours_per_member = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
    )

    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("SACCO Financial Summary")
        verbose_name_plural = _("SACCO Financial Summaries")
        unique_together = ("cooperative", "period_type", "period_start")
        ordering = ["-period_end"]

    def __str__(self):
        return (
            f"{self.cooperative.name} | "
            f"{self.get_period_type_display()} | "
            f"{self.period_start} – {self.period_end}"
        )

    def compute_kpis(self):
        """
        Populate computed KPI fields from the raw financial data.
        Called by a Celery task after submission or verification.
        """
        def safe_div(numerator, denominator):
            if denominator and denominator != 0:
                return round(numerator / denominator, 4)
            return None

        self.kpi_delinquency_rate = safe_div(self.par_30_days, self.gross_loan_portfolio)
        self.kpi_capital_adequacy = safe_div(self.total_equity, self.total_assets)
        self.kpi_roa = safe_div(self.net_surplus, self.total_assets)
        self.kpi_youth_participation_rate = safe_div(self.youth_members, self.total_members)
        self.kpi_female_participation_rate = safe_div(self.female_members, self.total_members)

        liquid_assets = self.total_assets - self.gross_loan_portfolio  # simplified
        self.kpi_liquidity_ratio = safe_div(liquid_assets, self.total_deposits)

        self.kpi_portfolio_yield = safe_div(
            self.interest_income, self.gross_loan_portfolio
        )
        if self.active_borrowers and self.active_borrowers > 0:
            self.kpi_cost_per_borrower = round(
                self.operating_expenses / self.active_borrowers, 2
            )

        total_costs = (
            self.operating_expenses + self.loan_loss_provisions + self.interest_expense
        )
        self.kpi_operational_self_sufficiency = safe_div(self.total_income, total_costs)

        self.save(
            update_fields=[
                "kpi_delinquency_rate",
                "kpi_liquidity_ratio",
                "kpi_capital_adequacy",
                "kpi_roa",
                "kpi_cost_per_borrower",
                "kpi_portfolio_yield",
                "kpi_operational_self_sufficiency",
                "kpi_youth_participation_rate",
                "kpi_female_participation_rate",
            ]
        )


# ─────────────────────────────────────────────────────────────────────────────
# Savings Account
# ─────────────────────────────────────────────────────────────────────────────

class SavingsAccount(models.Model):
    """Member savings / share account within a SACCO."""

    ACCOUNT_TYPE_SHARES = "shares"
    ACCOUNT_TYPE_SAVINGS = "savings"
    ACCOUNT_TYPE_FIXED = "fixed_deposit"
    ACCOUNT_TYPE_HOLIDAY = "holiday"

    ACCOUNT_TYPES = (
        (ACCOUNT_TYPE_SHARES, _("Share Capital Account")),
        (ACCOUNT_TYPE_SAVINGS, _("Voluntary Savings Account")),
        (ACCOUNT_TYPE_FIXED, _("Fixed / Term Deposit")),
        (ACCOUNT_TYPE_HOLIDAY, _("Holiday / Club Savings")),
    )

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="savings_accounts"
    )
    account_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal("0.00"),
        help_text=_("Annual interest rate, e.g. 0.0350 = 3.50%"),
    )
    opened_date = models.DateField()
    is_active = models.BooleanField(default=True)
    # Mambu reference
    mambu_encoded_key = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = _("Savings Account")
        verbose_name_plural = _("Savings Accounts")
        unique_together = ("member", "account_number")

    def __str__(self):
        return f"{self.member} – {self.get_account_type_display()} ({self.account_number})"


# ─────────────────────────────────────────────────────────────────────────────
# Loan Account
# ─────────────────────────────────────────────────────────────────────────────

class LoanAccount(models.Model):
    """Individual member loan — feeds into delinquency and PAR KPIs."""

    STATUS_ACTIVE = "active"
    STATUS_CLOSED = "closed"
    STATUS_WRITTEN_OFF = "written_off"
    STATUS_RESTRUCTURED = "restructured"

    STATUS_CHOICES = (
        (STATUS_ACTIVE, _("Active")),
        (STATUS_CLOSED, _("Closed / Repaid")),
        (STATUS_WRITTEN_OFF, _("Written Off")),
        (STATUS_RESTRUCTURED, _("Restructured")),
    )

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="loan_accounts"
    )
    loan_id = models.CharField(max_length=50, unique=True)
    disbursement_date = models.DateField()
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=4,
        help_text=_("Annual interest rate"),
    )
    term_months = models.PositiveIntegerField()
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    arrears_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text=_("Total amount in arrears (overdue)"),
    )
    days_in_arrears = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    purpose = models.CharField(max_length=255, blank=True)
    maturity_date = models.DateField(blank=True, null=True)
    # Mambu reference
    mambu_encoded_key = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = _("Loan Account")
        verbose_name_plural = _("Loan Accounts")
        ordering = ["-disbursement_date"]

    def __str__(self):
        return f"Loan {self.loan_id} – {self.member} (SZL {self.outstanding_balance})"

    @property
    def is_delinquent(self) -> bool:
        return self.days_in_arrears > 0

    @property
    def is_par30(self) -> bool:
        return self.days_in_arrears >= 30