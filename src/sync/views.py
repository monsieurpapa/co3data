from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import RoleRequiredMixin
from .models import Device, PendingChange
from rest_framework.views import APIView

from .models import Device, PendingChange, SyncLog

class SyncPushAPIView(APIView):
    """Endpoint for mobile devices to push pending changes."""
    def post(self, request):
        data = request.data
        changes = data.get("changes", [])
        device_id = data.get("device_id")
        
        try:
            device = Device.objects.get(device_id=device_id)
            # Log the sync attempt
            log = SyncLog.objects.create(
                device=device,
                status="Success",
                changes_uploaded=len(changes),
                message=f"Received {len(changes)} changes from mobile device."
            )
            log.sync_end_time = timezone.now()
            log.save()
            
            # In a full implementation, we would loop through changes and create PendingChange objects
            # or apply them directly.
            
            return Response({"status": "success", "processed": len(changes), "log_id": log.id}, status=status.HTTP_200_OK)
        except Device.DoesNotExist:
            return Response({"status": "error", "message": "Device not registered"}, status=status.HTTP_400_BAD_REQUEST)

class SyncPullAPIView(APIView):
    """Endpoint for mobile devices to pull latest updates."""
    def get(self, request):
        last_sync = request.query_params.get("last_sync")
        # In a real implementation, we would query for all changes since last_sync
        # and return them in a serialized format.
        return Response({
            "status": "success",
            "server_time": timezone.now().isoformat(),
            "updates": []
        }, status=status.HTTP_200_OK)

class SyncStatusView(RoleRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = 'sync/sync_status.html'

    required_roles = ["manager", "regional_officer", "admin"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        devices = Device.objects.all()
        pending = PendingChange.objects.all()
        
        if not user.is_superuser:
            if not user.region:
                devices = devices.none()
                pending = pending.none()
            else:
                devices = devices.filter(user__region=user.region)
                pending = pending.filter(device__user__region=user.region)

        context['devices'] = devices
        context['pending_changes_count'] = pending.filter(is_synced=False).count()
        context['recent_changes'] = pending.order_by('-timestamp')[:20]
        return context
