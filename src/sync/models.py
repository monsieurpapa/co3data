from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid


class Device(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    device_id = models.CharField(max_length=255, unique=True, help_text=_("Unique identifier for the mobile device"))
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="devices")
    last_sync_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Device")
        verbose_name_plural = _("Devices")

    def __str__(self):
        return f"Device {self.device_id} for {self.user.username}"


class PendingChange(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    CHANGE_TYPE_CHOICES = (
        ("create", _("Create")),
        ("update", _("Update")),
        ("delete", _("Delete")),
    )
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="pending_changes")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    change_type = models.CharField(max_length=10, choices=CHANGE_TYPE_CHOICES)
    payload = models.JSONField(help_text=_("JSON representation of the changed data"))
    timestamp = models.DateTimeField(auto_now_add=True)
    is_synced = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    local_uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True, null=True, blank=True)

    class Meta:
        verbose_name = _("Pending Change")
        verbose_name_plural = _("Pending Changes")
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.change_type} from {self.device}"


class SyncLog(models.Model):
    CONFLICT_STRATEGY_LAST_WRITE = "last_write_wins"
    CONFLICT_STRATEGY_SERVER = "server_wins"
    CONFLICT_STRATEGY_CLIENT = "client_wins"
    CONFLICT_STRATEGY_MANUAL = "manual"

    CONFLICT_STRATEGY_CHOICES = (
        (CONFLICT_STRATEGY_LAST_WRITE, _("Last write wins")),
        (CONFLICT_STRATEGY_SERVER, _("Server wins")),
        (CONFLICT_STRATEGY_CLIENT, _("Client wins")),
        (CONFLICT_STRATEGY_MANUAL, _("Manual resolution")),
    )

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="sync_logs")
    sync_start_time = models.DateTimeField(auto_now_add=True)
    sync_end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=50, help_text=_("e.g., Success, Failed, Partial"))
    message = models.TextField(blank=True, null=True)
    changes_uploaded = models.PositiveIntegerField(default=0)
    changes_downloaded = models.PositiveIntegerField(default=0)
    conflict_strategy = models.CharField(max_length=32, choices=CONFLICT_STRATEGY_CHOICES, blank=True, null=True)

    class Meta:
        verbose_name = _("Synchronization Log")
        verbose_name_plural = _("Synchronization Logs")
        ordering = ["-sync_start_time"]

    def __str__(self):
        return f"Sync for {self.device} at {self.sync_start_time} - {self.status}"
