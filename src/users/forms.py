from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _

from .models import User, Region


class UserForm(forms.ModelForm):
    """Form for creating and editing users"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=False,
        help_text=_("Leave blank to keep existing password")
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=False,
        label=_("Confirm Password"),
        help_text=_("Enter the same password as before, for verification")
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'region', 'phone_number', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={"class": "form-control"}),
            'email': forms.EmailInput(attrs={"class": "form-control"}),
            'first_name': forms.TextInput(attrs={"class": "form-control"}),
            'last_name': forms.TextInput(attrs={"class": "form-control"}),
            'role': forms.Select(attrs={"class": "form-select"}),
            'region': forms.Select(attrs={"class": "form-select"}),
            'phone_number': forms.TextInput(attrs={"class": "form-control"}),
            'is_active': forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            'username': _("Nom d'utilisateur"),
            'email': _("Email"),
            'first_name': _("Prénom"),
            'last_name': _("Nom"),
            'role': _("Rôle"),
            'region': _("Région"),
            'phone_number': _("Numéro de téléphone"),
            'is_active': _("Actif"),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password != password_confirm:
            self.add_error('password_confirm', _("Les mots de passe ne correspondent pas."))

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class UserCreationFormCustom(UserCreationForm):
    """Custom user creation form"""
    role = forms.ChoiceField(
        choices=User.USER_ROLES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Rôle")
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Région")
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label=_("Numéro de téléphone")
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'region', 'phone_number', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={"class": "form-control"}),
            'email': forms.EmailInput(attrs={"class": "form-control"}),
            'first_name': forms.TextInput(attrs={"class": "form-control"}),
            'last_name': forms.TextInput(attrs={"class": "form-control"}),
            'password1': forms.PasswordInput(attrs={"class": "form-control"}),
            'password2': forms.PasswordInput(attrs={"class": "form-control"}),
        }
        labels = {
            'username': _("Nom d'utilisateur"),
            'email': _("Email"),
            'first_name': _("Prénom"),
            'last_name': _("Nom"),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data.get('role', 'member')
        user.region = self.cleaned_data.get('region')
        user.phone_number = self.cleaned_data.get('phone_number')
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    """Form for users to update their own profile"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_picture', 'preferred_language']
        widgets = {
            'first_name': forms.TextInput(attrs={"class": "form-control"}),
            'last_name': forms.TextInput(attrs={"class": "form-control"}),
            'email': forms.EmailInput(attrs={"class": "form-control"}),
            'phone_number': forms.TextInput(attrs={"class": "form-control"}),
            'profile_picture': forms.FileInput(attrs={"class": "form-control"}),
            'preferred_language': forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            'first_name': _("Prénom"),
            'last_name': _("Nom"),
            'email': _("Email"),
            'phone_number': _("Numéro de téléphone"),
            'profile_picture': _("Photo de profil"),
            'preferred_language': _("Langue préférée"),
        }
