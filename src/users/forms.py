from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import Region, User


class UserProfileForm(forms.ModelForm):
    """Form for users to update their own profile."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "preferred_language", "profile_picture"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "preferred_language": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "first_name": _("Prénom"),
            "last_name": _("Nom"),
            "email": _("Email"),
            "phone_number": _("Numéro de téléphone"),
            "preferred_language": _("Langue préférée"),
        }


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            "username", "first_name", "last_name", "email",
            "role", "region", "cooperative", "phone_number", "preferred_language",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["region"].queryset = Region.objects.filter(country_code="CD")
        for field in self.fields.values():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput)):
                field.widget.attrs["class"] = "form-control"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "email",
            "role", "region", "cooperative", "phone_number", "preferred_language",
            "is_active", "force_password_change",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["region"].queryset = Region.objects.filter(country_code="CD")
        for field in self.fields.values():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput)):
                field.widget.attrs["class"] = "form-control"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
