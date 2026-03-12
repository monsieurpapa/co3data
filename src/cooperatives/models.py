from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import Region, User

class Cooperative(models.Model):
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

class Member(models.Model):
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
        """Enforce inclusive coding constraints."""
        from django.core.exceptions import ValidationError
        if self.age_group == 'youth' and not self.phone_number:
            # Youth members should ideally have a phone number for digital engagement
            pass # Or raise ValidationError if mandatory
        if self.is_board_member and not self.board_role:
            raise ValidationError(_("Board role is required for board members."))

class Farm(models.Model):
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
    CROP_TYPE_CHOICES = (
        ("coffee", _("Coffee")),
        ("cocoa", _("Cocoa")),
    )
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="production_records")
    crop_type = models.CharField(max_length=50, choices=CROP_TYPE_CHOICES)
    harvest_date = models.DateField()
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    quality_grade = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = _("Production Record")
        verbose_name_plural = _("Production Records")
        ordering = ["-harvest_date"]

    def __str__(self):
        return f"{self.crop_type} production on {self.farm} on {self.harvest_date}"

    def clean(self):
        """Perform basic data quality validation."""
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        if self.harvest_date > timezone.now().date():
            raise ValidationError(_("Harvest date cannot be in the future."))
        if self.quantity_kg <= 0:
            raise ValidationError(_("Quantity must be greater than zero."))

class FinancialRecord(models.Model):
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
