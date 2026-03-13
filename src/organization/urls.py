from django.urls import path
from . import views

app_name = 'organization'

urlpatterns = [
    path('settings/', views.organization_settings, name='organization_settings'),

    # admin management
    path('admin/organizations/', views.organization_list, name='organization_list'),
    path('admin/organizations/add/', views.organization_create, name='organization_add'),
    path('admin/organizations/<uuid:uuid>/edit/', views.organization_update, name='organization_edit'),
    path('admin/organizations/<uuid:uuid>/delete/', views.organization_delete, name='organization_delete'),
]
