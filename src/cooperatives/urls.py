from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import CooperativeViewSet, MemberViewSet, FarmViewSet, ProductionRecordViewSet

from . import views

router = DefaultRouter()
router.register(r"cooperatives", CooperativeViewSet)
router.register(r"members", MemberViewSet)
router.register(r"farms", FarmViewSet)
router.register(r"production-records", ProductionRecordViewSet)

app_name = "cooperatives"

urlpatterns = [
    path("list/", views.CooperativeListView.as_view(), name="cooperative_list"),
    path("add/", views.CooperativeCreateView.as_view(), name="cooperative_add"),
    path("<int:pk>/", views.CooperativeDetailView.as_view(), name="cooperative_detail"),
    path("<int:pk>/edit/", views.CooperativeUpdateView.as_view(), name="cooperative_edit"),
    path("<int:pk>/delete/", views.CooperativeDeleteView.as_view(), name="cooperative_delete"),
    path("members/", views.MemberListView.as_view(), name="member_list"),
    path("members/add/", views.MemberCreateView.as_view(), name="member_add"),
    path("members/<int:pk>/", views.MemberDetailView.as_view(), name="member_detail"),
    path("members/<int:pk>/edit/", views.MemberUpdateView.as_view(), name="member_edit"),
    path("members/<int:pk>/delete/", views.MemberDeleteView.as_view(), name="member_delete"),
    path("cherry-deliveries/", views.CherryDeliveryListView.as_view(), name="cherry_delivery_list"),
    path("cherry-deliveries/new/", views.CherryDeliveryCreateView.as_view(), name="cherry_delivery_create"),
    path("cherry-deliveries/<int:pk>/", views.CherryDeliveryDetailView.as_view(), name="cherry_delivery_detail"),
    path("api/", include(router.urls)),
]
