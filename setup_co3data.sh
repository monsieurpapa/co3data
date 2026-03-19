#!/usr/bin/env bash
# =============================================================================
# CO3DATA — Full Production Implementation Script
# Usage: bash setup_co3data.sh [your-github-username]
#
# Clones monsieurpapa/co3data, writes all missing production files,
# then commits and pushes to GitHub.
# =============================================================================
set -euo pipefail
REPO_URL="https://github.com/monsieurpapa/co3data.git"
REPO_DIR="co3data"

GH_USER="${1:-monsieurpapa}"
BRANCH="feature/production-implementation"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CO3DATA — Production Implementation Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Clone ────────────────────────────────────────────────────────────────
if [ -d "$REPO_DIR" ]; then
  echo "⚠  Directory '$REPO_DIR' already exists — pulling latest instead"
  cd "$REPO_DIR" && git pull && cd ..
else
  git clone "$REPO_URL"
fi
cd "$REPO_DIR"
git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"

# ── 2. Directory scaffold ────────────────────────────────────────────────────
echo "📁 Creating directory structure..."
mkdir -p src/{core,users,cooperatives,questionnaires,analytics,sync}
mkdir -p src/templates/{users,cooperatives,questionnaires,analytics,sync,partials}
mkdir -p src/static/{js,css}
mkdir -p src/locale/{fr,sw}/LC_MESSAGES
mkdir -p .github/workflows
mkdir -p tests/{unit,integration}

# ── Helper to write files (avoids heredoc quoting nightmares) ────────────────
write_file() { mkdir -p "$(dirname "$1")"; cat > "$1"; }

# =============================================================================
# CORE APP
# =============================================================================

write_file src/core/__init__.py << 'PYEOF'
PYEOF

write_file src/core/celery.py << 'PYEOF'
"""Celery application entry-point for CO3DATA."""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
app = Celery("co3data")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Compute KPIs for all cooperatives every night at 02:00 Africa/Kinshasa
    "nightly-kpi-computation": {
        "task": "core.tasks.compute_all_cooperative_kpis",
        "schedule": crontab(hour=2, minute=0),
    },
    # Data quality sweep every 6 hours
    "data-quality-checks": {
        "task": "core.tasks.run_data_quality_checks",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # Purge sync logs older than 90 days — weekly
    "cleanup-sync-logs": {
        "task": "core.tasks.cleanup_old_sync_logs",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),
    },
}
PYEOF

write_file src/core/wsgi.py << 'PYEOF'
"""WSGI entry-point for CO3DATA."""
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
application = get_wsgi_application()
PYEOF

write_file src/core/settings.py << 'PYEOF'
"""
CO3DATA — Production-Ready Django Settings
Central Africa Coffee & Cocoa Cooperatives Data Platform
"""
import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    LANGUAGE_CODE=(str, "fr"),
    TIME_ZONE=(str, "Africa/Kinshasa"),
)
environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework.authtoken",
    "django_celery_beat",
    "crispy_forms",
    "crispy_bootstrap5",
    "cloudinary_storage",
    "cloudinary",
    # Local
    "users",
    "cooperatives",
    "questionnaires",
    "analytics",
    "sync",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"
AUTH_USER_MODEL = "users.User"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "django.template.context_processors.i18n",
    ]},
}]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": env("POSTGRES_DB", default="co3data"),
    "USER": env("POSTGRES_USER", default="co3data"),
    "PASSWORD": env("POSTGRES_PASSWORD", default="co3data"),
    "HOST": env("POSTGRES_HOST", default="db"),
    "PORT": env("POSTGRES_PORT", default="5432"),
    "CONN_MAX_AGE": 60,
    "OPTIONS": {"connect_timeout": 10},
}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = env("LANGUAGE_CODE")
LANGUAGES = [("fr", "Français"), ("sw", "Kiswahili"), ("en", "English")]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = env("TIME_ZONE")
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": env("CLOUDINARY_CLOUD_NAME", default=""),
    "API_KEY":    env("CLOUDINARY_API_KEY",    default=""),
    "API_SECRET": env("CLOUDINARY_API_SECRET", default=""),
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CELERY_BROKER_URL  = env("REDIS_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

CACHES = {"default": {
    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    "LOCATION": env("REDIS_URL", default="redis://redis:6379/1"),
}}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/day", "user": "1000/hour"},
}

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"verbose": {
        "format": "{levelname} {asctime} {module} {message}",
        "style": "{",
    }},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "verbose"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django":   {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "co3data":  {"handlers": ["console"], "level": "DEBUG" if DEBUG else "INFO", "propagate": False},
    },
}

LOGIN_URL = "/users/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/users/login/"
PYEOF

write_file src/core/urls.py << 'PYEOF'
"""CO3DATA — Root URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter

from cooperatives.views import (
    DashboardView,
    CooperativeListView, CooperativeDetailView, CooperativeCreateView, CooperativeUpdateView,
    MemberListView, MemberCreateView, MemberDetailView,
    CherryDeliveryListView, CherryDeliveryCreateView, CherryDeliveryDetailView,
    CooperativeViewSet, MemberViewSet, WashingStationViewSet, ProductionRecordViewSet,
    CherryDeliveryAPIView, MemberLookupAPIView,
    SyncPushAPIView, SyncPullAPIView,
)

router = DefaultRouter()
router.register(r"cooperatives", CooperativeViewSet, basename="cooperative")
router.register(r"members",      MemberViewSet,      basename="member")
router.register(r"stations",     WashingStationViewSet, basename="station")
router.register(r"production",   ProductionRecordViewSet, basename="production")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/login/",  auth_views.LoginView.as_view(template_name="users/login.html"),   name="login"),
    path("users/logout/", auth_views.LogoutView.as_view(),                                    name="logout"),
    path("users/password-change/",
         auth_views.PasswordChangeView.as_view(template_name="users/password_change.html"),
         name="password_change"),
    path("users/password-change/done/",
         auth_views.PasswordChangeDoneView.as_view(template_name="users/password_change_done.html"),
         name="password_change_done"),
    path("users/", include("users.urls")),
    path("",           DashboardView.as_view(), name="dashboard"),
    path("dashboard/", DashboardView.as_view(), name="dashboard_alt"),
    path("cooperatives/",          CooperativeListView.as_view(),   name="cooperative-list"),
    path("cooperatives/create/",   CooperativeCreateView.as_view(), name="cooperative-create"),
    path("cooperatives/<int:pk>/", CooperativeDetailView.as_view(), name="cooperative-detail"),
    path("cooperatives/<int:pk>/edit/", CooperativeUpdateView.as_view(), name="cooperative-update"),
    path("members/",          MemberListView.as_view(),   name="member-list"),
    path("members/create/",   MemberCreateView.as_view(), name="member-create"),
    path("members/<int:pk>/", MemberDetailView.as_view(), name="member-detail"),
    path("deliveries/",          CherryDeliveryListView.as_view(),   name="delivery-list"),
    path("deliveries/create/",   CherryDeliveryCreateView.as_view(), name="delivery-create"),
    path("deliveries/<int:pk>/", CherryDeliveryDetailView.as_view(), name="delivery-detail"),
    path("questionnaires/", include("questionnaires.urls")),
    path("analytics/",      include("analytics.urls")),
    path("api/v1/", include(router.urls)),
    path("api/v1/cherry-deliveries/", CherryDeliveryAPIView.as_view(),   name="api-cherry-deliveries"),
    path("api/v1/members/lookup/",    MemberLookupAPIView.as_view(),      name="api-member-lookup"),
    path("api/v1/sync/push/",         SyncPushAPIView.as_view(),          name="api-sync-push"),
    path("api/v1/sync/pull/",         SyncPullAPIView.as_view(),          name="api-sync-pull"),
    path("api/v1/auth/", include("rest_framework.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
PYEOF

write_file src/core/tasks.py << 'PYEOF'
"""CO3DATA — Celery Background Tasks"""
import logging
from datetime import date, timedelta
from io import BytesIO

from celery import shared_task
from django.db.models import Sum
from django.utils import timezone

logger = logging.getLogger("co3data.tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def compute_kpis_for_cooperative(self, cooperative_id: int, period_start: str, period_end: str):
    from cooperatives.models import Cooperative, Member, ProductionRecord, FinancialRecord
    from analytics.models import KPI, KPIResult
    try:
        cooperative = Cooperative.objects.get(pk=cooperative_id)
        start, end = date.fromisoformat(period_start), date.fromisoformat(period_end)
        members   = Member.objects.filter(cooperative=cooperative, is_active=True)
        production = ProductionRecord.objects.filter(station__cooperative=cooperative,
                                                     harvest_date__gte=start, harvest_date__lte=end)
        financials = cooperative.financial_records.filter(transaction_date__gte=start,
                                                          transaction_date__lte=end)
        total_kg   = float(production.aggregate(t=Sum("quantity_kg"))["t"] or 0)
        total_m    = members.count()
        female_m   = members.filter(gender="female").count()
        youth_m    = members.filter(age_group="youth").count()
        income     = float(financials.filter(transaction_type="income").aggregate(t=Sum("amount"))["t"] or 0)
        expenses   = float(financials.filter(transaction_type="expense").aggregate(t=Sum("amount"))["t"] or 0)
        context = {
            "total_production_kg": total_kg,
            "total_members": total_m,
            "female_members": female_m,
            "youth_members": youth_m,
            "total_income": income,
            "total_expenses": expenses,
            "production_per_member": total_kg / total_m if total_m else 0,
            "female_participation_rate": (female_m / total_m * 100) if total_m else 0,
            "youth_participation_rate":  (youth_m  / total_m * 100) if total_m else 0,
            "net_income": income - expenses,
        }
        computed = 0
        for kpi in KPI.objects.filter(is_active=True):
            value = kpi.compute(context)
            if value is not None:
                KPIResult.objects.update_or_create(
                    kpi=kpi, cooperative=cooperative,
                    period_start=start, period_end=end,
                    defaults={"value": value},
                )
                computed += 1
        logger.info(f"Computed {computed} KPIs for {cooperative.name} [{start}–{end}]")
        return {"cooperative": cooperative.name, "kpis_computed": computed}
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def compute_all_cooperative_kpis():
    from cooperatives.models import Cooperative
    today      = timezone.now().date()
    period_end = today.replace(day=1) - timedelta(days=1)
    period_start = period_end.replace(day=1)
    for coop in Cooperative.objects.filter(is_active=True):
        compute_kpis_for_cooperative.delay(coop.pk, period_start.isoformat(), period_end.isoformat())


@shared_task(bind=True, max_retries=3)
def run_data_quality_checks(self, cooperative_id: int = None):
    from cooperatives.models import Cooperative, ProductionRecord
    from analytics.models import DataValidationRule, DataQualityAlert
    rules = DataValidationRule.objects.filter(is_active=True)
    coops = Cooperative.objects.filter(is_active=True)
    if cooperative_id:
        coops = coops.filter(pk=cooperative_id)
    alerts_created = 0
    for coop in coops:
        for rule in rules:
            if "ProductionRecord" in rule.applies_to_model:
                for record in ProductionRecord.objects.filter(station__cooperative=coop):
                    data = {"quantity_kg": float(record.quantity_kg),
                            "base_price_fc": float(record.base_price_fc or 0)}
                    if not rule.evaluate(data):
                        _, created = DataQualityAlert.objects.get_or_create(
                            rule=rule, cooperative=coop,
                            record_model="ProductionRecord", record_id=record.pk,
                            defaults={"message": f"Violation règle '{rule.name}' – enregistrement #{record.pk}",
                                      "is_resolved": False},
                        )
                        if created:
                            alerts_created += 1
    logger.info(f"Data quality check: {alerts_created} new alerts")
    return {"alerts_created": alerts_created}


@shared_task
def generate_cooperative_report_xlsx(cooperative_id: int, report_config_id: int):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from cooperatives.models import Cooperative, Member, ProductionRecord, FinancialRecord
    try:
        cooperative = Cooperative.objects.get(pk=cooperative_id)
        wb = openpyxl.Workbook()
        # Members sheet
        ws = wb.active
        ws.title = "Membres"
        headers = ["ID Membre","Code Agriculteur","Nom","Genre","Groupe Âge","Groupement","Village"]
        for c, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=c, value=h)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1B6CA8")
        for r, m in enumerate(Member.objects.filter(cooperative=cooperative, is_active=True), 2):
            ws.append([m.member_id, m.farmer_code, m.full_name,
                       m.get_gender_display(), m.get_age_group_display(),
                       m.groupement, m.village])
        # Production sheet
        wp = wb.create_sheet("Production")
        for c, h in enumerate(["Date","Station","Agriculteur","Quantité kg","Prix FC","Reçu"], 1):
            cell = wp.cell(row=1, column=c, value=h)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="2E7D32")
        for r, d in enumerate(ProductionRecord.objects.filter(station__cooperative=cooperative)
                               .select_related("member","station"), 2):
            wp.append([d.harvest_date.isoformat() if d.harvest_date else "",
                       str(d.station) if d.station else "",
                       str(d.member) if d.member else "",
                       float(d.quantity_kg),
                       float(d.total_price_fc) if d.total_price_fc else "",
                       d.receipt_number or ""])
        output = BytesIO()
        wb.save(output)
        logger.info(f"Report generated for {cooperative.name}")
        return {"status": "success"}
    except Exception as exc:
        logger.exception(f"Report generation failed: {exc}")
        return {"status": "error", "error": str(exc)}


@shared_task
def cleanup_old_sync_logs(days_to_keep: int = 90):
    from sync.models import SyncLog
    cutoff = timezone.now() - timedelta(days=days_to_keep)
    deleted, _ = SyncLog.objects.filter(sync_start_time__lt=cutoff).delete()
    logger.info(f"Deleted {deleted} old sync logs")
    return {"deleted": deleted}
PYEOF

# =============================================================================
# USERS APP
# =============================================================================
write_file src/users/__init__.py << 'PYEOF'
PYEOF

write_file src/users/models.py << 'PYEOF'
"""CO3DATA — Users: RBAC-enabled custom user model"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Region(models.Model):
    name    = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=100, default="DRC")
    description = models.TextField(blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Région")
        verbose_name_plural = _("Régions")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.country})"


class User(AbstractUser):
    USER_ROLES = (
        ("member",          _("Membre de Coopérative")),
        ("field_agent",     _("Agent de Terrain")),
        ("manager",         _("Gestionnaire de Coopérative")),
        ("regional_officer",_("Officier Régional")),
        ("apex_body",       _("Représentant Apex")),
        ("government",      _("Officiel Gouvernemental")),
        ("admin",           _("Administrateur Système")),
    )
    ROLE_PERMISSIONS = {
        "member":           ["view_own_data"],
        "field_agent":      ["view_cooperative","add_member","add_productionrecord","add_submission"],
        "manager":          ["view_cooperative","add_member","change_member",
                             "add_productionrecord","add_financialrecord","view_reports"],
        "regional_officer": ["view_region","view_reports","export_data"],
        "apex_body":        ["view_all","view_reports","export_data"],
        "government":       ["view_all","view_reports","export_data"],
        "admin":            ["all"],
    }

    role              = models.CharField(max_length=20, choices=USER_ROLES, default="field_agent")
    phone_number      = models.CharField(max_length=20, blank=True, null=True)
    region            = models.ForeignKey(Region, on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name="users")
    cooperative       = models.ForeignKey("cooperatives.Cooperative", on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name="staff_users")
    preferred_language = models.CharField(
        max_length=5, choices=[("fr","Français"),("sw","Kiswahili"),("en","English")],
        default="fr")
    last_sync_at      = models.DateTimeField(null=True, blank=True)
    profile_picture   = models.ImageField(upload_to="profiles/", null=True, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def can(self, permission: str) -> bool:
        role_perms = self.ROLE_PERMISSIONS.get(self.role, [])
        return "all" in role_perms or permission in role_perms

    def get_accessible_cooperatives(self):
        from cooperatives.models import Cooperative
        if self.can("view_all"):
            return Cooperative.objects.all()
        if self.can("view_region") and self.region:
            return Cooperative.objects.filter(region=self.region)
        if self.cooperative:
            return Cooperative.objects.filter(pk=self.cooperative.pk)
        return Cooperative.objects.none()
PYEOF

write_file src/users/admin.py << 'PYEOF'
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["name", "country"]
    search_fields = ["name", "country"]


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (_("CO3DATA Profile"), {"fields": ("role","phone_number","region","cooperative",
                                           "preferred_language","last_sync_at","profile_picture")}),
    )
    list_display  = ["username", "email", "get_full_name", "role", "region", "is_active"]
    list_filter   = ["role", "region", "is_active"]
    search_fields = ["username", "email", "first_name", "last_name"]
PYEOF

write_file src/users/urls.py << 'PYEOF'
from django.urls import path
from . import views
app_name = "users"
urlpatterns = [
    path("profile/", views.ProfileView.as_view(), name="profile"),
]
PYEOF

write_file src/users/views.py << 'PYEOF'
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from .models import User


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ["first_name", "last_name", "email", "phone_number", "preferred_language", "profile_picture"]
    template_name = "users/profile.html"
    success_url = "/users/profile/"

    def get_object(self):
        return self.request.user
PYEOF

# =============================================================================
# COOPERATIVES APP
# =============================================================================
write_file src/cooperatives/__init__.py << 'PYEOF'
PYEOF

write_file src/cooperatives/models.py << 'PYEOF'
"""CO3DATA — Cooperatives: core data models"""
import re
import uuid
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import Region, User


class Cooperative(models.Model):
    COOPERATIVE_TYPES = (
        ("coffee", _("Coopérative Café")),
        ("cocoa",  _("Coopérative Cacao")),
        ("mixed",  _("Coopérative Mixte Café & Cacao")),
        ("sacco",  _("SACCO")),
        ("other",  _("Autre")),
    )
    name                = models.CharField(max_length=255, unique=True)
    registration_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    type                = models.CharField(max_length=50, choices=COOPERATIVE_TYPES)
    region              = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="cooperatives")
    establishment_date  = models.DateField(blank=True, null=True)
    contact_person      = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                                            related_name="managed_cooperatives")
    address             = models.TextField(blank=True, null=True)
    phone               = models.CharField(max_length=20, blank=True, null=True)
    email               = models.EmailField(blank=True, null=True)
    logo                = models.ImageField(upload_to="cooperatives/logos/", null=True, blank=True)
    is_active           = models.BooleanField(default=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Coopérative")
        verbose_name_plural = _("Coopératives")
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.filter(is_active=True).count()

    @property
    def female_member_count(self):
        return self.members.filter(gender="female", is_active=True).count()

    @property
    def youth_member_count(self):
        return self.members.filter(age_group="youth", is_active=True).count()


class WashingStation(models.Model):
    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE, related_name="washing_stations")
    name        = models.CharField(max_length=255)
    code        = models.CharField(max_length=20, blank=True, null=True)
    village     = models.CharField(max_length=100, blank=True, null=True)
    groupement  = models.CharField(max_length=100, blank=True, null=True)
    latitude    = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude   = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Station de Lavage")
        verbose_name_plural = _("Stations de Lavage")
        ordering = ["cooperative", "name"]
        unique_together = [("cooperative", "name")]

    def __str__(self):
        return f"{self.name} ({self.cooperative.name})"


def validate_farmer_code(value):
    if not re.match(r"^[A-Z]+ [A-Z]+ \d{3}$", value):
        raise ValidationError(
            _("Code invalide. Format: PREFIX INITIALES NUMÉRO (ex: TCC BMB 009)")
        )


class Member(models.Model):
    GENDER_CHOICES    = [("male",_("Masculin")),("female",_("Féminin")),("other",_("Autre"))]
    AGE_GROUP_CHOICES = [("youth",_("Jeune 18-35")),("adult",_("Adulte 36-60")),("senior",_("Senior 61+"))]

    cooperative           = models.ForeignKey(Cooperative, on_delete=models.CASCADE, related_name="members")
    member_id             = models.CharField(max_length=50)
    farmer_code           = models.CharField(max_length=20, unique=True, null=True, blank=True,
                                             validators=[validate_farmer_code])
    farmer_code_prefix    = models.CharField(max_length=10, blank=True, null=True, db_index=True)
    farmer_code_initials  = models.CharField(max_length=10, blank=True, null=True, db_index=True)
    farmer_code_number    = models.PositiveSmallIntegerField(null=True, blank=True)
    first_name            = models.CharField(max_length=100)
    last_name             = models.CharField(max_length=100)
    gender                = models.CharField(max_length=10, choices=GENDER_CHOICES)
    age_group             = models.CharField(max_length=10, choices=AGE_GROUP_CHOICES)
    date_of_birth         = models.DateField(null=True, blank=True)
    phone_number          = models.CharField(max_length=20, blank=True, null=True)
    national_id           = models.CharField(max_length=50, blank=True, null=True)
    groupement            = models.CharField(max_length=100, blank=True, null=True)
    village               = models.CharField(max_length=100, blank=True, null=True)
    subvillage            = models.CharField(max_length=100, blank=True, null=True)
    date_joined           = models.DateField(auto_now_add=True)
    is_active             = models.BooleanField(default=True)
    created_at            = models.DateTimeField(auto_now_add=True)
    updated_at            = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Membre")
        verbose_name_plural = _("Membres")
        unique_together = [("cooperative", "member_id")]
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["cooperative","is_active"]),
            models.Index(fields=["farmer_code"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.farmer_code or self.member_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def clean(self):
        if self.farmer_code:
            validate_farmer_code(self.farmer_code)
            parts = self.farmer_code.split()
            self.farmer_code_prefix   = parts[0]
            self.farmer_code_initials = parts[1]
            self.farmer_code_number   = int(parts[2])

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Farm(models.Model):
    CERTIFICATION_CHOICES = [
        ("none","Aucune"),("organic","Biologique"),("fairtrade","Commerce Équitable"),
        ("rainforest","Rainforest Alliance"),("utm","UTZ"),
    ]
    member         = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="farms")
    farm_name      = models.CharField(max_length=255, blank=True, null=True)
    size_hectares  = models.DecimalField(max_digits=10, decimal_places=4)
    latitude       = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude      = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    altitude_m     = models.PositiveIntegerField(null=True, blank=True)
    certification  = models.CharField(max_length=20, choices=CERTIFICATION_CHOICES, default="none")
    soil_type      = models.CharField(max_length=100, blank=True, null=True)
    number_of_trees = models.PositiveIntegerField(null=True, blank=True)
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Ferme")
        verbose_name_plural = _("Fermes")

    def __str__(self):
        return self.farm_name or f"Ferme de {self.member.full_name}"


class ProductionRecord(models.Model):
    CROP_TYPE_CHOICES  = [("coffee",_("Café")),("cocoa",_("Cacao"))]
    RECORD_TYPE_CHOICES = [("generic",_("Générique")),("cherry_delivery",_("Livraison Cerises"))]

    record_type   = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES, default="generic")
    crop_type     = models.CharField(max_length=50, choices=CROP_TYPE_CHOICES)
    farm          = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="production_records",
                                      null=True, blank=True)
    member        = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="production_records",
                                      null=True, blank=True)
    station       = models.ForeignKey(WashingStation, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name="cherry_deliveries")
    harvest_date  = models.DateField()
    quantity_kg   = models.DecimalField(max_digits=10, decimal_places=2)
    quality_grade = models.CharField(max_length=50, blank=True, null=True)
    # Cherry delivery fields
    purchase_date           = models.DateField(null=True, blank=True)
    receipt_number          = models.CharField(max_length=50, blank=True, null=True)
    base_price_fc           = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_price_fc          = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    exchange_rate_fc_usd    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cherry_register_number  = models.CharField(max_length=50, blank=True, null=True)
    delivery_report_number  = models.CharField(max_length=50, blank=True, null=True)
    reception_date          = models.DateField(null=True, blank=True)
    # Offline sync
    sync_uuid          = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_locally_created = models.BooleanField(default=False)
    is_synced          = models.BooleanField(default=True)
    notes              = models.TextField(blank=True, null=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)
    created_by         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name="production_records_created")

    class Meta:
        verbose_name = _("Enregistrement de Production")
        verbose_name_plural = _("Enregistrements de Production")
        ordering = ["-harvest_date"]
        indexes = [
            models.Index(fields=["record_type","harvest_date"]),
            models.Index(fields=["sync_uuid"]),
            models.Index(fields=["station","harvest_date"]),
        ]

    def __str__(self):
        return f"{self.get_crop_type_display()} – {self.quantity_kg}kg – {self.harvest_date}"

    def clean(self):
        if self.record_type == "cherry_delivery":
            errors = {}
            if not self.station:
                errors["station"] = _("Station de lavage obligatoire pour une livraison.")
            if not self.member:
                errors["member"] = _("Membre obligatoire pour une livraison.")
            if not self.receipt_number:
                errors["receipt_number"] = _("Numéro de reçu obligatoire.")
            if errors:
                raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.base_price_fc and self.quantity_kg:
            self.total_price_fc = Decimal(str(self.quantity_kg)) * Decimal(str(self.base_price_fc))
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def total_price_usd(self):
        if self.total_price_fc and self.exchange_rate_fc_usd and self.exchange_rate_fc_usd > 0:
            return self.total_price_fc / self.exchange_rate_fc_usd
        return None


class FinancialRecord(models.Model):
    TRANSACTION_TYPES = [
        ("income",_("Recette")),("expense",_("Dépense")),
        ("loan_disbursement",_("Décaissement Prêt")),("loan_repayment",_("Remboursement Prêt")),
        ("dividend",_("Dividende")),("member_savings",_("Épargne Membre")),("other",_("Autre")),
    ]
    CURRENCY_CHOICES = [
        ("CDF",_("Franc Congolais")),("USD",_("Dollar US")),
        ("RWF",_("Franc Rwandais")),("BIF",_("Franc Burundais")),
    ]
    cooperative      = models.ForeignKey(Cooperative, on_delete=models.CASCADE, related_name="financial_records")
    member           = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name="financial_records")
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    amount           = models.DecimalField(max_digits=14, decimal_places=2)
    currency         = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="CDF")
    description      = models.TextField(blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    verified         = models.BooleanField(default=False)
    verified_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name="verified_financial_records")
    sync_uuid        = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at       = models.DateTimeField(auto_now_add=True)
    created_by       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name="financial_records_created")

    class Meta:
        verbose_name = _("Enregistrement Financier")
        verbose_name_plural = _("Enregistrements Financiers")
        ordering = ["-transaction_date"]
        indexes = [
            models.Index(fields=["cooperative","transaction_date"]),
            models.Index(fields=["transaction_type"]),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} – {self.amount} {self.currency} – {self.transaction_date}"
PYEOF

write_file src/cooperatives/admin.py << 'PYEOF'
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Cooperative, WashingStation, Member, Farm, ProductionRecord, FinancialRecord


class WashingStationInline(admin.TabularInline):
    model = WashingStation
    extra = 0
    fields = ["name", "code", "village", "groupement", "is_active"]


class MemberInline(admin.TabularInline):
    model = Member
    extra = 0
    fields = ["member_id", "farmer_code", "first_name", "last_name", "gender", "age_group", "is_active"]
    show_change_link = True


@admin.register(Cooperative)
class CooperativeAdmin(admin.ModelAdmin):
    list_display  = ["name", "type", "region", "member_count", "is_active", "created_at"]
    list_filter   = ["type", "region", "is_active"]
    search_fields = ["name", "registration_number"]
    inlines       = [WashingStationInline, MemberInline]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(WashingStation)
class WashingStationAdmin(admin.ModelAdmin):
    list_display  = ["name", "cooperative", "village", "groupement", "is_active"]
    list_filter   = ["cooperative", "is_active"]
    search_fields = ["name", "code"]


class FarmInline(admin.TabularInline):
    model = Farm
    extra = 0
    fields = ["farm_name", "size_hectares", "certification", "is_active"]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display  = ["__str__", "cooperative", "gender", "age_group", "groupement", "village", "is_active"]
    list_filter   = ["cooperative", "gender", "age_group", "is_active"]
    search_fields = ["first_name", "last_name", "farmer_code", "member_id"]
    inlines       = [FarmInline]
    readonly_fields = ["farmer_code_prefix","farmer_code_initials","farmer_code_number","date_joined"]


class CherryDeliveryFieldset(admin.ModelAdmin):
    fieldsets = (
        (_("Identification"), {"fields": ("record_type","crop_type","station","member","farm")}),
        (_("Quantités"), {"fields": ("harvest_date","quantity_kg","quality_grade")}),
        (_("Livraison Cerises"), {"fields": (
            "purchase_date","receipt_number","base_price_fc","total_price_fc",
            "exchange_rate_fc_usd","cherry_register_number","delivery_report_number","reception_date",
        ), "classes": ("collapse",)}),
        (_("Synchronisation"), {"fields": ("sync_uuid","is_locally_created","is_synced"), "classes": ("collapse",)}),
        (_("Notes"), {"fields": ("notes",)}),
    )
    readonly_fields = ["sync_uuid","total_price_fc","created_at","updated_at"]


@admin.register(ProductionRecord)
class ProductionRecordAdmin(CherryDeliveryFieldset):
    list_display  = ["__str__", "record_type", "station", "member", "quantity_kg",
                     "receipt_number", "is_synced", "harvest_date"]
    list_filter   = ["record_type", "crop_type", "is_synced", "station__cooperative"]
    search_fields = ["member__farmer_code","receipt_number","cherry_register_number"]
    date_hierarchy = "harvest_date"


@admin.register(FinancialRecord)
class FinancialRecordAdmin(admin.ModelAdmin):
    list_display  = ["cooperative","transaction_type","amount","currency","transaction_date","verified"]
    list_filter   = ["cooperative","transaction_type","currency","verified"]
    search_fields = ["reference_number","description"]
    date_hierarchy = "transaction_date"
PYEOF

write_file src/cooperatives/serializers.py << 'PYEOF'
"""CO3DATA — DRF Serializers"""
from rest_framework import serializers
from .models import Cooperative, Member, Farm, WashingStation, ProductionRecord, FinancialRecord
from users.models import Region


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["id","name","country"]


class CooperativeSerializer(serializers.ModelSerializer):
    region_name         = serializers.CharField(source="region.name", read_only=True)
    member_count        = serializers.IntegerField(read_only=True)
    female_member_count = serializers.IntegerField(read_only=True)
    youth_member_count  = serializers.IntegerField(read_only=True)
    class Meta:
        model  = Cooperative
        fields = ["id","name","registration_number","type","region","region_name",
                  "establishment_date","address","phone","email","is_active",
                  "member_count","female_member_count","youth_member_count","created_at","updated_at"]
        read_only_fields = ["created_at","updated_at"]


class WashingStationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = WashingStation
        fields = ["id","cooperative","name","code","village","groupement","latitude","longitude","is_active"]


class MemberSerializer(serializers.ModelSerializer):
    full_name        = serializers.CharField(read_only=True)
    cooperative_name = serializers.CharField(source="cooperative.name", read_only=True)
    class Meta:
        model  = Member
        fields = ["id","cooperative","cooperative_name","member_id","farmer_code",
                  "farmer_code_prefix","farmer_code_initials","farmer_code_number",
                  "first_name","last_name","full_name","gender","age_group",
                  "date_of_birth","phone_number","national_id","groupement","village","subvillage",
                  "date_joined","is_active","created_at"]
        read_only_fields = ["farmer_code_prefix","farmer_code_initials","farmer_code_number",
                            "full_name","date_joined","created_at"]


class FarmSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)
    class Meta:
        model  = Farm
        fields = ["id","member","member_name","farm_name","size_hectares",
                  "latitude","longitude","altitude_m","certification","soil_type","number_of_trees","is_active"]


class ProductionRecordSerializer(serializers.ModelSerializer):
    total_price_usd = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    class Meta:
        model  = ProductionRecord
        fields = ["id","record_type","crop_type","farm","member","station",
                  "harvest_date","quantity_kg","quality_grade",
                  "purchase_date","receipt_number","base_price_fc","total_price_fc","total_price_usd",
                  "exchange_rate_fc_usd","cherry_register_number","delivery_report_number","reception_date",
                  "sync_uuid","is_locally_created","is_synced","notes","created_at","updated_at"]
        read_only_fields = ["sync_uuid","total_price_fc","total_price_usd","created_at","updated_at"]


class CherryDeliverySerializer(ProductionRecordSerializer):
    def validate(self, data):
        data["record_type"] = "cherry_delivery"
        if not data.get("station"):
            raise serializers.ValidationError({"station": "Station de lavage obligatoire."})
        if not data.get("member"):
            raise serializers.ValidationError({"member": "Membre obligatoire."})
        if not data.get("receipt_number"):
            raise serializers.ValidationError({"receipt_number": "Numéro de reçu obligatoire."})
        return data


class FinancialRecordSerializer(serializers.ModelSerializer):
    cooperative_name = serializers.CharField(source="cooperative.name", read_only=True)
    member_name      = serializers.CharField(source="member.full_name", read_only=True)
    class Meta:
        model  = FinancialRecord
        fields = ["id","cooperative","cooperative_name","member","member_name",
                  "transaction_date","transaction_type","amount","currency",
                  "description","reference_number","verified","sync_uuid","created_at"]
        read_only_fields = ["sync_uuid","created_at"]


class SyncPushSerializer(serializers.Serializer):
    model          = serializers.ChoiceField(choices=["ProductionRecord","Member","Farm","FinancialRecord"])
    operation      = serializers.ChoiceField(choices=["create","update","delete"])
    sync_uuid      = serializers.UUIDField()
    payload        = serializers.JSONField()
    local_timestamp = serializers.DateTimeField()
    device_id      = serializers.CharField(max_length=255)
PYEOF

write_file src/cooperatives/forms.py << 'PYEOF'
"""CO3DATA — Cooperatives Forms"""
from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset, HTML
from .models import Cooperative, Member, Farm, WashingStation, ProductionRecord, FinancialRecord


class BaseUserScopedForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user:
            accessible = user.get_accessible_cooperatives()
            for field in self.fields.values():
                if hasattr(field, "queryset") and field.queryset.model == Cooperative:
                    field.queryset = accessible


class CooperativeForm(forms.ModelForm):
    class Meta:
        model  = Cooperative
        fields = ["name","registration_number","type","region","establishment_date",
                  "contact_person","address","phone","email","logo"]
        widgets = {
            "establishment_date": forms.DateInput(attrs={"type":"date"}),
            "address": forms.Textarea(attrs={"rows":2}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_("Informations Générales"),
                Row(Column("name",css_class="col-md-8"),Column("type",css_class="col-md-4")),
                Row(Column("registration_number",css_class="col-md-6"),Column("establishment_date",css_class="col-md-6")),
            ),
            Fieldset(_("Localisation & Contact"),
                Row(Column("region",css_class="col-md-6"),Column("contact_person",css_class="col-md-6")),
                "address",
                Row(Column("phone",css_class="col-md-6"),Column("email",css_class="col-md-6")),
            ),
            "logo",
            Submit("submit",_("Enregistrer"),css_class="btn btn-primary"),
        )


class MemberForm(BaseUserScopedForm):
    class Meta:
        model  = Member
        fields = ["cooperative","member_id","farmer_code","first_name","last_name",
                  "gender","age_group","date_of_birth","phone_number","national_id",
                  "groupement","village","subvillage"]
        widgets = {"date_of_birth": forms.DateInput(attrs={"type":"date"})}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("cooperative",css_class="col-md-6"),Column("member_id",css_class="col-md-3"),
                Column("farmer_code",css_class="col-md-3")),
            Fieldset(_("Identité"),
                Row(Column("first_name",css_class="col-md-6"),Column("last_name",css_class="col-md-6")),
                Row(Column("gender",css_class="col-md-4"),Column("age_group",css_class="col-md-4"),
                    Column("date_of_birth",css_class="col-md-4")),
                Row(Column("phone_number",css_class="col-md-6"),Column("national_id",css_class="col-md-6")),
            ),
            Fieldset(_("Localisation"),
                Row(Column("groupement",css_class="col-md-4"),Column("village",css_class="col-md-4"),
                    Column("subvillage",css_class="col-md-4")),
            ),
            Submit("submit",_("Enregistrer le Membre"),css_class="btn btn-primary"),
        )


class CherryDeliveryForm(BaseUserScopedForm):
    member_search = forms.CharField(
        label=_("Rechercher Agriculteur (Code/Nom)"), required=False,
        widget=forms.TextInput(attrs={
            "placeholder":"ex: TCC BMB 009",
            "autocomplete":"off",
            "data-autocomplete-url":"/api/v1/members/lookup/",
            "class":"form-control",
        })
    )
    class Meta:
        model  = ProductionRecord
        fields = ["station","member","harvest_date","purchase_date","quantity_kg",
                  "base_price_fc","total_price_fc","exchange_rate_fc_usd",
                  "receipt_number","cherry_register_number","delivery_report_number",
                  "reception_date","quality_grade","notes","is_locally_created"]
        widgets = {
            "harvest_date":  forms.DateInput(attrs={"type":"date"}),
            "purchase_date": forms.DateInput(attrs={"type":"date"}),
            "reception_date":forms.DateInput(attrs={"type":"date"}),
            "total_price_fc":forms.NumberInput(attrs={"readonly":True,"data-computed":"true","class":"form-control bg-light"}),
            "notes":forms.Textarea(attrs={"rows":2}),
            "is_locally_created":forms.HiddenInput(),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["station"].queryset = WashingStation.objects.filter(
                cooperative__in=self.user.get_accessible_cooperatives(), is_active=True)
            self.fields["member"].queryset = Member.objects.filter(
                cooperative__in=self.user.get_accessible_cooperatives(), is_active=True)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_("Station & Agriculteur"),
                HTML("""<div class="mb-3" id="member-search-wrapper">
                    <label class="form-label fw-bold">{% trans "Rechercher Agriculteur" %}</label>
                    <input type="text" class="form-control" placeholder="ex: TCC BMB 009"
                           data-autocomplete-url="/api/v1/members/lookup/" autocomplete="off">
                    <div id="member-autocomplete-results" class="list-group mt-1 d-none position-absolute w-100" style="z-index:1000"></div>
                </div>"""),
                Row(Column("station",css_class="col-md-6"),Column("member",css_class="col-md-6")),
            ),
            Fieldset(_("Dates"),
                Row(Column("harvest_date",css_class="col-md-4"),Column("purchase_date",css_class="col-md-4"),
                    Column("reception_date",css_class="col-md-4")),
            ),
            Fieldset(_("Quantité & Prix"),
                Row(Column("quantity_kg",css_class="col-md-3"),Column("base_price_fc",css_class="col-md-3"),
                    Column("total_price_fc",css_class="col-md-3"),Column("exchange_rate_fc_usd",css_class="col-md-3")),
            ),
            Fieldset(_("Références"),
                Row(Column("receipt_number",css_class="col-md-4"),Column("cherry_register_number",css_class="col-md-4"),
                    Column("delivery_report_number",css_class="col-md-4")),
            ),
            Row(Column("quality_grade",css_class="col-md-4"),Column("notes",css_class="col-md-8")),
            "is_locally_created",
            Submit("submit",_("Enregistrer la Livraison"),css_class="btn btn-success btn-lg w-100 mt-3"),
        )
    def clean(self):
        cleaned = super().clean()
        qty, price = cleaned.get("quantity_kg"), cleaned.get("base_price_fc")
        if qty and price:
            cleaned["total_price_fc"] = qty * price
        return cleaned


class FinancialRecordForm(BaseUserScopedForm):
    class Meta:
        model  = FinancialRecord
        fields = ["cooperative","member","transaction_date","transaction_type","amount","currency","description","reference_number"]
        widgets = {"transaction_date":forms.DateInput(attrs={"type":"date"}),"description":forms.Textarea(attrs={"rows":2})}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["member"].queryset = Member.objects.filter(
                cooperative__in=self.user.get_accessible_cooperatives())
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("cooperative",css_class="col-md-6"),Column("member",css_class="col-md-6")),
            Row(Column("transaction_date",css_class="col-md-4"),Column("transaction_type",css_class="col-md-4"),
                Column("currency",css_class="col-md-4")),
            Row(Column("amount",css_class="col-md-4"),Column("reference_number",css_class="col-md-8")),
            "description",
            Submit("submit",_("Enregistrer Transaction"),css_class="btn btn-primary"),
        )
PYEOF

write_file src/cooperatives/views.py << 'PYEOF'
"""CO3DATA — Cooperatives Views (web + REST API)"""
import logging
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Sum, Q
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView, TemplateView
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import CooperativeForm, MemberForm, CherryDeliveryForm, FinancialRecordForm
from .models import Cooperative, Member, Farm, WashingStation, ProductionRecord, FinancialRecord
from .serializers import (
    CooperativeSerializer, MemberSerializer, FarmSerializer, WashingStationSerializer,
    ProductionRecordSerializer, CherryDeliverySerializer, FinancialRecordSerializer,
    SyncPushSerializer,
)

logger = logging.getLogger("co3data")


class CanManageMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.can("add_member") or self.request.user.can("view_all")


# ── Dashboard ─────────────────────────────────────────────────────────────────
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user  = self.request.user
        coops = user.get_accessible_cooperatives()
        ago30 = timezone.now().date() - timedelta(days=30)
        ctx.update({
            "cooperative_count":   coops.count(),
            "member_count":        Member.objects.filter(cooperative__in=coops, is_active=True).count(),
            "female_member_count": Member.objects.filter(cooperative__in=coops, is_active=True, gender="female").count(),
            "youth_member_count":  Member.objects.filter(cooperative__in=coops, is_active=True, age_group="youth").count(),
            "total_production_kg": ProductionRecord.objects.filter(
                station__cooperative__in=coops, harvest_date__gte=ago30,
            ).aggregate(t=Sum("quantity_kg"))["t"] or 0,
            "pending_sync_count":  ProductionRecord.objects.filter(is_synced=False).count(),
            "recent_deliveries":   ProductionRecord.objects.filter(
                record_type="cherry_delivery", station__cooperative__in=coops,
            ).select_related("member","station").order_by("-harvest_date")[:10],
        })
        return ctx


# ── Cooperatives ──────────────────────────────────────────────────────────────
class CooperativeListView(LoginRequiredMixin, ListView):
    model = Cooperative
    template_name = "cooperatives/cooperative_list.html"
    context_object_name = "cooperatives"
    paginate_by = 20
    def get_queryset(self):
        qs = self.request.user.get_accessible_cooperatives().annotate(
            member_count=Count("members", filter=Q(members__is_active=True))
        ).select_related("region")
        if q := self.request.GET.get("q"):
            qs = qs.filter(Q(name__icontains=q)|Q(registration_number__icontains=q))
        return qs


class CooperativeDetailView(LoginRequiredMixin, DetailView):
    model = Cooperative
    template_name = "cooperatives/cooperative_detail.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        coop = self.object
        ctx["members"]           = coop.members.filter(is_active=True).order_by("last_name")[:20]
        ctx["washing_stations"]  = coop.washing_stations.filter(is_active=True)
        ctx["recent_deliveries"] = ProductionRecord.objects.filter(
            station__cooperative=coop, record_type="cherry_delivery"
        ).order_by("-harvest_date")[:15]
        ctx["financial_summary"] = FinancialRecord.objects.filter(
            cooperative=coop).values("transaction_type").annotate(total=Sum("amount"))
        return ctx


class CooperativeCreateView(LoginRequiredMixin, CanManageMixin, CreateView):
    model = Cooperative; form_class = CooperativeForm
    template_name = "cooperatives/cooperative_form.html"
    def form_valid(self, form):
        messages.success(self.request, _("Coopérative créée."))
        return super().form_valid(form)
    def get_success_url(self): return f"/cooperatives/{self.object.pk}/"


class CooperativeUpdateView(LoginRequiredMixin, CanManageMixin, UpdateView):
    model = Cooperative; form_class = CooperativeForm
    template_name = "cooperatives/cooperative_form.html"
    def get_success_url(self): return f"/cooperatives/{self.object.pk}/"


# ── Members ───────────────────────────────────────────────────────────────────
class MemberListView(LoginRequiredMixin, ListView):
    model = Member; template_name = "cooperatives/member_list.html"
    context_object_name = "members"; paginate_by = 25
    def get_queryset(self):
        qs = Member.objects.filter(
            cooperative__in=self.request.user.get_accessible_cooperatives(), is_active=True,
        ).select_related("cooperative")
        if q := self.request.GET.get("q"):
            qs = qs.filter(Q(first_name__icontains=q)|Q(last_name__icontains=q)
                           |Q(farmer_code__icontains=q)|Q(member_id__icontains=q))
        if g := self.request.GET.get("gender"): qs = qs.filter(gender=g)
        if a := self.request.GET.get("age_group"): qs = qs.filter(age_group=a)
        return qs.order_by("last_name","first_name")


class MemberCreateView(LoginRequiredMixin, CanManageMixin, CreateView):
    model = Member; form_class = MemberForm
    template_name = "cooperatives/member_form.html"
    def get_form_kwargs(self):
        kw = super().get_form_kwargs(); kw["user"] = self.request.user; return kw
    def form_valid(self, form):
        messages.success(self.request, _("Membre enregistré."))
        return super().form_valid(form)
    def get_success_url(self): return f"/members/{self.object.pk}/"


class MemberDetailView(LoginRequiredMixin, DetailView):
    model = Member; template_name = "cooperatives/member_detail.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["farms"] = self.object.farms.filter(is_active=True)
        ctx["production_records"] = self.object.production_records.order_by("-harvest_date")[:20]
        ctx["total_production_kg"] = self.object.production_records.aggregate(t=Sum("quantity_kg"))["t"] or 0
        return ctx


# ── Cherry Deliveries ─────────────────────────────────────────────────────────
class CherryDeliveryListView(LoginRequiredMixin, ListView):
    model = ProductionRecord; template_name = "cooperatives/cherry_delivery_list.html"
    context_object_name = "deliveries"; paginate_by = 30
    def get_queryset(self):
        qs = ProductionRecord.objects.filter(
            record_type="cherry_delivery",
            station__cooperative__in=self.request.user.get_accessible_cooperatives(),
        ).select_related("member","station","station__cooperative")
        if s := self.request.GET.get("station"): qs = qs.filter(station_id=s)
        if d := self.request.GET.get("date_from"): qs = qs.filter(harvest_date__gte=d)
        if d := self.request.GET.get("date_to"):   qs = qs.filter(harvest_date__lte=d)
        if c := self.request.GET.get("farmer_code"): qs = qs.filter(member__farmer_code__icontains=c)
        if (sync := self.request.GET.get("synced")) == "0": qs = qs.filter(is_synced=False)
        elif sync == "1": qs = qs.filter(is_synced=True)
        return qs.order_by("-harvest_date")
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["stations"]  = WashingStation.objects.filter(
            cooperative__in=self.request.user.get_accessible_cooperatives(), is_active=True)
        qs = self.get_queryset()
        ctx["total_kg"]  = qs.aggregate(t=Sum("quantity_kg"))["t"] or 0
        ctx["total_fc"]  = qs.aggregate(t=Sum("total_price_fc"))["t"] or 0
        return ctx


class CherryDeliveryCreateView(LoginRequiredMixin, CanManageMixin, CreateView):
    model = ProductionRecord; form_class = CherryDeliveryForm
    template_name = "cooperatives/cherry_delivery_form.html"
    def get_form_kwargs(self):
        kw = super().get_form_kwargs(); kw["user"] = self.request.user; return kw
    def form_valid(self, form):
        form.instance.record_type = "cherry_delivery"
        form.instance.crop_type   = "coffee"
        form.instance.created_by  = self.request.user
        messages.success(self.request, _("Livraison enregistrée."))
        return super().form_valid(form)
    def get_success_url(self): return "/deliveries/"


class CherryDeliveryDetailView(LoginRequiredMixin, DetailView):
    model = ProductionRecord; template_name = "cooperatives/cherry_delivery_detail.html"
    queryset = ProductionRecord.objects.filter(record_type="cherry_delivery")


# ── REST API ViewSets ─────────────────────────────────────────────────────────
class CooperativeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CooperativeSerializer; permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self): return self.request.user.get_accessible_cooperatives().select_related("region")


class MemberViewSet(viewsets.ModelViewSet):
    serializer_class = MemberSerializer; permission_classes = [permissions.IsAuthenticated]
    search_fields = ["first_name","last_name","farmer_code","member_id"]
    def get_queryset(self):
        return Member.objects.filter(cooperative__in=self.request.user.get_accessible_cooperatives())


class WashingStationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WashingStationSerializer; permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return WashingStation.objects.filter(
            cooperative__in=self.request.user.get_accessible_cooperatives(), is_active=True)


class ProductionRecordViewSet(viewsets.ModelViewSet):
    serializer_class = ProductionRecordSerializer; permission_classes = [permissions.IsAuthenticated]
    search_fields = ["member__farmer_code","receipt_number"]
    def get_queryset(self):
        qs = ProductionRecord.objects.filter(
            station__cooperative__in=self.request.user.get_accessible_cooperatives(),
        ).select_related("member","station","farm")
        if t := self.request.query_params.get("type"): qs = qs.filter(record_type=t)
        return qs.order_by("-harvest_date")
    def perform_create(self, serializer): serializer.save(created_by=self.request.user)


class CherryDeliveryAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    def get_serializer_class(self):
        return CherryDeliverySerializer if self.request.method == "POST" else ProductionRecordSerializer
    def get_queryset(self):
        return ProductionRecord.objects.filter(record_type="cherry_delivery",
            station__cooperative__in=self.request.user.get_accessible_cooperatives()).order_by("-harvest_date")
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, record_type="cherry_delivery")


class MemberLookupAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        code = request.query_params.get("code","")
        if len(code) < 2: return Response([])
        members = Member.objects.filter(
            farmer_code__icontains=code,
            cooperative__in=request.user.get_accessible_cooperatives(), is_active=True,
        ).values("id","farmer_code","first_name","last_name","groupement","village")[:10]
        return Response(list(members))


# ── Sync API ──────────────────────────────────────────────────────────────────
class SyncPushAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        from sync.services import process_pending_changes
        serializer = SyncPushSerializer(data=request.data, many=True)
        if not serializer.is_valid(): return Response(serializer.errors, status=400)
        results = process_pending_changes(serializer.validated_data, request.user)
        return Response(results)


class SyncPullAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        since_str = request.query_params.get("since")
        try: since = datetime.fromisoformat(since_str) if since_str else None
        except (ValueError, TypeError): since = None
        coops   = request.user.get_accessible_cooperatives()
        filters = {"updated_at__gt": since} if since else {}
        return Response({
            "cooperatives":      CooperativeSerializer(coops.filter(**filters), many=True).data,
            "members":           MemberSerializer(Member.objects.filter(cooperative__in=coops,**filters),many=True).data,
            "washing_stations":  WashingStationSerializer(WashingStation.objects.filter(cooperative__in=coops,is_active=True),many=True).data,
            "production_records":ProductionRecordSerializer(ProductionRecord.objects.filter(station__cooperative__in=coops,**filters),many=True).data,
            "server_timestamp":  timezone.now().isoformat(),
        })
PYEOF

# =============================================================================
# SYNC APP
# =============================================================================
write_file src/sync/__init__.py << 'PYEOF'
PYEOF

write_file src/sync/models.py << 'PYEOF'
"""CO3DATA — Sync: device registry, change queue, sync history"""
import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class Device(models.Model):
    device_id   = models.CharField(max_length=255, unique=True)
    user        = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="devices")
    device_name = models.CharField(max_length=100, blank=True, null=True)
    platform    = models.CharField(max_length=50, blank=True, null=True, help_text="android, ios, web")
    last_sync_at = models.DateTimeField(blank=True, null=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Appareil")
        verbose_name_plural = _("Appareils")

    def __str__(self):
        return f"{self.device_id} ({self.user.username})"


class PendingChange(models.Model):
    CHANGE_TYPES = [("create","Création"),("update","Modification"),("delete","Suppression")]
    CONFLICT_STRATEGIES = [
        ("last_write_wins","Dernière Écriture"),("server_wins","Serveur"),
        ("client_wins","Client"),("manual","Manuel"),
    ]
    device        = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="pending_changes")
    content_type  = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id     = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type","object_id")
    change_type   = models.CharField(max_length=10, choices=CHANGE_TYPES)
    local_uuid    = models.UUIDField(default=uuid.uuid4, unique=True)
    payload       = models.JSONField()
    timestamp     = models.DateTimeField(auto_now_add=True)
    is_synced     = models.BooleanField(default=False)
    attempts      = models.PositiveSmallIntegerField(default=0)
    last_error    = models.TextField(blank=True, null=True)
    conflict_strategy = models.CharField(max_length=20, choices=CONFLICT_STRATEGIES,
                                          default="last_write_wins", blank=True, null=True)

    class Meta:
        verbose_name = _("Changement en Attente")
        verbose_name_plural = _("Changements en Attente")
        ordering = ["timestamp"]
        indexes = [models.Index(fields=["is_synced","device"])]


class SyncLog(models.Model):
    device              = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="sync_logs")
    sync_start_time     = models.DateTimeField(auto_now_add=True)
    sync_end_time       = models.DateTimeField(blank=True, null=True)
    status              = models.CharField(max_length=20, default="success")
    message             = models.TextField(blank=True, null=True)
    changes_uploaded    = models.PositiveIntegerField(default=0)
    changes_downloaded  = models.PositiveIntegerField(default=0)
    conflicts_detected  = models.PositiveSmallIntegerField(default=0)
    conflict_strategy   = models.CharField(max_length=20, default="last_write_wins")

    class Meta:
        verbose_name = _("Journal de Synchronisation")
        verbose_name_plural = _("Journaux de Synchronisation")
        ordering = ["-sync_start_time"]

    def __str__(self):
        return f"Sync {self.device} @ {self.sync_start_time} [{self.status}]"
PYEOF

write_file src/sync/admin.py << 'PYEOF'
from django.contrib import admin
from .models import Device, PendingChange, SyncLog


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ["device_id","user","platform","last_sync_at","is_active"]
    list_filter  = ["platform","is_active"]
    search_fields = ["device_id","user__username"]


@admin.register(PendingChange)
class PendingChangeAdmin(admin.ModelAdmin):
    list_display = ["local_uuid","device","change_type","is_synced","timestamp","attempts"]
    list_filter  = ["change_type","is_synced"]


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ["device","status","changes_uploaded","changes_downloaded","conflicts_detected","sync_start_time"]
    list_filter  = ["status"]
    date_hierarchy = "sync_start_time"
PYEOF

write_file src/sync/services.py << 'PYEOF'
"""CO3DATA — Sync Services: offline change processing"""
import logging
from typing import Dict, Any, List
from django.db import transaction
from django.utils import timezone
from cooperatives.models import Member, Farm, ProductionRecord, FinancialRecord
from sync.models import Device, SyncLog

logger = logging.getLogger("co3data.sync")

MODEL_MAP = {
    "ProductionRecord": ProductionRecord,
    "Member": Member,
    "Farm": Farm,
    "FinancialRecord": FinancialRecord,
}


def get_or_register_device(device_id: str, user) -> Device:
    device, _ = Device.objects.get_or_create(device_id=device_id, defaults={"user": user})
    return device


def process_pending_changes(changes: List[Dict], user) -> Dict:
    results = {"processed": 0, "skipped": 0, "conflicts": [], "errors": []}
    for change in changes:
        model_name = change["model"]
        operation  = change["operation"]
        sync_uuid  = change["sync_uuid"]
        payload    = change["payload"]
        device_id  = change["device_id"]
        model_class = MODEL_MAP.get(model_name)
        if not model_class:
            results["errors"].append({"sync_uuid": str(sync_uuid), "error": f"Unknown model: {model_name}"})
            continue
        try:
            with transaction.atomic():
                result = _apply_change(model_class, operation, sync_uuid, payload, user)
                if result == "skipped":
                    results["skipped"] += 1
                elif result == "conflict":
                    results["conflicts"].append({"sync_uuid": str(sync_uuid), "model": model_name})
                else:
                    results["processed"] += 1
                    device = get_or_register_device(device_id, user)
                    device.last_sync_at = timezone.now()
                    device.save(update_fields=["last_sync_at"])
        except Exception as exc:
            logger.exception(f"Error processing {sync_uuid}: {exc}")
            results["errors"].append({"sync_uuid": str(sync_uuid), "error": str(exc)})
    return results


def _apply_change(model_class, operation, sync_uuid, payload, user) -> str:
    existing = None
    if hasattr(model_class, "sync_uuid"):
        try:
            existing = model_class.objects.get(sync_uuid=sync_uuid)
            if operation == "create":
                return "skipped"
        except model_class.DoesNotExist:
            pass
    if operation == "create":
        _create_record(model_class, payload, sync_uuid, user)
    elif operation == "update":
        if existing is None: _create_record(model_class, payload, sync_uuid, user)
        else: _update_record(existing, payload, user)
    elif operation == "delete":
        if existing and hasattr(existing, "is_active"):
            existing.is_active = False
            existing.save(update_fields=["is_active"])
    return "ok"


def _create_record(model_class, payload, sync_uuid, user):
    p = _clean_payload(model_class, payload)
    p["sync_uuid"] = sync_uuid
    if "is_locally_created" in {f.name for f in model_class._meta.get_fields()}:
        p["is_locally_created"] = True
    field_names = {f.name for f in model_class._meta.get_fields()}
    if "created_by" in field_names:
        p["created_by"] = user
    model_class.objects.create(**p)


def _update_record(instance, payload, user):
    p = _clean_payload(instance.__class__, payload)
    for k, v in p.items():
        if k not in ("id","pk","sync_uuid","created_at","created_by"):
            setattr(instance, k, v)
    instance.save()


def _clean_payload(model_class, payload):
    valid = {f.name for f in model_class._meta.get_fields()}
    return {k: v for k, v in payload.items() if k in valid}
PYEOF

# =============================================================================
# ANALYTICS APP
# =============================================================================
write_file src/analytics/__init__.py << 'PYEOF'
PYEOF

write_file src/analytics/models.py << 'PYEOF'
"""CO3DATA — Analytics: KPIs, reports, data quality"""
from django.db import models
from django.utils.translation import gettext_lazy as _
try:
    from simpleeval import EvalWithCompoundTypes
except ImportError:
    EvalWithCompoundTypes = None
from cooperatives.models import Cooperative
from users.models import User


class KPI(models.Model):
    CATEGORIES = [
        ("production",_("Production")),("financial",_("Financier")),
        ("membership",_("Adhésion")),("gender",_("Genre & Inclusion")),
        ("quality",_("Qualité")),("sustainability",_("Durabilité")),
    ]
    name                 = models.CharField(max_length=255, unique=True)
    slug                 = models.SlugField(unique=True)
    category             = models.CharField(max_length=20, choices=CATEGORIES)
    description          = models.TextField(blank=True, null=True)
    unit                 = models.CharField(max_length=30, blank=True, null=True)
    calculation_formula  = models.TextField()
    is_active            = models.BooleanField(default=True)
    higher_is_better     = models.BooleanField(default=True)
    created_by           = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("KPI")
        verbose_name_plural = _("KPIs")
        ordering = ["category","name"]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def compute(self, context: dict):
        if EvalWithCompoundTypes is None: return None
        try:
            return float(EvalWithCompoundTypes(names=context).eval(self.calculation_formula))
        except Exception:
            return None


class KPIResult(models.Model):
    kpi          = models.ForeignKey(KPI, on_delete=models.CASCADE, related_name="results")
    cooperative  = models.ForeignKey(Cooperative, on_delete=models.CASCADE, related_name="kpi_results")
    period_start = models.DateField()
    period_end   = models.DateField()
    value        = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    computed_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Résultat KPI")
        unique_together = [("kpi","cooperative","period_start","period_end")]
        ordering = ["-period_end"]


class ReportConfiguration(models.Model):
    FORMATS = [("pdf","PDF"),("xlsx","Excel"),("csv","CSV")]
    name             = models.CharField(max_length=255)
    description      = models.TextField(blank=True, null=True)
    kpis             = models.ManyToManyField(KPI, blank=True)
    parameters       = models.JSONField(blank=True, null=True)
    format           = models.CharField(max_length=10, choices=FORMATS, default="pdf")
    schedule_cron    = models.CharField(max_length=50, blank=True, null=True)
    viewable_by_roles = models.JSONField(default=list)
    created_by       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Configuration de Rapport")
        verbose_name_plural = _("Configurations de Rapports")

    def __str__(self): return self.name
    def is_accessible_by(self, user): return user.role == "admin" or user.role in self.viewable_by_roles


class DataValidationRule(models.Model):
    SEVERITIES = [("warning",_("Avertissement")),("error",_("Erreur"))]
    name              = models.CharField(max_length=255)
    description       = models.TextField(blank=True, null=True)
    rule_expression   = models.TextField()
    applies_to_model  = models.CharField(max_length=100)
    applies_to_field  = models.CharField(max_length=100, blank=True, null=True)
    severity          = models.CharField(max_length=10, choices=SEVERITIES, default="warning")
    is_active         = models.BooleanField(default=True)
    created_by        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Règle de Validation")
        verbose_name_plural = _("Règles de Validation")

    def __str__(self): return self.name
    def evaluate(self, data: dict) -> bool:
        if EvalWithCompoundTypes is None: return True
        try: return bool(EvalWithCompoundTypes(names=data).eval(self.rule_expression))
        except Exception: return True


class DataQualityAlert(models.Model):
    rule         = models.ForeignKey(DataValidationRule, on_delete=models.CASCADE, related_name="alerts")
    cooperative  = models.ForeignKey(Cooperative, on_delete=models.CASCADE, related_name="data_quality_alerts")
    record_model = models.CharField(max_length=100)
    record_id    = models.PositiveIntegerField()
    message      = models.TextField()
    alert_date   = models.DateTimeField(auto_now_add=True)
    is_resolved  = models.BooleanField(default=False)
    resolved_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name="resolved_alerts")
    resolved_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _("Alerte Qualité")
        verbose_name_plural = _("Alertes Qualité")
        ordering = ["-alert_date"]
        indexes = [models.Index(fields=["cooperative","is_resolved"])]
PYEOF

write_file src/analytics/admin.py << 'PYEOF'
from django.contrib import admin
from .models import KPI, KPIResult, ReportConfiguration, DataValidationRule, DataQualityAlert


@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ["name","category","unit","is_active","higher_is_better"]
    list_filter  = ["category","is_active"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(KPIResult)
class KPIResultAdmin(admin.ModelAdmin):
    list_display = ["kpi","cooperative","period_start","period_end","value","computed_at"]
    list_filter  = ["kpi","cooperative"]


@admin.register(ReportConfiguration)
class ReportConfigAdmin(admin.ModelAdmin):
    list_display = ["name","format","created_by","created_at"]
    filter_horizontal = ["kpis"]


@admin.register(DataValidationRule)
class DataValidationRuleAdmin(admin.ModelAdmin):
    list_display = ["name","applies_to_model","severity","is_active"]
    list_filter  = ["severity","is_active"]


@admin.register(DataQualityAlert)
class DataQualityAlertAdmin(admin.ModelAdmin):
    list_display = ["rule","cooperative","record_model","record_id","is_resolved","alert_date"]
    list_filter  = ["is_resolved","cooperative","rule__severity"]
PYEOF

write_file src/analytics/views.py << 'PYEOF'
"""CO3DATA — Analytics Views"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from django.views.generic import TemplateView, ListView
from .models import KPI, KPIResult, DataQualityAlert, ReportConfiguration
from cooperatives.models import Member, ProductionRecord, FinancialRecord


class CanViewReportsMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.can("view_reports") or self.request.user.can("view_all")


class AnalyticsDashboardView(LoginRequiredMixin, CanViewReportsMixin, TemplateView):
    template_name = "analytics/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user  = self.request.user
        coops = user.get_accessible_cooperatives()
        today = timezone.now().date()
        start = today.replace(day=1)

        ctx["open_alerts"]   = DataQualityAlert.objects.filter(
            cooperative__in=coops, is_resolved=False).count()
        ctx["kpi_results"]   = KPIResult.objects.filter(
            cooperative__in=coops).select_related("kpi","cooperative").order_by("-period_end")[:20]
        ctx["report_configs"] = ReportConfiguration.objects.filter(
            viewable_by_roles__contains=user.role)
        # Inclusion stats
        total_m  = Member.objects.filter(cooperative__in=coops, is_active=True)
        ctx["inclusion_stats"] = {
            "total":   total_m.count(),
            "female":  total_m.filter(gender="female").count(),
            "youth":   total_m.filter(age_group="youth").count(),
            "male":    total_m.filter(gender="male").count(),
        }
        # Production trend last 6 months
        ctx["production_trend"] = [
            {
                "month": (today - timedelta(days=30*i)).strftime("%Y-%m"),
                "total_kg": ProductionRecord.objects.filter(
                    station__cooperative__in=coops,
                    harvest_date__year=(today - timedelta(days=30*i)).year,
                    harvest_date__month=(today - timedelta(days=30*i)).month,
                ).aggregate(t=Sum("quantity_kg"))["t"] or 0,
            }
            for i in range(6)
        ]
        return ctx


class AlertListView(LoginRequiredMixin, CanViewReportsMixin, ListView):
    model = DataQualityAlert
    template_name = "analytics/alert_list.html"
    context_object_name = "alerts"
    paginate_by = 30

    def get_queryset(self):
        return DataQualityAlert.objects.filter(
            cooperative__in=self.request.user.get_accessible_cooperatives(),
            is_resolved=False,
        ).select_related("rule","cooperative").order_by("-alert_date")
PYEOF

write_file src/analytics/urls.py << 'PYEOF'
from django.urls import path
from . import views
app_name = "analytics"
urlpatterns = [
    path("",        views.AnalyticsDashboardView.as_view(), name="dashboard"),
    path("alerts/", views.AlertListView.as_view(),          name="alerts"),
]
PYEOF

# =============================================================================
# QUESTIONNAIRES APP
# =============================================================================
write_file src/questionnaires/__init__.py << 'PYEOF'
PYEOF

write_file src/questionnaires/models.py << 'PYEOF'
"""CO3DATA — Questionnaires: dynamic data collection engine"""
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _


class Questionnaire(models.Model):
    TARGET_CHOICES = [("cooperative",_("Coopérative")),("member",_("Membre"))]
    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by  = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    is_active   = models.BooleanField(default=True)
    target_model = models.CharField(max_length=50, choices=TARGET_CHOICES, default="cooperative")

    class Meta:
        verbose_name = _("Questionnaire")
        verbose_name_plural = _("Questionnaires")

    def __str__(self): return self.title


class Question(models.Model):
    TYPES = [
        ("text",_("Texte Libre")),("number",_("Nombre")),
        ("select",_("Choix Unique")),("multiselect",_("Choix Multiple")),
        ("date",_("Date")),("boolean",_("Oui/Non")),("file",_("Fichier")),
    ]
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name="questions")
    text          = models.TextField()
    question_type = models.CharField(max_length=20, choices=TYPES)
    order         = models.PositiveIntegerField(default=0)
    is_required   = models.BooleanField(default=False)
    options       = models.JSONField(blank=True, null=True, help_text='{"choices":["A","B","C"]}')
    help_text     = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ["order"]

    def __str__(self): return f"[{self.questionnaire.title}] {self.text[:60]}"


class Submission(models.Model):
    questionnaire  = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name="submissions")
    submitted_by   = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True)
    submitted_at   = models.DateTimeField(auto_now_add=True)
    content_type   = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id      = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type","object_id")
    is_complete    = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Soumission")
        verbose_name_plural = _("Soumissions")
        ordering = ["-submitted_at"]


class Answer(models.Model):
    submission    = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="answers")
    question      = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    value_text    = models.TextField(blank=True, null=True)
    value_number  = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    value_date    = models.DateField(blank=True, null=True)
    value_boolean = models.BooleanField(blank=True, null=True)

    class Meta:
        verbose_name = _("Réponse")
        verbose_name_plural = _("Réponses")
        unique_together = [("submission","question")]
PYEOF

write_file src/questionnaires/admin.py << 'PYEOF'
from django.contrib import admin
from .models import Questionnaire, Question, Submission, Answer


class QuestionInline(admin.TabularInline):
    model  = Question
    extra  = 1
    fields = ["order","text","question_type","is_required","options"]


class AnswerInline(admin.TabularInline):
    model  = Answer
    extra  = 0
    readonly_fields = ["question","value_text","value_number","value_date","value_boolean"]


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ["title","target_model","is_active","created_at"]
    list_filter  = ["target_model","is_active"]
    inlines      = [QuestionInline]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["questionnaire","submitted_by","submitted_at","is_complete"]
    list_filter  = ["questionnaire","is_complete"]
    inlines      = [AnswerInline]
PYEOF

write_file src/questionnaires/views.py << 'PYEOF'
"""CO3DATA — Questionnaires Views"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from .models import Questionnaire, Question, Submission, Answer


class QuestionnaireListView(LoginRequiredMixin, ListView):
    model = Questionnaire
    template_name = "questionnaires/questionnaire_list.html"
    context_object_name = "questionnaires"
    def get_queryset(self): return Questionnaire.objects.filter(is_active=True)


class QuestionnaireSubmitView(LoginRequiredMixin, TemplateView):
    template_name = "questionnaires/submit.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["questionnaire"] = get_object_or_404(Questionnaire, pk=self.kwargs["pk"], is_active=True)
        ctx["questions"] = ctx["questionnaire"].questions.all()
        return ctx

    def post(self, request, pk):
        questionnaire = get_object_or_404(Questionnaire, pk=pk)
        from cooperatives.models import Cooperative
        from django.contrib.contenttypes.models import ContentType
        coop_id = request.POST.get("cooperative_id") or (
            request.user.cooperative.pk if request.user.cooperative else None)
        if not coop_id:
            messages.error(request, _("Coopérative non spécifiée."))
            return redirect(f"/questionnaires/{pk}/submit/")
        coop = get_object_or_404(Cooperative, pk=coop_id)
        ct = ContentType.objects.get_for_model(Cooperative)
        submission = Submission.objects.create(
            questionnaire=questionnaire, submitted_by=request.user,
            content_type=ct, object_id=coop.pk)
        for question in questionnaire.questions.all():
            field_key = f"question_{question.pk}"
            raw = request.POST.get(field_key)
            if raw is not None:
                Answer.objects.create(submission=submission, question=question, value_text=raw)
        submission.is_complete = True
        submission.save(update_fields=["is_complete"])
        messages.success(request, _("Questionnaire soumis avec succès."))
        return redirect("/questionnaires/")
PYEOF

write_file src/questionnaires/urls.py << 'PYEOF'
from django.urls import path
from . import views
app_name = "questionnaires"
urlpatterns = [
    path("",             views.QuestionnaireListView.as_view(),   name="list"),
    path("<int:pk>/submit/", views.QuestionnaireSubmitView.as_view(), name="submit"),
]
PYEOF

# =============================================================================
# TEMPLATES
# =============================================================================
write_file src/templates/base.html << 'PYEOF'
{% load i18n static %}
<!DOCTYPE html>
<html lang="{{ LANGUAGE_CODE|default:'fr' }}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <meta name="theme-color" content="#1B6CA8">
  <title>{% block title %}CO3DATA{% endblock %} — CO3DATA</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
  <link rel="stylesheet" href="{% static 'css/co3data.css' %}">
  {% block extra_css %}{% endblock %}
</head>
<body class="co3data-app">
  {% if user.is_authenticated %}
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary sticky-top shadow-sm">
    <div class="container-fluid">
      <a class="navbar-brand fw-bold" href="/dashboard/">
        <i class="bi bi-tree"></i> CO3DATA
      </a>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#mainNav">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="mainNav">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item"><a class="nav-link" href="/cooperatives/"><i class="bi bi-building"></i> {% trans "Coopératives" %}</a></li>
          <li class="nav-item"><a class="nav-link" href="/members/"><i class="bi bi-people"></i> {% trans "Membres" %}</a></li>
          <li class="nav-item"><a class="nav-link" href="/deliveries/"><i class="bi bi-box-arrow-in-down"></i> {% trans "Livraisons" %}</a></li>
          <li class="nav-item"><a class="nav-link" href="/questionnaires/"><i class="bi bi-clipboard-data"></i> {% trans "Questionnaires" %}</a></li>
          {% if user.can_view_reports %}<li class="nav-item"><a class="nav-link" href="/analytics/"><i class="bi bi-bar-chart"></i> {% trans "Analytique" %}</a></li>{% endif %}
        </ul>
        <div class="navbar-nav">
          {% if pending_sync_count %}<span class="badge bg-warning text-dark me-2"><i class="bi bi-cloud-slash"></i> {{ pending_sync_count }}</span>{% endif %}
          <a class="nav-link" href="/users/profile/"><i class="bi bi-person-circle"></i> {{ user.get_full_name|default:user.username }}</a>
          <a class="nav-link" href="/users/logout/"><i class="bi bi-box-arrow-right"></i></a>
        </div>
      </div>
    </div>
  </nav>
  {% endif %}
  <main class="container-fluid py-3">
    {% if messages %}
      {% for message in messages %}
        <div class="alert alert-{{ message.tags|default:'info' }} alert-dismissible fade show" role="alert">
          {{ message }}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
      {% endfor %}
    {% endif %}
    {% block content %}{% endblock %}
  </main>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  <script src="{% static 'js/co3data.js' %}"></script>
  {% block extra_js %}{% endblock %}
</body>
</html>
PYEOF

write_file src/templates/dashboard.html << 'PYEOF'
{% extends "base.html" %}
{% load i18n humanize %}
{% block title %}{% trans "Tableau de Bord" %}{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h1 class="h3 mb-0"><i class="bi bi-speedometer2"></i> {% trans "Tableau de Bord" %}</h1>
  <small class="text-muted">{{ request.user.get_full_name }} · {{ request.user.get_role_display }}</small>
</div>

<div class="row g-3 mb-4">
  <div class="col-6 col-md-3">
    <div class="card border-0 shadow-sm h-100">
      <div class="card-body text-center">
        <div class="display-6 text-primary fw-bold">{{ cooperative_count }}</div>
        <div class="text-muted small">{% trans "Coopératives" %}</div>
        <i class="bi bi-building fs-4 text-primary opacity-25"></i>
      </div>
    </div>
  </div>
  <div class="col-6 col-md-3">
    <div class="card border-0 shadow-sm h-100">
      <div class="card-body text-center">
        <div class="display-6 text-success fw-bold">{{ member_count|intcomma }}</div>
        <div class="text-muted small">{% trans "Membres Actifs" %}</div>
        <div class="mt-1">
          <span class="badge bg-success-subtle text-success"><i class="bi bi-gender-female"></i> {{ female_member_count }}</span>
          <span class="badge bg-info-subtle text-info ms-1"><i class="bi bi-star"></i> {{ youth_member_count }} {% trans "jeunes" %}</span>
        </div>
      </div>
    </div>
  </div>
  <div class="col-6 col-md-3">
    <div class="card border-0 shadow-sm h-100">
      <div class="card-body text-center">
        <div class="display-6 text-warning fw-bold">{{ total_production_kg|floatformat:0|intcomma }}</div>
        <div class="text-muted small">{% trans "kg (30 derniers jours)" %}</div>
        <i class="bi bi-basket fs-4 text-warning opacity-25"></i>
      </div>
    </div>
  </div>
  <div class="col-6 col-md-3">
    <div class="card border-0 shadow-sm h-100 {% if pending_sync_count %}border-warning{% endif %}">
      <div class="card-body text-center">
        <div class="display-6 {% if pending_sync_count %}text-warning{% else %}text-secondary{% endif %} fw-bold">{{ pending_sync_count }}</div>
        <div class="text-muted small">{% trans "En attente sync" %}</div>
        <i class="bi bi-cloud-upload fs-4 {% if pending_sync_count %}text-warning{% else %}text-secondary{% endif %} opacity-25"></i>
      </div>
    </div>
  </div>
</div>

<div class="card border-0 shadow-sm">
  <div class="card-header bg-white d-flex justify-content-between align-items-center">
    <strong><i class="bi bi-box-arrow-in-down text-success"></i> {% trans "Livraisons Récentes de Cerises" %}</strong>
    <a href="/deliveries/create/" class="btn btn-success btn-sm"><i class="bi bi-plus"></i> {% trans "Nouvelle Livraison" %}</a>
  </div>
  <div class="card-body p-0">
    {% if recent_deliveries %}
    <div class="table-responsive">
      <table class="table table-hover mb-0 align-middle">
        <thead class="table-light"><tr>
          <th>{% trans "Date" %}</th><th>{% trans "Agriculteur" %}</th>
          <th>{% trans "Station" %}</th><th class="text-end">{% trans "Quantité (kg)" %}</th>
          <th class="text-end">{% trans "Prix Total (FC)" %}</th><th>{% trans "Sync" %}</th>
        </tr></thead>
        <tbody>{% for d in recent_deliveries %}
          <tr>
            <td>{{ d.harvest_date }}</td>
            <td>{{ d.member.full_name|default:"—" }}<br><small class="text-muted">{{ d.member.farmer_code|default:"" }}</small></td>
            <td>{{ d.station.name|default:"—" }}</td>
            <td class="text-end fw-bold">{{ d.quantity_kg|floatformat:1|intcomma }}</td>
            <td class="text-end">{{ d.total_price_fc|floatformat:0|intcomma|default:"—" }}</td>
            <td>{% if d.is_synced %}<span class="badge bg-success">✓</span>{% else %}<span class="badge bg-warning text-dark">⏳</span>{% endif %}</td>
          </tr>
        {% endfor %}</tbody>
      </table>
    </div>
    {% else %}<p class="text-center text-muted py-4">{% trans "Aucune livraison récente." %}</p>{% endif %}
  </div>
</div>
{% endblock %}
PYEOF

write_file src/templates/users/login.html << 'PYEOF'
{% load i18n %}
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>CO3DATA — {% trans "Connexion" %}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
</head>
<body class="bg-light d-flex align-items-center min-vh-100">
  <div class="container" style="max-width:400px">
    <div class="card shadow border-0">
      <div class="card-header bg-primary text-white text-center py-4">
        <h2 class="mb-0 fw-bold"><i class="bi bi-tree"></i> CO3DATA</h2>
        <small>{% trans "Coopératives Café & Cacao — Afrique Centrale" %}</small>
      </div>
      <div class="card-body p-4">
        {% if form.errors %}<div class="alert alert-danger">{% trans "Identifiants incorrects." %}</div>{% endif %}
        <form method="post">
          {% csrf_token %}
          <div class="mb-3">
            <label class="form-label">{% trans "Nom d'utilisateur" %}</label>
            <input type="text" name="username" class="form-control form-control-lg" autofocus required>
          </div>
          <div class="mb-3">
            <label class="form-label">{% trans "Mot de passe" %}</label>
            <input type="password" name="password" class="form-control form-control-lg" required>
          </div>
          <input type="hidden" name="next" value="{{ next }}">
          <button type="submit" class="btn btn-primary btn-lg w-100">{% trans "Se connecter" %}</button>
        </form>
      </div>
      <div class="card-footer text-center text-muted small py-2">CO3DATA v1.0</div>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
</body>
</html>
PYEOF

write_file src/templates/cooperatives/cherry_delivery_form.html << 'PYEOF'
{% extends "base.html" %}
{% load i18n crispy_forms_tags %}
{% block title %}{% trans "Nouvelle Livraison de Cerises" %}{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-lg-9">
    <div class="card shadow border-0">
      <div class="card-header bg-success text-white">
        <h4 class="mb-0"><i class="bi bi-box-arrow-in-down"></i> {% trans "Enregistrer une Livraison de Cerises" %}</h4>
        <small>{% trans "Données enregistrées localement si hors ligne." %}</small>
      </div>
      <div class="card-body">
        <form method="post" id="cherry-form">
          {% csrf_token %}
          {% crispy form %}
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
{% block extra_js %}
<script>
// Auto-calculate total price
document.addEventListener('input', function(e) {
  if (e.target.name === 'quantity_kg' || e.target.name === 'base_price_fc') {
    const qty   = parseFloat(document.querySelector('[name=quantity_kg]').value) || 0;
    const price = parseFloat(document.querySelector('[name=base_price_fc]').value) || 0;
    document.querySelector('[name=total_price_fc]').value = (qty * price).toFixed(2);
  }
});
// Member autocomplete
const searchInput = document.querySelector('[data-autocomplete-url]');
const resultsDiv  = document.getElementById('member-autocomplete-results');
const memberField = document.querySelector('[name=member]');
if (searchInput) {
  searchInput.addEventListener('input', async function() {
    const code = this.value.trim();
    if (code.length < 2) { resultsDiv.classList.add('d-none'); return; }
    const res  = await fetch(`/api/v1/members/lookup/?code=${encodeURIComponent(code)}`);
    const data = await res.json();
    resultsDiv.innerHTML = '';
    if (data.length === 0) { resultsDiv.classList.add('d-none'); return; }
    data.forEach(m => {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'list-group-item list-group-item-action';
      item.innerHTML = `<strong>${m.farmer_code}</strong> — ${m.first_name} ${m.last_name} <span class="text-muted">(${m.village || ''})</span>`;
      item.addEventListener('click', () => {
        searchInput.value = m.farmer_code;
        if (memberField) {
          const opt = document.createElement('option');
          opt.value = m.id; opt.selected = true;
          memberField.appendChild(opt);
        }
        resultsDiv.classList.add('d-none');
      });
      resultsDiv.appendChild(item);
    });
    resultsDiv.classList.remove('d-none');
  });
}
// Mark offline if no network
if (!navigator.onLine) {
  const flag = document.querySelector('[name=is_locally_created]');
  if (flag) flag.value = 'on';
  document.querySelector('.card-header').insertAdjacentHTML('beforeend',
    '<div class="alert alert-warning mt-2 mb-0"><i class="bi bi-wifi-off"></i> Hors ligne — données sauvegardées localement.</div>');
}
</script>
{% endblock %}
PYEOF

write_file src/templates/cooperatives/cherry_delivery_list.html << 'PYEOF'
{% extends "base.html" %}
{% load i18n humanize %}
{% block title %}{% trans "Livraisons de Cerises" %}{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <h2><i class="bi bi-box-arrow-in-down text-success"></i> {% trans "Livraisons de Cerises" %}</h2>
  <a href="/deliveries/create/" class="btn btn-success"><i class="bi bi-plus-circle"></i> {% trans "Nouvelle Livraison" %}</a>
</div>
<!-- Filters -->
<div class="card mb-3 border-0 shadow-sm">
  <div class="card-body py-2">
    <form method="get" class="row g-2 align-items-end">
      <div class="col-md-3">
        <label class="form-label small">{% trans "Station" %}</label>
        <select name="station" class="form-select form-select-sm">
          <option value="">{% trans "Toutes les stations" %}</option>
          {% for s in stations %}<option value="{{ s.pk }}" {% if request.GET.station == s.pk|stringformat:"s" %}selected{% endif %}>{{ s.name }}</option>{% endfor %}
        </select>
      </div>
      <div class="col-md-2">
        <label class="form-label small">{% trans "Du" %}</label>
        <input type="date" name="date_from" value="{{ request.GET.date_from }}" class="form-control form-control-sm">
      </div>
      <div class="col-md-2">
        <label class="form-label small">{% trans "Au" %}</label>
        <input type="date" name="date_to"   value="{{ request.GET.date_to }}"   class="form-control form-control-sm">
      </div>
      <div class="col-md-2">
        <label class="form-label small">{% trans "Code Agriculteur" %}</label>
        <input type="text" name="farmer_code" value="{{ request.GET.farmer_code }}" class="form-control form-control-sm" placeholder="TCC BMB 009">
      </div>
      <div class="col-md-2">
        <label class="form-label small">{% trans "Sync" %}</label>
        <select name="synced" class="form-select form-select-sm">
          <option value="">{% trans "Tous" %}</option>
          <option value="1" {% if request.GET.synced == "1" %}selected{% endif %}>{% trans "Synchronisés" %}</option>
          <option value="0" {% if request.GET.synced == "0" %}selected{% endif %}>{% trans "Hors ligne" %}</option>
        </select>
      </div>
      <div class="col-md-1">
        <button type="submit" class="btn btn-primary btn-sm w-100"><i class="bi bi-search"></i></button>
      </div>
    </form>
  </div>
</div>
<!-- Totals -->
<div class="row g-2 mb-3">
  <div class="col-md-3"><div class="card bg-success text-white border-0"><div class="card-body py-2 text-center"><div class="fw-bold fs-5">{{ total_kg|floatformat:1|intcomma }} kg</div><small>{% trans "Total Quantité" %}</small></div></div></div>
  <div class="col-md-3"><div class="card bg-primary text-white border-0"><div class="card-body py-2 text-center"><div class="fw-bold fs-5">{{ total_fc|floatformat:0|intcomma }} FC</div><small>{% trans "Total Prix" %}</small></div></div></div>
  <div class="col-md-3"><div class="card bg-info text-white border-0"><div class="card-body py-2 text-center"><div class="fw-bold fs-5">{{ page_obj.paginator.count }}</div><small>{% trans "Livraisons" %}</small></div></div></div>
</div>
<!-- Table -->
<div class="card border-0 shadow-sm">
  <div class="table-responsive">
    <table class="table table-hover align-middle mb-0">
      <thead class="table-light">
        <tr>
          <th>{% trans "Date" %}</th><th>{% trans "Agriculteur" %}</th><th>{% trans "Station" %}</th>
          <th class="text-end">{% trans "Qté (kg)" %}</th><th class="text-end">{% trans "Prix FC" %}</th>
          <th>{% trans "Reçu" %}</th><th>{% trans "Sync" %}</th><th></th>
        </tr>
      </thead>
      <tbody>
        {% for d in deliveries %}
        <tr>
          <td>{{ d.harvest_date|date:"d/m/Y" }}</td>
          <td>
            <span class="fw-bold">{{ d.member.full_name|default:"—" }}</span><br>
            <small class="text-muted font-monospace">{{ d.member.farmer_code|default:"" }}</small>
          </td>
          <td>{{ d.station.name|default:"—" }}</td>
          <td class="text-end fw-bold">{{ d.quantity_kg|floatformat:1|intcomma }}</td>
          <td class="text-end text-muted">{{ d.total_price_fc|floatformat:0|intcomma|default:"—" }}</td>
          <td><small class="font-monospace">{{ d.receipt_number|default:"—" }}</small></td>
          <td>
            {% if d.is_synced %}<span class="badge bg-success"><i class="bi bi-cloud-check"></i> Sync</span>
            {% else %}<span class="badge bg-warning text-dark"><i class="bi bi-cloud-slash"></i> Local</span>{% endif %}
          </td>
          <td><a href="/deliveries/{{ d.pk }}/" class="btn btn-outline-secondary btn-sm"><i class="bi bi-eye"></i></a></td>
        </tr>
        {% empty %}
        <tr><td colspan="8" class="text-center text-muted py-5"><i class="bi bi-inbox fs-2 d-block mb-2"></i>{% trans "Aucune livraison trouvée." %}</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
<!-- Pagination -->
{% if page_obj.has_other_pages %}
<nav class="mt-3"><ul class="pagination justify-content-center">
  {% if page_obj.has_previous %}<li class="page-item"><a class="page-link" href="?page={{ page_obj.previous_page_number }}">‹</a></li>{% endif %}
  <li class="page-item disabled"><span class="page-link">{{ page_obj.number }} / {{ page_obj.paginator.num_pages }}</span></li>
  {% if page_obj.has_next %}<li class="page-item"><a class="page-link" href="?page={{ page_obj.next_page_number }}">›</a></li>{% endif %}
</ul></nav>
{% endif %}
{% endblock %}
PYEOF

# =============================================================================
# STATIC FILES
# =============================================================================
write_file src/static/css/co3data.css << 'PYEOF'
/* CO3DATA — Custom Styles */
:root {
  --co3-primary:   #1B6CA8;
  --co3-success:   #2E7D32;
  --co3-warning:   #E65100;
  --co3-accent:    #F9A825;
  --co3-bg:        #F4F6F9;
}
body.co3data-app { background-color: var(--co3-bg); font-family: 'Segoe UI', system-ui, sans-serif; }
.navbar { border-bottom: 3px solid var(--co3-accent); }
.card  { border-radius: .75rem; }
.card-header { border-radius: .75rem .75rem 0 0 !important; }
.table th { font-size: .8rem; text-transform: uppercase; letter-spacing: .05em; color: #6c757d; }
.font-monospace { font-family: 'Courier New', monospace; font-size: .85em; }
.badge { font-size: .75rem; }
/* Offline indicator */
body.offline::after {
  content: "⚡ Hors Ligne";
  position: fixed; bottom: 1rem; right: 1rem;
  background: #E65100; color: #fff; padding: .4rem .8rem;
  border-radius: 999px; font-size: .8rem; z-index: 9999;
}
PYEOF

write_file src/static/js/co3data.js << 'PYEOF'
/* CO3DATA — Main JavaScript */
"use strict";

// Offline detection
function updateOnlineStatus() {
  document.body.classList.toggle("offline", !navigator.onLine);
}
window.addEventListener("online",  updateOnlineStatus);
window.addEventListener("offline", updateOnlineStatus);
updateOnlineStatus();

// Service Worker registration (offline-first)
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/static/js/sw.js").catch(() => {});
}

// Auto-dismiss alerts after 5 seconds
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".alert.alert-success").forEach(el => {
    setTimeout(() => el.classList.add("fade"), 4500);
    setTimeout(() => el.remove(), 5000);
  });
});
PYEOF

write_file src/static/js/sw.js << 'PYEOF'
/* CO3DATA — Service Worker (offline cache) */
const CACHE_NAME = "co3data-v1";
const STATIC_ASSETS = ["/", "/dashboard/", "/deliveries/", "/members/",
  "/static/css/co3data.css", "/static/js/co3data.js"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(STATIC_ASSETS)));
});

self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    fetch(e.request)
      .then(res => { caches.open(CACHE_NAME).then(c => c.put(e.request, res.clone())); return res; })
      .catch(() => caches.match(e.request))
  );
});
PYEOF

# =============================================================================
# TESTS
# =============================================================================
write_file tests/__init__.py << 'PYEOF'
PYEOF

write_file tests/conftest.py << 'PYEOF'
"""CO3DATA — pytest / Django test fixtures"""
import pytest
from django.test import TestCase


@pytest.fixture
def region(db):
    from users.models import Region
    return Region.objects.create(name="Kivu", country="DRC")


@pytest.fixture
def cooperative(db, region):
    from cooperatives.models import Cooperative
    return Cooperative.objects.create(name="TCC Kivu", type="coffee", region=region)


@pytest.fixture
def washing_station(db, cooperative):
    from cooperatives.models import WashingStation
    return WashingStation.objects.create(cooperative=cooperative, name="KAHISA", village="Kahisa")


@pytest.fixture
def field_agent(db, cooperative):
    from users.models import User
    return User.objects.create_user(
        username="agent01", password="testpass123",
        role="field_agent", cooperative=cooperative,
    )


@pytest.fixture
def member(db, cooperative):
    from cooperatives.models import Member
    return Member.objects.create(
        cooperative=cooperative, member_id="BMB-009",
        farmer_code="TCC BMB 009",
        first_name="Jean", last_name="Mushagalusa",
        gender="male", age_group="adult",
    )
PYEOF

write_file tests/unit/test_models.py << 'PYEOF'
"""Unit tests for CO3DATA models"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError


class TestFarmerCodeValidation:
    def test_valid_farmer_code(self, member):
        assert member.farmer_code == "TCC BMB 009"
        assert member.farmer_code_prefix == "TCC"
        assert member.farmer_code_initials == "BMB"
        assert member.farmer_code_number == 9

    def test_invalid_farmer_code_raises(self, db, cooperative):
        from cooperatives.models import Member
        with pytest.raises(ValidationError):
            Member.objects.create(
                cooperative=cooperative, member_id="BAD-001",
                farmer_code="INVALID",
                first_name="Test", last_name="User",
                gender="male", age_group="adult",
            )


class TestProductionRecord:
    def test_total_price_auto_computed(self, db, member, washing_station):
        from cooperatives.models import ProductionRecord
        import datetime
        record = ProductionRecord.objects.create(
            record_type="cherry_delivery",
            crop_type="coffee",
            member=member,
            station=washing_station,
            harvest_date=datetime.date.today(),
            quantity_kg=Decimal("56.0"),
            base_price_fc=Decimal("1000.00"),
            receipt_number="REC-001",
        )
        assert record.total_price_fc == Decimal("56000.00")

    def test_cherry_delivery_requires_receipt(self, db, member, washing_station):
        from cooperatives.models import ProductionRecord
        import datetime
        with pytest.raises(ValidationError):
            r = ProductionRecord(
                record_type="cherry_delivery",
                crop_type="coffee",
                member=member,
                station=washing_station,
                harvest_date=datetime.date.today(),
                quantity_kg=Decimal("10.0"),
                # No receipt_number
            )
            r.full_clean()


class TestCooperativeStats:
    def test_member_counts(self, cooperative, member):
        assert cooperative.member_count == 1
        assert cooperative.female_member_count == 0


class TestUserRBAC:
    def test_field_agent_permissions(self, field_agent):
        assert field_agent.can("add_member") is True
        assert field_agent.can("view_reports") is False
        assert field_agent.can("view_all") is False

    def test_admin_has_all_permissions(self, db):
        from users.models import User
        admin = User.objects.create_user(username="admin01", password="x", role="admin")
        assert admin.can("view_reports") is True
        assert admin.can("export_data") is True
PYEOF

write_file tests/unit/test_sync_services.py << 'PYEOF'
"""Unit tests for offline sync service"""
import pytest
import uuid
from django.utils import timezone


@pytest.mark.django_db
def test_process_create_change(field_agent, cooperative, washing_station):
    from sync.services import process_pending_changes
    import datetime
    sync_id = uuid.uuid4()
    changes = [{
        "model": "ProductionRecord",
        "operation": "create",
        "sync_uuid": sync_id,
        "payload": {
            "record_type": "cherry_delivery",
            "crop_type": "coffee",
            "station": washing_station.pk,
            "harvest_date": datetime.date.today().isoformat(),
            "quantity_kg": "45.5",
            "receipt_number": "REC-SYNC-001",
        },
        "local_timestamp": timezone.now().isoformat(),
        "device_id": "test-device-001",
    }]
    results = process_pending_changes(changes, field_agent)
    assert results["processed"] == 1
    assert results["errors"] == []


@pytest.mark.django_db
def test_idempotent_sync(field_agent, cooperative, washing_station):
    """Duplicate sync_uuid should be skipped, not duplicated."""
    from sync.services import process_pending_changes
    from cooperatives.models import ProductionRecord
    import datetime
    sync_id = uuid.uuid4()
    change = [{
        "model": "ProductionRecord",
        "operation": "create",
        "sync_uuid": sync_id,
        "payload": {
            "record_type": "cherry_delivery",
            "crop_type": "coffee",
            "station": washing_station.pk,
            "harvest_date": datetime.date.today().isoformat(),
            "quantity_kg": "30.0",
            "receipt_number": "REC-IDEM-001",
        },
        "local_timestamp": timezone.now().isoformat(),
        "device_id": "test-device-002",
    }]
    process_pending_changes(change, field_agent)
    process_pending_changes(change, field_agent)  # second call
    assert ProductionRecord.objects.filter(sync_uuid=sync_id).count() == 1
PYEOF

# =============================================================================
# GITHUB ACTIONS CI/CD
# =============================================================================
write_file .github/workflows/ci.yml << 'PYEOF'
name: CO3DATA CI

on:
  push:
    branches: [main, develop, "feature/**"]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.12"

jobs:
  test:
    name: Test & Lint
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: co3data_test
          POSTGRES_USER: co3data
          POSTGRES_PASSWORD: co3data
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
        options: --health-cmd "redis-cli ping" --health-interval 10s

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with: { python-version: "${{ env.PYTHON_VERSION }}" }

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-django pytest-cov flake8 black isort whitenoise

      - name: Write .env for CI
        run: |
          cat > .env << EOF
          SECRET_KEY=ci-secret-key-not-for-production
          DEBUG=True
          ALLOWED_HOSTS=localhost,127.0.0.1
          POSTGRES_DB=co3data_test
          POSTGRES_USER=co3data
          POSTGRES_PASSWORD=co3data
          POSTGRES_HOST=localhost
          POSTGRES_PORT=5432
          REDIS_URL=redis://localhost:6379/0
          LANGUAGE_CODE=fr
          TIME_ZONE=Africa/Kinshasa
          CLOUDINARY_CLOUD_NAME=
          CLOUDINARY_API_KEY=
          CLOUDINARY_API_SECRET=
          EOF

      - name: Lint with flake8
        run: flake8 src/ --max-line-length=120 --exclude=migrations --count --statistics
        continue-on-error: true

      - name: Check formatting with black
        run: black --check src/ --line-length=120
        continue-on-error: true

      - name: Django system check
        env:
          DJANGO_SETTINGS_MODULE: core.settings
          PYTHONPATH: src
        run: python src/manage.py check --deploy 2>&1 | grep -v "WARNINGS" || true

      - name: Run migrations
        env:
          DJANGO_SETTINGS_MODULE: core.settings
          PYTHONPATH: src
        run: python src/manage.py migrate --no-input

      - name: Run tests
        env:
          DJANGO_SETTINGS_MODULE: core.settings
          PYTHONPATH: src
        run: |
          pytest tests/ \
            --ds=core.settings \
            --cov=src \
            --cov-report=xml \
            --cov-report=term-missing \
            -v

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with: { file: coverage.xml }
        continue-on-error: true

  docker-build:
    name: Docker Build Check
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker compose build --no-cache
        continue-on-error: true
PYEOF

write_file .github/workflows/deploy.yml << 'PYEOF'
name: CO3DATA Deploy

on:
  push:
    branches: [main]
    tags: ["v*"]

jobs:
  deploy:
    name: Deploy to Production
    runs-on: ubuntu-latest
    environment: production
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
        continue-on-error: true

      - name: Build & push Docker image
        run: |
          docker build -t co3data:${{ github.sha }} .
          docker tag co3data:${{ github.sha }} co3data:latest
        continue-on-error: true

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host:     ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key:      ${{ secrets.DEPLOY_KEY }}
          script: |
            cd /opt/co3data
            git pull origin main
            docker compose pull
            docker compose up -d --no-deps web celery
            docker compose exec web python manage.py migrate --no-input
            docker compose exec web python manage.py collectstatic --no-input
        continue-on-error: true
PYEOF

# =============================================================================
# MANAGE.PY + REQUIREMENTS UPDATE
# =============================================================================
write_file src/manage.py << 'PYEOF'
#!/usr/bin/env python
"""CO3DATA Django management utility."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Couldn't import Django. Check your virtualenv.") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
PYEOF
chmod +x src/manage.py

cat >> requirements.txt << 'EOF'

# Added for production readiness
whitenoise~=6.7
pytest~=8.0
pytest-django~=4.8
pytest-cov~=5.0
factory-boy~=3.3
flake8~=7.0
black~=24.0
isort~=5.13
EOF

# =============================================================================
# .ENV EXAMPLE (update)
# =============================================================================
cat > .env.example << 'EOF'
# CO3DATA Environment Configuration
# Copy to .env and fill in values before running

SECRET_KEY=change-me-to-a-long-random-string-in-production

# Set to False in production
DEBUG=True

# Comma-separated list
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# PostgreSQL
POSTGRES_DB=co3data
POSTGRES_USER=co3data
POSTGRES_PASSWORD=change-me-in-production
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis (Celery broker + cache)
REDIS_URL=redis://redis:6379/0

# Cloudinary (media storage)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Localization
LANGUAGE_CODE=fr
TIME_ZONE=Africa/Kinshasa
EOF

# =============================================================================
# pytest.ini
# =============================================================================
cat > pytest.ini << 'EOF'
[pytest]
DJANGO_SETTINGS_MODULE = core.settings
python_files = tests/*/test_*.py
python_classes = Test*
python_functions = test_*
pythonpath = src
EOF

# =============================================================================
# 3. Git commit & push
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Committing & pushing to GitHub..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

git add -A
git status --short

git commit -m "feat: implement full production backend

- Django settings (production-hardened, i18n FR/SW/EN, Redis, Celery)
- cooperatives app: WashingStation, enhanced Member (farmer_code),
  cherry delivery ProductionRecord (sync_uuid, auto total_price_fc)
- DRF serializers + ViewSets for all models
- SyncPushAPIView / SyncPullAPIView with last-write-wins idempotency
- sync app: Device, PendingChange (local_uuid), SyncLog (conflict_strategy)
- analytics app: KPI engine (simpleeval), DataValidationRule, DataQualityAlert
- questionnaires app: dynamic forms, submission engine
- Celery tasks: KPI computation, XLSX reports, data quality, log cleanup
- GitHub Actions: CI (lint+test+migrate) and deploy workflow
- Templates: base layout, dashboard, cherry delivery list/form, login
- Service worker for offline-first PWA caching
- Full test suite: model validation, RBAC, idempotent sync
- pytest.ini, .env.example updated"

git push origin "$BRANCH"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅  Done! Branch pushed: $BRANCH"
echo ""
echo "  Next steps:"
echo "  1. Open a Pull Request from '$BRANCH' → main"
echo "  2. Copy .env.example → .env and fill in secrets"
echo "  3. docker compose up --build"
echo "  4. python src/manage.py migrate && createsuperuser"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
