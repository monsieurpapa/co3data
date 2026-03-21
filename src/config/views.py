"""
Custom error page views for 403, 404, and 500.

Renders error templates with referrer_url so navigation can take users
back to the previous page. Used as handler403, handler404, handler500
in config.urls. Also exposed at /error/403/, /error/404/, /error/500/
for testing and direct access.
"""
from urllib.parse import urlparse

from django.shortcuts import render
from django.http import HttpResponse


def health_check(request):
    """Minimal endpoint for container health probes."""
    return HttpResponse("OK", status=200)


def _get_safe_referrer(request):
    """
    Return HTTP_REFERER only if it is from the same host to avoid open redirects.
    """
    referrer = request.META.get("HTTP_REFERER")
    if not referrer:
        return None
    try:
        referrer_netloc = urlparse(referrer).netloc.split(":")[0]
        host = request.get_host().split(":")[0]
        if referrer_netloc and referrer_netloc == host:
            return referrer
    except Exception:
        pass
    return None


def custom_page_not_found(request, exception=None):
    """Handler for 404: render 404.html with request path and referrer."""
    context = {
        "request_path": getattr(request, "path", ""),
        "referrer_url": _get_safe_referrer(request),
    }
    return render(request, "404.html", context, status=404)


def custom_permission_denied(request, exception=None):
    """Handler for 403: render 403.html with exception message and referrer."""
    context = {
        "exception": str(exception) if exception else None,
        "referrer_url": _get_safe_referrer(request),
    }
    return render(request, "403.html", context, status=403)


def custom_server_error(request):
    """Handler for 500: render 500.html with referrer."""
    context = {
        "referrer_url": _get_safe_referrer(request),
    }
    return render(request, "500.html", context, status=500)


def error_page_404(request):
    """Explicit URL view for 404 (e.g. testing at /error/404/)."""
    return custom_page_not_found(request)


def error_page_403(request):
    """Explicit URL view for 403 (e.g. testing at /error/403/)."""
    return custom_permission_denied(request)


def error_page_500(request):
    """Explicit URL view for 500 (e.g. testing at /error/500/)."""
    return custom_server_error(request)
