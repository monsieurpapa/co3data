# src/users/urls.py
from django.urls import path
from . import views
 
app_name = "users"
 
urlpatterns = [
    path("", views.UserListView.as_view(), name="user_list"),
    path("new/", views.UserCreateView.as_view(), name="user_create"),
    path("<int:pk>/", views.UserDetailView.as_view(), name="user_detail"),
    path("<int:pk>/edit/", views.UserUpdateView.as_view(), name="user_update"),
    path("<int:pk>/toggle-active/", views.UserToggleActiveView.as_view(), name="user_toggle_active"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_update"),
    path("audit-log/", views.AuditLogListView.as_view(), name="audit_log"),
]
 