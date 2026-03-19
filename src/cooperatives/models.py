from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import Region, User
import uuid

class Cooperative(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    COOPERATIVE_TYPES = (
        ("coffee", _("Coffee Cooperative")),
        ("cocoa", _("Cocoa Cooperative")),
        ("mixed", _("Mixed Coffee & Cocoa Cooperative")),
        ("sacco", _("SACCO (Savings and Credit Cooperative)")),
        ("other", _("Other Cooperative Type")),
    )
    name = models.CharField(max_length=255, unique=True)
    registration_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    type = models.CharField(max_length=50, choices=COOPERATIVE_TYPES)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="cooperatives")
    establishment_date = models.DateField(blank=True, null=True)
    contact_person = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="managed_cooperatives")
    address = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Cooperative")
        verbose_name_plural = _("Cooperatives")

    def __str__(self):
        return self.name


class WashingStation(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE, related_name="washing_stations")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, blank=True, null=True)
    village = models.CharField(max_length=100, blank=True, null=True)
    groupement = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = _("Washing Station")
        verbose_name_plural = _("Washing Stations")

    def __str__(self):
        return f"{self.name} ({self.cooperative})"

class Member(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    GENDER_CHOICES = (
        ("male", _("Male")),
        ("female", _("Female")),
        ("other", _("Other")),
    )
    AGE_GROUP_CHOICES = (
        ("youth", _("Youth (18-35)")),
        ("adult", _("Adult (36-60)")),
        ("senior", _("Senior (61+)")),
    )
    BOARD_ROLE_CHOICES = (
        ("president", _("President")),
        ("vice_president", _("Vice President")),
        ("secretary", _("Secretary")),
        ("treasurer", _("Treasurer")),
        ("advisor", _("Advisor")),
        ("other", _("Other")),
    )
    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE, related_name="members")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    member_id = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    age_group = models.CharField(max_length=10, choices=AGE_GROUP_CHOICES)
    
    # Geographic Data
    territory = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Territory"))
    groupement = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Groupement"))
    village = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Village"))
    subvillage = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Sub-village / Localité"))

    farmer_code = models.CharField(max_length=50, blank=True, null=True, unique=True, db_index=True, verbose_name=_("Farmer Code"))
    farmer_code_prefix = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    farmer_code_initials = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    farmer_code_number = models.PositiveIntegerField(blank=True, null=True, db_index=True)
    
    is_marginalized = models.BooleanField(default=False, verbose_name=_("From Marginalized Group"))
    is_board_member = models.BooleanField(default=False, verbose_name=_("Board Member"))
    board_role = models.CharField(max_length=50, choices=BOARD_ROLE_CHOICES, blank=True, null=True, verbose_name=_("Board Role"))
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_joined = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = _("Member")
        verbose_name_plural = _("Members")
        unique_together = ("cooperative", "member_id")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.member_id})"

    def clean(self):
        from django.core.exceptions import ValidationError
        import re

        if self.is_board_member and not self.board_role:
            raise ValidationError(_("Board role is required for board members."))

        if self.farmer_code:
            pattern = r"^[A-Z]+ [A-Z]+ \d{3}$"
            if not re.match(pattern, self.farmer_code):
                raise ValidationError({"farmer_code": _("Farmer code must match pattern 'TCC BMB 009'.")})

            prefix, initials, number_str = self.farmer_code.split(" ")
            self.farmer_code_prefix = prefix
            self.farmer_code_initials = initials
            try:
                self.farmer_code_number = int(number_str)
            except ValueError:
                raise ValidationError({"farmer_code": _("Invalid farmer code number segment.")})

class Farm(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="farms")
    farm_name = models.CharField(max_length=255, blank=True, null=True)
    size_hectares = models.DecimalField(max_digits=10, decimal_places=2)
    trees_count = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Number of Trees"))
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    class Meta:
        verbose_name = _("Farm")
        verbose_name_plural = _("Farms")

    def __str__(self):
        return self.farm_name or f"Farm of {self.member.first_name} {self.member.last_name}"

class ProductionRecord(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    CROP_TYPE_CHOICES = (
        ("coffee", _("Coffee")),
        ("cocoa", _("Cocoa")),
    )

    RECORD_TYPE_GENERIC = "generic"
    RECORD_TYPE_CHERRY = "cherry_delivery"
    RECORD_TYPE_CHOICES = (
        (RECORD_TYPE_GENERIC, _("Generic")),
        (RECORD_TYPE_CHERRY, _("Cherry Delivery")),
    )

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="production_records", blank=True, null=True)
    station = models.ForeignKey(WashingStation, on_delete=models.SET_NULL, related_name="production_records", blank=True, null=True)
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, related_name="production_records", blank=True, null=True)

    record_type = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES, default=RECORD_TYPE_GENERIC, db_index=True)

    crop_type = models.CharField(max_length=50, choices=CROP_TYPE_CHOICES)
    harvest_date = models.DateField(blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    reception_date = models.DateField(blank=True, null=True)

    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    quality_grade = models.CharField(max_length=50, blank=True, null=True)

    receipt_number = models.CharField(max_length=50, blank=True, null=True)
    base_price_fc = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_price_fc = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    exchange_rate_fc_usd = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    cherry_register_number = models.CharField(max_length=50, blank=True, null=True)
    delivery_report_number = models.CharField(max_length=50, blank=True, null=True)

    sync_uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True, db_index=True)
    is_locally_created = models.BooleanField(default=False)
    participants = models.ManyToManyField(User, related_name="production_records_participated", blank=True)

    class Meta:
        verbose_name = _("Production Record")
        verbose_name_plural = _("Production Records")
        ordering = ["-harvest_date"]

    def __str__(self):
        if self.record_type == self.RECORD_TYPE_CHERRY:
            return _("%(qty)s kg cherry delivery for %(member)s at %(station)s") % {
                "qty": self.quantity_kg,
                "member": self.member or _("Unknown member"),
                "station": self.station or _("Unknown station"),
            }
        return f"{self.crop_type} production on {self.farm} on {self.harvest_date}"

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils import timezone

        errors = {}

        if self.quantity_kg is not None and self.quantity_kg <= 0:
            errors["quantity_kg"] = _("Quantity must be greater than zero.")

        if self.record_type == self.RECORD_TYPE_GENERIC:
            if not self.farm:
                errors["farm"] = _("Farm is required for generic production records.")
            if self.harvest_date:
                if self.harvest_date > timezone.now().date():
                    errors["harvest_date"] = _("Harvest date cannot be in the future.")
            else:
                errors["harvest_date"] = _("Harvest date is required for generic production records.")

        if self.record_type == self.RECORD_TYPE_CHERRY:
            if not self.station:
                errors["station"] = _("Washing station is required for cherry deliveries.")
            if not self.member:
                errors["member"] = _("Member is required for cherry deliveries.")
            if not self.purchase_date:
                errors["purchase_date"] = _("Purchase date is required for cherry deliveries.")
            if not self.receipt_number:
                errors["receipt_number"] = _("Receipt number is required for cherry deliveries.")
            if self.base_price_fc is None:
                errors["base_price_fc"] = _("Base price (FC) is required for cherry deliveries.")

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.record_type == self.RECORD_TYPE_CHERRY and self.quantity_kg is not None and self.base_price_fc is not None:
            # total_price_fc stored for offline/reporting convenience
            self.total_price_fc = self.quantity_kg * self.base_price_fc
        super().save(*args, **kwargs)

class FinancialRecord(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    TRANSACTION_TYPE_CHOICES = (
        ("income", _("Income")),
        ("expense", _("Expense")),
        ("loan", _("Loan")),
        ("dividend", _("Dividend")),
        ("other", _("Other")),
    )
    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE, related_name="financial_records")
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Financial Record")
        verbose_name_plural = _("Financial Records")
        ordering = ["-transaction_date"]

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} for {self.cooperative} on {self.transaction_date}"


class Buyer(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = _("Buyer")
        verbose_name_plural = _("Buyers")
        ordering = ["name"]

    def __str__(self):
        return self.name


class CooperativeCertificate(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE, related_name="certificates")
    name = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255, blank=True, null=True)
    issued_date = models.DateField(blank=True, null=True)
    expires_date = models.DateField(blank=True, null=True)
    document = models.FileField(upload_to="cooperative_certificates/")
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Cooperative Certificate")
        verbose_name_plural = _("Cooperative Certificates")
        ordering = ["-issued_date"]

    def __str__(self):
        return f"{self.name} ({self.cooperative})"


class CooperativeSale(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE, related_name="sales")
    buyer = models.ForeignKey(Buyer, on_delete=models.PROTECT, related_name="sales")

    year = models.PositiveIntegerField()
    grade = models.CharField(max_length=50)
    destination_country = models.CharField(max_length=100)
    quantity_kg = models.DecimalField(max_digits=12, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_value = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    arrival_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Cooperative Sale")
        verbose_name_plural = _("Cooperative Sales")
        ordering = ["-year", "-quantity_kg"]

    def __str__(self):
        return f"{self.cooperative} → {self.buyer} ({self.year})"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.quantity_kg is not None and self.quantity_kg <= 0:
            raise ValidationError({"quantity_kg": _("Quantity must be positive.")})

    def save(self, *args, **kwargs):
        if self.price_per_kg is not None and self.quantity_kg is not None:
            self.total_value = self.price_per_kg * self.quantity_kg
        super().save(*args, **kwargs)
