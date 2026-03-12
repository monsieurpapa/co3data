from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from .models import PendingChange

class SyncManager:
    """Manager for processing offline synchronization changes."""

    @staticmethod
    def process_pending_change(change_id):
        """Processes a single pending change and applies it to the target model."""
        try:
            change = PendingChange.objects.get(id=change_id, is_synced=False)
            model = change.content_type.model_class()
            payload = change.payload
            
            if change.change_type == 'create':
                # Create new instance
                instance = model(**payload)
                instance.save()
                change.object_id = instance.id
            
            elif change.change_type == 'update':
                # Update existing instance
                instance = model.objects.get(id=change.object_id)
                for field, value in payload.items():
                    set_base = getattr(instance, field)
                    setattr(instance, field, value)
                instance.save()
            
            elif change.change_type == 'delete':
                # Delete existing instance
                model.objects.filter(id=change.object_id).delete()
            
            change.is_synced = True
            change.save()
            return True
            
        except Exception as e:
            print(f"Error processing change {change_id}: {e}")
            change.attempts += 1
            change.save()
            return False

    @classmethod
    def process_device_changes(cls, device):
        """Processes all unsynced changes for a specific device."""
        changes = PendingChange.objects.filter(device=device, is_synced=False).order_by('timestamp')
        success_count = 0
        for change in changes:
            if cls.process_pending_change(change.id):
                success_count += 1
        return success_count
