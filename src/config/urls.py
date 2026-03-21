from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from config.views import health_check

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("account/", include("allauth.urls")),
    path("", include("analytics.urls", namespace="analytics")),
    path("cooperatives/", include("cooperatives.urls", namespace="cooperatives")),
    path("users/", include("users.urls", namespace="users")),
    path("questionnaires/", include("questionnaires.urls", namespace="questionnaires")),
    prefix_default_language=False,
)

urlpatterns += [
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/sync/", include("sync.urls", namespace="sync")),
    path("api-auth/", include("rest_framework.urls")),
    path("health/", health_check, name="health_check"),
    # path("account/", include(("two_factor.urls", "two_factor"))),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)