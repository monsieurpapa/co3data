from django.urls import path
from . import views

app_name = 'questionnaires'

urlpatterns = [
    path('list/', views.QuestionnaireListView.as_view(), name='questionnaire_list'),
    path('<int:pk>/', views.QuestionnaireDetailView.as_view(), name='questionnaire_detail'),
    path('<int:pk>/submit/', views.QuestionnaireSubmissionView.as_view(), name='questionnaire_submit'),
    path('submissions/', views.SubmissionListView.as_view(), name='submission_list'),
    path('submissions/<int:pk>/', views.SubmissionDetailView.as_view(), name='submission_detail'),
]
