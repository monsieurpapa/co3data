from django.contrib import admin
from .models import Device, PendingChange, SyncLog

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'user', 'last_sync_at', 'is_active')

@admin.register(PendingChange)
class PendingChangeAdmin(admin.ModelAdmin):
    list_display = ('device', 'change_type', 'content_type', 'timestamp', 'is_synced')
    list_filter = ('is_synced', 'change_type')

@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('device', 'sync_start_time', 'sync_end_time', 'status')
    list_filter = ('status',)
