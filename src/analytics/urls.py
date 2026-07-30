# src/analytics/urls.py
from django.urls import path
from . import views
 
app_name = "analytics"
 
urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("kpis/", views.KPIListView.as_view(), name="kpi_list"),
    path("alerts/", views.DataQualityAlertListView.as_view(), name="alert_list"),
    path("alerts/<int:pk>/resolve/", views.DataQualityAlertResolveView.as_view(), name="alert_resolve"),
    path("reports/", views.ReportListView.as_view(), name="report_list"),
    path("reports/<int:pk>/run/", views.ReportRunView.as_view(), name="report_run"),
    path("exports/", views.ExportJobListView.as_view(), name="export_job_list"),
    # Chart data endpoints
    path("charts/kpi-trend/", views.SystemKPIChartDataView.as_view(), name="chart_kpi_trend"),
    path("charts/demographics/", views.MemberDemographicsChartView.as_view(), name="chart_demographics"),
]