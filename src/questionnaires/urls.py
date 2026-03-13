from django.urls import path
from . import views

app_name = 'questionnaires'

urlpatterns = [
    path('questionnaire/add/', views.QuestionnaireCreateView.as_view(), name='questionnaire_add'),
    path('list/', views.QuestionnaireListView.as_view(), name='questionnaire_list'),
    path('questionnaire/<uuid:uuid>/', views.QuestionnaireDetailView.as_view(), name='questionnaire_detail'),
    path('questionnaire/<uuid:uuid>/submit/', views.QuestionnaireSubmissionView.as_view(), name='questionnaire_submit'),
    path('submissions/', views.SubmissionListView.as_view(), name='submission_list'),
    path('submissions/<uuid:uuid>/', views.SubmissionDetailView.as_view(), name='submission_detail'),
]
