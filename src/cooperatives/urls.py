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
    path("<uuid:uuid>/", views.CooperativeDetailView.as_view(), name="cooperative_detail"),
    path("<uuid:uuid>/edit/", views.CooperativeUpdateView.as_view(), name="cooperative_edit"),
    path("<uuid:uuid>/delete/", views.CooperativeDeleteView.as_view(), name="cooperative_delete"),
    path("members/", views.MemberListView.as_view(), name="member_list"),
    path("members/add/", views.MemberCreateView.as_view(), name="member_add"),
    path("members/<uuid:uuid>/", views.MemberDetailView.as_view(), name="member_detail"),
    path("members/<uuid:uuid>/edit/", views.MemberUpdateView.as_view(), name="member_edit"),
    path("members/<uuid:uuid>/delete/", views.MemberDeleteView.as_view(), name="member_delete"),
    path("cherry-deliveries/", views.CherryDeliveryListView.as_view(), name="cherry_delivery_list"),
    path("cherry-deliveries/new/", views.CherryDeliveryCreateView.as_view(), name="cherry_delivery_create"),
    path("cherry-deliveries/<uuid:uuid>/", views.CherryDeliveryDetailView.as_view(), name="cherry_delivery_detail"),
    path("cherry-deliveries/<uuid:uuid>/edit/", views.CherryDeliveryUpdateView.as_view(), name="cherry_delivery_edit"),
    path("cherry-deliveries/<uuid:uuid>/delete/", views.CherryDeliveryDeleteView.as_view(), name="cherry_delivery_delete"),
    path("production-records/", views.ProductionRecordListView.as_view(), name="production_record_list"),
    path("production-records/new/", views.ProductionRecordCreateView.as_view(), name="production_record_add"),
    path("production-records/<uuid:uuid>/", views.ProductionRecordDetailView.as_view(), name="production_record_detail"),
    path("production-records/<uuid:uuid>/edit/", views.ProductionRecordUpdateView.as_view(), name="production_record_edit"),
    path("production-records/<uuid:uuid>/delete/", views.ProductionRecordDeleteView.as_view(), name="production_record_delete"),
    path("financial-records/", views.FinancialRecordListView.as_view(), name="financial_record_list"),
    path("financial-records/new/", views.FinancialRecordCreateView.as_view(), name="financial_record_add"),
    path("financial-records/<uuid:uuid>/", views.FinancialRecordDetailView.as_view(), name="financial_record_detail"),
    path("financial-records/<uuid:uuid>/edit/", views.FinancialRecordUpdateView.as_view(), name="financial_record_edit"),
    path("financial-records/<uuid:uuid>/delete/", views.FinancialRecordDeleteView.as_view(), name="financial_record_delete"),

    # Buyers
    path("buyers/", views.BuyerListView.as_view(), name="buyer_list"),
    path("buyers/add/", views.BuyerCreateView.as_view(), name="buyer_add"),
    path("buyers/<uuid:uuid>/edit/", views.BuyerUpdateView.as_view(), name="buyer_edit"),
    path("buyers/<uuid:uuid>/delete/", views.BuyerDeleteView.as_view(), name="buyer_delete"),

    # Cooperative Certificates
    path("<uuid:uuid>/certificates/", views.CooperativeCertificateListView.as_view(), name="cooperative_certificate_list"),
    path("<uuid:uuid>/certificates/add/", views.CooperativeCertificateCreateView.as_view(), name="cooperative_certificate_add"),
    path("<uuid:uuid>/certificates/<uuid:cert_uuid>/edit/", views.CooperativeCertificateUpdateView.as_view(), name="cooperative_certificate_edit"),
    path("<uuid:uuid>/certificates/<uuid:cert_uuid>/delete/", views.CooperativeCertificateDeleteView.as_view(), name="cooperative_certificate_delete"),

    # Cooperative Sales
    path("<uuid:uuid>/sales/", views.CooperativeSaleListView.as_view(), name="cooperative_sale_list"),
    path("<uuid:uuid>/sales/add/", views.CooperativeSaleCreateView.as_view(), name="cooperative_sale_add"),
    path("<uuid:uuid>/sales/<uuid:sale_uuid>/edit/", views.CooperativeSaleUpdateView.as_view(), name="cooperative_sale_edit"),
    path("<uuid:uuid>/sales/<uuid:sale_uuid>/delete/", views.CooperativeSaleDeleteView.as_view(), name="cooperative_sale_delete"),

    path("api/", include(router.urls)),
]
