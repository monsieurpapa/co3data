from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('list/', views.UserListView.as_view(), name='user_list'),
    path('user/add/', views.UserCreateView.as_view(), name='user_add'),
    path('user/<uuid:uuid>/', views.UserDetailView.as_view(), name='user_detail'),
    path('user/<uuid:uuid>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('user/<uuid:uuid>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
]
