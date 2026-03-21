# src/sync/urls.py
from django.urls import path
from . import views
 
app_name = "sync"
 
urlpatterns = [
    path("devices/register/", views.DeviceRegisterView.as_view(), name="device_register"),
    path("push/", views.SyncPushView.as_view(), name="sync_push"),
    path("pull/", views.SyncPullView.as_view(), name="sync_pull"),
    path("conflicts/<int:pk>/resolve/", views.SyncConflictResolveView.as_view(), name="conflict_resolve"),
    path("status/", views.SyncStatusView.as_view(), name="sync_status"),
]
 