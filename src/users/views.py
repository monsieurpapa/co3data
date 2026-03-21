# src/users/views.py
# ─────────────────────────────────────────────────────────────────────────────
# CoopData – User management views (Eswatini / SUCOSA II)
# TOR §3.3 – user and access management with customisable permissions and audit trails
# TOR §4   – 2FA for admins and sensitive accounts
# ─────────────────────────────────────────────────────────────────────────────
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView, DetailView, ListView, TemplateView, UpdateView, View,
)

from .forms import UserCreateForm, UserUpdateForm
from .models import AuditLog, User


ADMIN_ROLES = ["system_admin"]


class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.role not in ADMIN_ROLES and not request.user.is_superuser:
                messages.error(request, _("Only administrators can manage users."))
                return redirect("analytics:dashboard")
        return super().dispatch(request, *args, **kwargs)


# ═════════════════════════════════════════════════════════════════════════════
# USER MANAGEMENT (admin only)
# ═════════════════════════════════════════════════════════════════════════════

class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    paginate_by = 25

    def get_queryset(self):
        qs = User.objects.select_related("region").order_by("last_name", "first_name")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q)
                | Q(username__icontains=q) | Q(email__icontains=q)
            )
        role = self.request.GET.get("role")
        if role:
            qs = qs.filter(role=role)
        region = self.request.GET.get("region")
        if region:
            qs = qs.filter(region_id=region)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["role_choices"] = User.USER_ROLES
        from .models import Region
        ctx["regions"] = Region.objects.filter(country_code="SZ").order_by("name")
        return ctx


class UserDetailView(AdminRequiredMixin, DetailView):
    model = User
    template_name = "users/user_detail.html"
    context_object_name = "target_user"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["audit_logs"] = AuditLog.objects.filter(
            user=self.object
        ).order_by("-timestamp")[:20]
        return ctx


class UserCreateView(AdminRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy("users:user_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditLog.objects.create(
            user=self.request.user,
            action=AuditLog.ACTION_CREATE,
            description=f"Created user: {self.object.username} [{self.object.get_role_display()}]",
            content_type_label="User",
            object_id=str(self.object.pk),
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )
        # If role requires 2FA, flag for enrollment
        if self.object.requires_2fa:
            self.object.force_password_change = True
            self.object.save(update_fields=["force_password_change"])
        messages.success(self.request, _("User created successfully."))
        return response


class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy("users:user_list")

    def form_valid(self, form):
        old_role = User.objects.get(pk=self.object.pk).role
        response = super().form_valid(form)
        new_role = self.object.role
        if old_role != new_role:
            AuditLog.objects.create(
                user=self.request.user,
                action=AuditLog.ACTION_ROLE_CHANGE,
                description=f"Role changed: {self.object.username} {old_role} → {new_role}",
                content_type_label="User",
                object_id=str(self.object.pk),
                ip_address=self.request.META.get("REMOTE_ADDR"),
                before_state={"role": old_role},
                after_state={"role": new_role},
            )
        messages.success(self.request, _("User updated successfully."))
        return response


class UserToggleActiveView(AdminRequiredMixin, View):
    """POST: activate or deactivate a user account."""

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        action = _("activated") if user.is_active else _("deactivated")
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.ACTION_UPDATE,
            description=f"User {action}: {user.username}",
            content_type_label="User",
            object_id=str(user.pk),
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        messages.success(request, _(f"User {user.username} {action}."))
        return redirect("users:user_list")


# ═════════════════════════════════════════════════════════════════════════════
# PROFILE (self-service)
# ═════════════════════════════════════════════════════════════════════════════

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["language_choices"] = User.LANGUAGE_CHOICES
        ctx["requires_2fa"] = self.request.user.requires_2fa
        ctx["is_2fa_enrolled"] = self.request.user.is_2fa_enrolled
        return ctx


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ["first_name", "last_name", "email", "phone_number", "preferred_language"]
    template_name = "users/profile_form.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self):
        return self.request.user

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs["class"] = "form-control"
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        # Activate language preference immediately
        lang = self.object.preferred_language
        from django.utils import translation
        translation.activate(lang)
        self.request.session[translation.LANGUAGE_SESSION_KEY] = lang
        messages.success(self.request, _("Profile updated."))
        return response


# ═════════════════════════════════════════════════════════════════════════════
# AUDIT LOG
# ═════════════════════════════════════════════════════════════════════════════

class AuditLogListView(AdminRequiredMixin, ListView):
    model = AuditLog
    template_name = "users/audit_log.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user").order_by("-timestamp")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(user__username__icontains=q)
                | Q(description__icontains=q)
                | Q(content_type_label__icontains=q)
            )
        action = self.request.GET.get("action")
        if action:
            qs = qs.filter(action=action)
        since = self.request.GET.get("since")
        if since:
            qs = qs.filter(timestamp__date__gte=since)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action_choices"] = AuditLog.ACTION_CHOICES
        return ctx