# src/sync/models.py
# ─────────────────────────────────────────────────────────────────────────────
# CoopData – Offline Synchronisation models
# TOR §2   – offline functionality with synchronisation capabilities
# TOR §3.3 – mobile-first, low-bandwidth, offline data entry
#
# Changes vs original:
#   • Added conflict resolution strategy field (TOR requirement for robustness)
#   • SyncLog now captures bandwidth used (useful for low-bandwidth monitoring)
#   • PendingChange has explicit CONFLICT state + resolution notes
#   • Added SyncConflict model for manual conflict resolution workflow
#   • Device tracks app_version to help debug field issues
# ─────────────────────────────────────────────────────────────────────────────

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

class Device(models.Model):
    """
    A registered mobile device used for offline data entry.
    TOR §3.3 – offline capable (tablets, laptops).
    """

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    device_id = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("Hardware/OS unique identifier"),
    )
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="devices"
    )
    device_name = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Human-friendly name, e.g. 'Field Tablet – Manzini'"),
    )
    app_version = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("CoopData app version installed on this device"),
    )
    platform = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("e.g. Android, iOS, PWA"),
    )
    last_sync_at = models.DateTimeField(blank=True, null=True)
    last_seen_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Device")
        verbose_name_plural = _("Devices")

    def __str__(self):
        return f"{self.device_name or self.device_id} [{self.user.username}]"


class PendingChange(models.Model):
    """
    A data modification queued on a device while offline.
    Pushed to the server upon reconnection.
    """

    CHANGE_CREATE = "create"
    CHANGE_UPDATE = "update"
    CHANGE_DELETE = "delete"

    CHANGE_TYPE_CHOICES = (
        (CHANGE_CREATE, _("Create")),
        (CHANGE_UPDATE, _("Update")),
        (CHANGE_DELETE, _("Delete")),
    )

    STATE_PENDING = "pending"
    STATE_SYNCED = "synced"
    STATE_FAILED = "failed"
    STATE_CONFLICT = "conflict"

    STATE_CHOICES = (
        (STATE_PENDING, _("Pending")),
        (STATE_SYNCED, _("Synced")),
        (STATE_FAILED, _("Failed")),
        (STATE_CONFLICT, _("Conflict – Needs Review")),
    )

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name="pending_changes"
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    change_type = models.CharField(max_length=10, choices=CHANGE_TYPE_CHOICES)
    payload = models.JSONField(
        help_text=_("JSON snapshot of all changed fields and their new values")
    )
    local_timestamp = models.DateTimeField(
        help_text=_("When the change was made on the device (device clock)")
    )
    server_received_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the server received this change"),
    )
    state = models.CharField(
        max_length=10, choices=STATE_CHOICES, default=STATE_PENDING, db_index=True
    )
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Pending Change")
        verbose_name_plural = _("Pending Changes")
        ordering = ["local_timestamp"]
        indexes = [
            models.Index(fields=["state", "device"]),
        ]

    def __str__(self):
        return (
            f"{self.get_change_type_display()} – "
            f"{self.content_type} #{self.object_id} "
            f"[{self.get_state_display()}]"
        )


class SyncConflict(models.Model):
    """
    Created when a PendingChange conflicts with a server-side modification.
    Supports manual resolution by a regional officer or SACCO manager.
    TOR §5 Phase 2 – incorporation of user feedback.
    """

    RESOLUTION_CLIENT_WINS = "client_wins"
    RESOLUTION_SERVER_WINS = "server_wins"
    RESOLUTION_MANUAL = "manual_merge"

    RESOLUTION_CHOICES = (
        (RESOLUTION_CLIENT_WINS, _("Accept Device Version")),
        (RESOLUTION_SERVER_WINS, _("Keep Server Version")),
        (RESOLUTION_MANUAL, _("Manual Merge")),
    )

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    pending_change = models.OneToOneField(
        PendingChange, on_delete=models.CASCADE, related_name="conflict"
    )
    server_snapshot = models.JSONField(
        help_text=_("State of the record on the server at the time of conflict")
    )
    device_snapshot = models.JSONField(
        help_text=_("State proposed by the device")
    )
    conflicting_fields = models.JSONField(
        default=list,
        help_text=_("List of field names that differ between device and server"),
    )
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_conflicts",
    )
    resolution = models.CharField(
        max_length=20, choices=RESOLUTION_CHOICES, blank=True
    )
    final_state = models.JSONField(
        null=True, blank=True,
        help_text=_("The merged/chosen final state applied to the database"),
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Sync Conflict")
        verbose_name_plural = _("Sync Conflicts")
        ordering = ["-detected_at"]

    def __str__(self):
        status = "Resolved" if self.resolved_at else "Unresolved"
        return f"Conflict #{self.pk} – {status}"


class SyncLog(models.Model):
    """
    Record of a synchronisation session for a device.
    """

    STATUS_SUCCESS = "success"
    STATUS_PARTIAL = "partial"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = (
        (STATUS_SUCCESS, _("Success")),
        (STATUS_PARTIAL, _("Partial – Some Changes Failed")),
        (STATUS_FAILED, _("Failed")),
    )

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name="sync_logs"
    )
    sync_start_time = models.DateTimeField(auto_now_add=True)
    sync_end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_SUCCESS
    )
    message = models.TextField(blank=True)
    changes_uploaded = models.PositiveIntegerField(default=0)
    changes_downloaded = models.PositiveIntegerField(default=0)
    conflicts_detected = models.PositiveIntegerField(default=0)
    # Bandwidth tracking – useful for low-bandwidth optimisation
    bytes_uploaded = models.PositiveIntegerField(default=0)
    bytes_downloaded = models.PositiveIntegerField(default=0)
    # Network info
    connection_type = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("e.g. wifi, 3G, 4G, satellite"),
    )

    class Meta:
        verbose_name = _("Sync Log")
        verbose_name_plural = _("Sync Logs")
        ordering = ["-sync_start_time"]

    def __str__(self):
        return (
            f"{self.device} | {self.sync_start_time:%Y-%m-%d %H:%M} | "
            f"{self.get_status_display()}"
        )

    @property
    def duration_seconds(self) -> int | None:
        if self.sync_end_time:
            return int((self.sync_end_time - self.sync_start_time).total_seconds())
        return None