from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

from .models import Organization
from .forms import OrganizationForm


def organization_settings(request):
    return HttpResponse('Organization settings placeholder')


# -----------------------------------------------------------------------------
# Admin organization management (superuser only)
# -----------------------------------------------------------------------------

def _staff_required(request):
    # Require superuser for organization admin actions
    if not request.user.is_superuser:
        raise PermissionDenied


@login_required
def organization_list(request):
    _staff_required(request)
    orgs = Organization.objects.all()
    return render(request, 'organization/organization_list.html', {'organizations': orgs})


@login_required
def organization_create(request):
    _staff_required(request)
    if request.method == 'POST':
        form = OrganizationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('organization:organization_list')
    else:
        form = OrganizationForm()
    return render(request, 'organization/organization_form.html', {'form': form, 'creating': True})


@login_required
def organization_update(request, uuid):
    _staff_required(request)
    org = get_object_or_404(Organization, uuid=uuid)
    if request.method == 'POST':
        form = OrganizationForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            return redirect('organization:organization_list')
    else:
        form = OrganizationForm(instance=org)
    return render(request, 'organization/organization_form.html', {'form': form, 'creating': False})


@login_required
def organization_delete(request, uuid):
    _staff_required(request)
    org = get_object_or_404(Organization, uuid=uuid)
    if request.method == 'POST':
        org.delete()
        return redirect('organization:organization_list')
    return render(request, 'organization/organization_confirm_delete.html', {'organization': org})
