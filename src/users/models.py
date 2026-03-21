# src/users/models.py
# ─────────────────────────────────────────────────────────────────────────────
# CoopData – User & Region models
# Aligned with DGRV / MCIT Eswatini TOR (SUCOSA II)
# Changes vs original:
#   • USER_ROLES updated to reflect Eswatini stakeholder hierarchy
#     (MCIT, Federation, Apex, SACCO, Regional Officer, Field Agent, Admin)
#   • Added AuditLog model (TOR §3.3 – audit trails)
#   • Added is_2fa_required flag per role (TOR §4 – 2FA for admins)
#   • Added preferred_language field (TOR §3.3 – multilingual)
#   • Added is_marginalized flag for inclusion tracking (TOR §3.1)
#   • Region now carries country ISO code for future multi-country expansion
# ─────────────────────────────────────────────────────────────────────────────

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

class Region(models.Model):
    """
    Geographical region / inkhundla.
    Supports multi-country expansion (Eswatini, Mozambique, etc.)
    """
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    # ISO 3166-1 alpha-2: SZ = Eswatini, MZ = Mozambique, ZA = South Africa
    country_code = models.CharField(
        max_length=2,
        default="SZ",
        help_text=_("ISO 3166-1 alpha-2 country code"),
    )
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Region")
        verbose_name_plural = _("Regions")
        unique_together = ("name", "country_code")
        ordering = ["country_code", "name"]

    def __str__(self):
        return f"{self.name} ({self.country_code})"


class User(AbstractUser):
    """
    Custom user model.  Role hierarchy matches the Eswatini cooperative
    ecosystem: MCIT > Federation > Apex Body > Regional Officer >
    SACCO Manager > Field Agent > Member.

    TOR §3.3 – multi-level, role-based access.
    TOR §4   – 2FA mandatory for admin and government roles.
    """

    # ── Role choices ──────────────────────────────────────────────────────────
    ROLE_SYSTEM_ADMIN = "system_admin"
    ROLE_GOVERNMENT = "government"          # MCIT officials
    ROLE_APEX_BODY = "apex_body"            # National Federation / Apex
    ROLE_REGIONAL_OFFICER = "regional_officer"
    ROLE_SACCO_MANAGER = "sacco_manager"   # Cooperative/SACCO manager
    ROLE_FIELD_AGENT = "field_agent"        # Data entry in the field
    ROLE_MEMBER = "member"                  # Cooperative member (read-only)
    ROLE_AUDITOR = "auditor"                # External auditor (read-only)

    USER_ROLES = (
        (ROLE_SYSTEM_ADMIN, _("System Administrator")),
        (ROLE_GOVERNMENT, _("Government Official (MCIT)")),
        (ROLE_APEX_BODY, _("Apex Body / Federation Representative")),
        (ROLE_REGIONAL_OFFICER, _("Regional Officer")),
        (ROLE_SACCO_MANAGER, _("SACCO / Cooperative Manager")),
        (ROLE_FIELD_AGENT, _("Field Agent / Data Collector")),
        (ROLE_MEMBER, _("Cooperative Member")),
        (ROLE_AUDITOR, _("Auditor (Read-Only)")),
    )

    # Roles that MUST have 2FA enabled (TOR §4)
    ROLES_REQUIRING_2FA = {ROLE_SYSTEM_ADMIN, ROLE_GOVERNMENT, ROLE_APEX_BODY}

    # ── Language choices (TOR §3.3) ───────────────────────────────────────────
    LANG_ENGLISH = "en"
    LANG_SISWATI = "ss"
    LANG_PORTUGUESE = "pt"

    LANGUAGE_CHOICES = (
        (LANG_ENGLISH, _("English")),
        (LANG_SISWATI, _("SiSwati")),
        (LANG_PORTUGUESE, _("Portuguese")),
    )

    # ── Fields ────────────────────────────────────────────────────────────────
    role = models.CharField(
        max_length=25,
        choices=USER_ROLES,
        default=ROLE_MEMBER,
        db_index=True,
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    preferred_language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default=LANG_ENGLISH,
        help_text=_("Interface language preference"),
    )
    # Inclusion tracking (TOR §3.1 – mandatory coding for marginalized groups)
    is_youth = models.BooleanField(
        default=False,
        help_text=_("Flag if user/member is aged 18-35"),
    )
    is_marginalized = models.BooleanField(
        default=False,
        help_text=_("Flag for inclusion-based programmes (TOR §3.1)"),
    )
    # Security
    is_2fa_enrolled = models.BooleanField(
        default=False,
        help_text=_("True once the user has completed 2FA setup"),
    )
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    force_password_change = models.BooleanField(
        default=False,
        help_text=_("Force user to change password on next login"),
    )

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return f"{self.get_full_name() or self.username} [{self.get_role_display()}]"

    @property
    def requires_2fa(self) -> bool:
        """Returns True if this role mandates 2FA (TOR §4)."""
        return self.role in self.ROLES_REQUIRING_2FA


# ─────────────────────────────────────────────────────────────────────────────
# Audit Trail (TOR §3.3 – user and access management with audit trails)
# ─────────────────────────────────────────────────────────────────────────────

class AuditLog(models.Model):
    """
    Immutable record of every create / update / delete action performed
    by any user.  Satisfies TOR §3.3 audit trail and §4 access logs.

    Consider using django-simple-history for automatic per-model history;
    this model captures higher-level events (login, export, role changes).
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
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    # Human-readable description
    description = models.TextField(blank=True)
    # The affected model / object (optional)
    content_type_label = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=50, blank=True)
    # Request metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    # For sensitive changes, store a before/after snapshot
    before_state = models.JSONField(blank=True, null=True)
    after_state = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")
        ordering = ["-timestamp"]
        # Audit logs must never be editable — enforce at DB level if possible
        default_permissions = ("view",)

    def __str__(self):
        actor = self.user.username if self.user else "system"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {actor} → {self.get_action_display()}"