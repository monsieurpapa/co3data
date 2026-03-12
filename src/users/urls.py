from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('list/', views.UserListView.as_view(), name='user_list'),
]
