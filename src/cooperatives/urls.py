from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    CooperativeViewSet, MemberViewSet, SACCOFinancialSummaryViewSet,
    LoanAccountViewSet, SavingsAccountViewSet, BoardMemberViewSet,
    TrainingRecordViewSet
)

from . import views

router = DefaultRouter()
router.register(r"cooperatives", CooperativeViewSet)
router.register(r"members", MemberViewSet)
router.register(r"financial-summaries", SACCOFinancialSummaryViewSet)
router.register(r"loans", LoanAccountViewSet)
router.register(r"savings", SavingsAccountViewSet)
router.register(r"board-members", BoardMemberViewSet)
router.register(r"training-records", TrainingRecordViewSet)

app_name = "cooperatives"

urlpatterns = [
    # ── Cooperatives ──────────────────────────────────────────────────────────
    path("", views.CooperativeListView.as_view(), name="cooperative_list"),
    path("new/", views.CooperativeCreateView.as_view(), name="cooperative_create"),
    path("<int:pk>/", views.CooperativeDetailView.as_view(), name="cooperative_detail"),
    path("<int:pk>/edit/", views.CooperativeUpdateView.as_view(), name="cooperative_update"),
    path("<int:pk>/delete/", views.CooperativeDeleteView.as_view(), name="cooperative_delete"),
 
    # ── Members (nested under cooperative) ───────────────────────────────────
    path("<int:cooperative_pk>/members/", views.MemberListView.as_view(), name="member_list"),
    path("<int:cooperative_pk>/members/new/", views.MemberCreateView.as_view(), name="member_create"),
    path("members/", views.MemberListView.as_view(), name="member_list_all"),
    path("members/<int:pk>/", views.MemberDetailView.as_view(), name="member_detail"),
    path("members/<int:pk>/edit/", views.MemberUpdateView.as_view(), name="member_update"),
 
    # ── Financial Summaries ───────────────────────────────────────────────────
    path("<int:cooperative_pk>/financials/", views.FinancialSummaryListView.as_view(), name="financial_summary_list"),
    path("<int:cooperative_pk>/financials/new/", views.FinancialSummaryCreateView.as_view(), name="financial_summary_create"),
    path("financials/", views.FinancialSummaryListView.as_view(), name="financial_summary_list_all"),
    path("financials/<int:pk>/", views.FinancialSummaryDetailView.as_view(), name="financial_summary_detail"),
    path("financials/<int:pk>/verify/", views.FinancialSummaryVerifyView.as_view(), name="financial_summary_verify"),
 
    # ── Board Members ─────────────────────────────────────────────────────────
    path("<int:cooperative_pk>/board/add/", views.BoardMemberCreateView.as_view(), name="board_member_create"),
 
    # ── Training Records ──────────────────────────────────────────────────────
    path("trainings/", views.TrainingRecordListView.as_view(), name="training_list_all"),
    path("<int:cooperative_pk>/trainings/", views.TrainingRecordListView.as_view(), name="training_list"),
    path("<int:cooperative_pk>/trainings/new/", views.TrainingRecordCreateView.as_view(), name="training_create"),
 
    # ── Loans ─────────────────────────────────────────────────────────────────
    path("loans/", views.LoanAccountListView.as_view(), name="loan_list"),
    path("loans/new/", views.LoanAccountCreateView.as_view(), name="loan_create"),
 
    # ── Savings ───────────────────────────────────────────────────────────────
    path("savings/new/", views.SavingsAccountCreateView.as_view(), name="savings_create"),

    path("api/", include(router.urls)),
]
