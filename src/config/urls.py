"""
URL configuration for the Accounting System.

Root routing: admin, allauth, i18n, budget, reporting, users,
organization, cashflow, and accounting (root namespace).
See docs/API.md for full URL reference.

Custom error pages: 403.html, 404.html, 500.html with views in config.views.
Handlers use referrer for "Go back" navigation. Test URLs: /error/403/, /error/404/, /error/500/
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

from config.views import (
    custom_permission_denied,
    custom_page_not_found,
    custom_server_error,
    error_page_403,
    error_page_404,
    error_page_500,
)

from django.views.generic import RedirectView

def health_check(request):
    return JsonResponse({"status": "ok"}, status=200)

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('', RedirectView.as_view(pattern_name='analytics:dashboard', permanent=False)),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('users/', include(('users.urls', 'users'), namespace='users')),
    path('cooperatives/', include(('cooperatives.urls', 'cooperatives'), namespace='cooperatives')),
    path('analytics/', include(('analytics.urls', 'analytics'), namespace='analytics')),
    path('questionnaires/', include(('questionnaires.urls', 'questionnaires'), namespace='questionnaires')),
    path('sync/', include(('sync.urls', 'sync'), namespace='sync')),

    # Error page URLs (for testing and direct access; handlers used when errors occur)
    path('error/404/', error_page_404),
    path('error/403/', error_page_403),
    path('error/500/', error_page_500),
]

handler403 = custom_permission_denied
handler404 = custom_page_not_found
handler500 = custom_server_error
