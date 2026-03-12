from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import RoleRequiredMixin
from .models import Device, PendingChange


class SyncStatusView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
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
                # Assuming Device and PendingChange should be filtered by user's region
                # Device might not have a region directly, but its user might.
                # However, usually devices belong to users.
                devices = devices.filter(user__region=user.region)
                # PendingChange is generic, so we filter by its user's region if possible
                pending = pending.filter(device__user__region=user.region)

        context['devices'] = devices
        context['pending_changes_count'] = pending.filter(is_synced=False).count()
        context['recent_changes'] = pending.order_by('-timestamp')[:20]
        return context
