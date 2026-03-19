from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=100, default="DRC")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = _("Région")
        verbose_name_plural = _("Régions")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.country})"

import uuid

class User(AbstractUser):
    # Custom user model extending Django's AbstractUser
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    USER_ROLES = (
        ('member', _('Cooperative Member')),
        ('field_agent', _('Field Agent')), # Mapped from agronomist in setup script logic
        ('manager', _('Cooperative Manager')),
        ('regional_officer', _('Regional Officer')),
        ('apex_body', _('Apex Body Representative')),
        ('government', _('Government Official')),
        ('admin', _('System Administrator')),
        # Keeping existing roles for compatibility
        ('agronomist', _('Agronomist')),
        ('supervisor', _('Agronomist Supervisor')),
        ('station_chef', _('Washing Station Chef')),
    )

    ROLE_PERMISSIONS = {
        "member":           ["view_own_data"],
        "field_agent":      ["view_cooperative","add_member","add_productionrecord","add_submission"],
        "agronomist":       ["view_cooperative","add_member","add_productionrecord","add_submission"],
        "manager":          ["view_cooperative","add_member","change_member",
                             "add_productionrecord","add_financialrecord","view_reports"],
        "regional_officer": ["view_region","view_reports","export_data"],
        "apex_body":        ["view_all","view_reports","export_data"],
        "government":       ["view_all","view_reports","export_data"],
        "admin":            ["all"],
    }

    role = models.CharField(max_length=20, choices=USER_ROLES, default='member')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    cooperative = models.ForeignKey("cooperatives.Cooperative", on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name="staff_users")
    preferred_language = models.CharField(
        max_length=5, choices=[("fr","Français"),("sw","Kiswahili"),("en","English")],
        default="fr")
    last_sync_at = models.DateTimeField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def can(self, permission: str) -> bool:
        role_perms = self.ROLE_PERMISSIONS.get(self.role, [])
        return "all" in role_perms or permission in role_perms

    def get_accessible_cooperatives(self):
        from cooperatives.models import Cooperative
        if self.can("view_all"):
            return Cooperative.objects.all()
        if self.can("view_region") and self.region:
            return Cooperative.objects.filter(region=self.region)
        if self.cooperative:
            return Cooperative.objects.filter(pk=self.cooperative.pk)
        return Cooperative.objects.none()
