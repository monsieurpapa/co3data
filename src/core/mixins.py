from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet

class RegionalAccessMixin(LoginRequiredMixin):
    """
    Ensures that the user can only access objects belonging to their region.
    Superusers and users without a region (if allowed) bypass this.
    """
    region_field = 'region' # Default field name on the model

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Superusers see everything
        if user.is_superuser:
            return queryset
            
        # If user has no region, they see nothing by default (strict RBAC)
        if not user.region:
            return queryset.none()
            
        # Filter by region
        filter_kwargs = {self.region_field: user.region}
        return queryset.filter(**filter_kwargs)

class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Restricts the view to users with one of the required roles.
    Superusers bypass the role check.
    """
    required_roles = []

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        return user.role in self.required_roles

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You do not have the required role to access this page.")
        return super().handle_no_permission()

class RegionalFormMixin:
    """
    Automatically assigns the user's region to the object on save.
    Used for CreateView and UpdateView.
    """
    region_field = 'region'

    def form_valid(self, form):
        user = self.request.user
        if not user.is_superuser and user.region:
            setattr(form.instance, self.region_field, user.region)
        return super().form_valid(form)
