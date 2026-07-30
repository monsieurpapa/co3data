from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

# Note: audit logging lives in users.AuditLog and sync logging in sync.SyncLog —
# both are richer (typed actions, device/bandwidth tracking) than a generic
# core-level duplicate would be, so this app only holds the generic Attachment.

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

