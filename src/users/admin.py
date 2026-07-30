# src/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import AuditLog, Region, User


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "country_code")
    list_filter = ("country_code",)
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "get_full_name", "role", "region", "cooperative", "preferred_language", "is_2fa_enrolled", "is_active")
    list_filter = ("role", "region", "preferred_language", "is_active")
    search_fields = ("username", "first_name", "last_name", "email")
    fieldsets = BaseUserAdmin.fieldsets + (
        (_("CoopData Profile"), {
            "fields": (
                "role", "region", "cooperative", "phone_number", "preferred_language", "profile_picture",
                "is_2fa_enrolled", "last_login_ip", "force_password_change",
            )
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_("CoopData Profile"), {
            "fields": ("role", "region", "cooperative", "phone_number", "preferred_language")
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "description", "ip_address")
    list_filter = ("action",)
    search_fields = ("user__username", "description", "content_type_label")
    date_hierarchy = "timestamp"
    readonly_fields = ("user", "action", "description", "content_type_label",
                       "object_id", "ip_address", "user_agent", "timestamp",
                       "before_state", "after_state")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False  # Audit logs are immutable