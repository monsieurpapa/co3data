import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)
    # ISO 3166-1 alpha-2 country code. Default "CD" = Democratic Republic of Congo.
    country_code = models.CharField(max_length=2, default="CD", help_text=_("ISO 3166-1 alpha-2 country code"))
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = _("Région")
        verbose_name_plural = _("Régions")
        unique_together = ("name", "country_code")
        ordering = ["country_code", "name"]

    def __str__(self):
        return f"{self.name} ({self.country_code})"


class User(AbstractUser):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    ROLE_MEMBER = "member"
    ROLE_FIELD_AGENT = "field_agent"
    ROLE_MANAGER = "manager"
    ROLE_REGIONAL_OFFICER = "regional_officer"
    ROLE_APEX_BODY = "apex_body"
    ROLE_GOVERNMENT = "government"
    ROLE_ADMIN = "admin"

    USER_ROLES = (
        (ROLE_MEMBER, _("Cooperative Member")),
        (ROLE_FIELD_AGENT, _("Field Agent")),
        (ROLE_MANAGER, _("Cooperative Manager")),
        (ROLE_REGIONAL_OFFICER, _("Regional Officer")),
        (ROLE_APEX_BODY, _("Apex Body Representative")),
        (ROLE_GOVERNMENT, _("Government Official")),
        (ROLE_ADMIN, _("System Administrator")),
    )

    ROLE_PERMISSIONS = {
        ROLE_MEMBER:           ["view_own_data"],
        ROLE_FIELD_AGENT:      ["view_cooperative", "add_member", "add_productionrecord", "add_submission"],
        ROLE_MANAGER:          ["view_cooperative", "add_member", "change_member",
                                 "add_productionrecord", "add_financialrecord", "view_reports"],
        ROLE_REGIONAL_OFFICER: ["view_region", "view_reports", "export_data"],
        ROLE_APEX_BODY:        ["view_all", "view_reports", "export_data"],
        ROLE_GOVERNMENT:       ["view_all", "view_reports", "export_data"],
        ROLE_ADMIN:            ["all"],
    }

    # Roles that must have 2FA enabled.
    ROLES_REQUIRING_2FA = {ROLE_ADMIN, ROLE_GOVERNMENT, ROLE_APEX_BODY}

    LANGUAGE_CHOICES = (
        ("fr", _("Français")),
        ("sw", _("Kiswahili")),
        ("en", _("English")),
    )

    role = models.CharField(max_length=20, choices=USER_ROLES, default=ROLE_MEMBER, db_index=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    cooperative = models.ForeignKey(
        "cooperatives.Cooperative",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_users",
    )
    preferred_language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default="fr", blank=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", null=True, blank=True)

    # Security
    is_2fa_enrolled = models.BooleanField(default=False, help_text=_("True once the user has completed 2FA setup"))
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    force_password_change = models.BooleanField(default=False, help_text=_("Force user to change password on next login"))

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def requires_2fa(self) -> bool:
        return self.role in self.ROLES_REQUIRING_2FA

    def can(self, permission: str) -> bool:
        role_perms = self.ROLE_PERMISSIONS.get(self.role, [])
        return "all" in role_perms or permission in role_perms

    def get_accessible_cooperatives(self):
        from cooperatives.models import Cooperative
        if self.is_superuser or self.can("view_all"):
            return Cooperative.objects.all()
        if self.can("view_region") and self.region:
            return Cooperative.objects.filter(region=self.region)
        if self.cooperative:
            return Cooperative.objects.filter(pk=self.cooperative.pk)
        return Cooperative.objects.none()


class AuditLog(models.Model):
    """
    Immutable record of significant actions performed by any user.
    Canonical audit trail for the project (core.AuditLog was a duplicate and has been removed).
    """

    ACTION_LOGIN = "login"
    ACTION_LOGOUT = "logout"
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_EXPORT = "export"
    ACTION_SYNC = "sync"
    ACTION_ROLE_CHANGE = "role_change"

    ACTION_CHOICES = (
        (ACTION_LOGIN, _("Login")),
        (ACTION_LOGOUT, _("Logout")),
        (ACTION_CREATE, _("Record Created")),
        (ACTION_UPDATE, _("Record Updated")),
        (ACTION_DELETE, _("Record Deleted")),
        (ACTION_EXPORT, _("Report / Data Exported")),
        (ACTION_SYNC, _("Offline Sync")),
        (ACTION_ROLE_CHANGE, _("User Role Changed")),
    )

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    description = models.TextField(blank=True)
    content_type_label = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    before_state = models.JSONField(blank=True, null=True)
    after_state = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")
        ordering = ["-timestamp"]
        default_permissions = ("view",)

    def __str__(self):
        actor = self.user.username if self.user else "system"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {actor} → {self.get_action_display()}"
