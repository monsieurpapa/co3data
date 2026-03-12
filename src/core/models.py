from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

class Attachment(models.Model):
    """Generic model for attaching files to other models."""
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    file = models.FileField(_("File"), upload_to="attachments/%Y/%m/")
    description = models.CharField(_("Description"), max_length=255, blank=True, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_attachments")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
        app_label = "core"

    def __str__(self):
        return f"Attachment {self.id} for {self.content_object}"

class AuditLog(models.Model):
    """Logs significant actions performed by users."""
    # Consider using a library like django-auditlog or django-simple-history for more robust logging
    ACTION_CHOICES = [
        (1, _("Addition")),
        (2, _("Change")),
        (3, _("Deletion")),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("User"))
    action_time = models.DateTimeField(_("Action Time"), auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Content Type"))
    object_id = models.TextField(_("Object ID"), blank=True, null=True)
    object_repr = models.CharField(_("Object Representation"), max_length=200)
    action_flag = models.PositiveSmallIntegerField(_("Action Flag"), choices=ACTION_CHOICES)
    change_message = models.TextField(_("Change Message"), blank=True)

    class Meta:
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")
        ordering = ["-action_time"]
        app_label = "core"

    def __str__(self):
        user_str = str(self.user) if self.user else "System"
        return f"{self.get_action_flag_display()} on {self.object_repr} by {user_str} at {self.action_time}"

class SyncLog(models.Model):
    """Tracks offline synchronization operations."""
    STATUS_CHOICES = [
        ("SUCCESS", _("Success")),
        ("FAILED", _("Failed")),
        ("PENDING", _("Pending")),
        ("IN_PROGRESS", _("In Progress")),
    ]
    DIRECTION_CHOICES = [
        ("UPLOAD", _("Upload to Server")),
        ("DOWNLOAD", _("Download to Client")),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="core_sync_logs")
    device_id = models.CharField(_("Device ID"), max_length=100, blank=True, null=True)
    sync_start_time = models.DateTimeField(_("Sync Start Time"), auto_now_add=True)
    sync_end_time = models.DateTimeField(_("Sync End Time"), null=True, blank=True)
    status = models.CharField(_("Status"), max_length=15, choices=STATUS_CHOICES, default="PENDING")
    direction = models.CharField(_("Direction"), max_length=10, choices=DIRECTION_CHOICES)
    records_processed = models.PositiveIntegerField(_("Records Processed"), default=0)
    details = models.TextField(_("Details/Error Message"), blank=True, null=True)

    class Meta:
        verbose_name = _("Sync Log")
        verbose_name_plural = _("Sync Logs")
        ordering = ["-sync_start_time"]
        app_label = "core"

    def __str__(self):
        user_str = str(self.user) if self.user else "System"
        return f"Sync {self.direction} by {user_str} at {self.sync_start_time} - {self.status}"

