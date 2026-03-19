from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from .models import User, Region
from .forms import UserForm, UserCreationFormCustom, UserProfileForm

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView

class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = "users/profile.html"
    success_url = "/users/profile/"

    def get_object(self):
        return self.request.user

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'user_list'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'admin'

class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'
    
    def test_func(self):
        user = self.get_object()
        return self.request.user.is_superuser or self.request.user.role == 'admin' or self.request.user == user

class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = UserCreationFormCustom
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Créer un nouvel utilisateur")
        return context

class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'
    
    def test_func(self):
        user = self.get_object()
        return self.request.user.is_superuser or self.request.user.role == 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Modifier l'utilisateur")
        return context

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users:user_list')
    slug_field = 'unique_id'
    slug_url_kwarg = 'uuid'
    
    def test_func(self):
        user = self.get_object()
        return (self.request.user.is_superuser or self.request.user.role == 'admin') and self.request.user != user
