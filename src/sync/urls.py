from django.urls import path
from . import views

app_name = 'sync'

urlpatterns = [
    path('status/', views.SyncStatusView.as_view(), name='sync_status'),
]
