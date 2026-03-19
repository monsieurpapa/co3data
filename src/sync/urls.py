from django.urls import path
from . import views

app_name = 'sync'

urlpatterns = [
    path('status/', views.SyncStatusView.as_view(), name='sync_status'),
    path('api/v1/push/', views.SyncPushAPIView.as_view(), name='api_sync_push'),
    path('api/v1/pull/', views.SyncPullAPIView.as_view(), name='api_sync_pull'),
]
