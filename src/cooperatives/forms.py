from decimal import Decimal

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    Member,
    Cooperative,
    ProductionRecord,
    FinancialRecord,
    WashingStation,
    Buyer,
    CooperativeCertificate,
    CooperativeSale,
)


class CooperativeForm(forms.ModelForm):
    class Meta:
        model = Cooperative
        fields = ["name", "registration_number", "type", "establishment_date", "contact_person", "address"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "registration_number": forms.TextInput(attrs={"class": "form-control"}),
            "type": forms.Select(attrs={"class": "form-select"}),
            "establishment_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "contact_person": forms.Select(attrs={"class": "form-select"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            "cooperative",
            "first_name",
            "last_name",
            "member_id",
            "gender",
            "age_group",
            "phone_number",
            "territory",
            "groupement",
            "village",
            "subvillage",
            "farmer_code",
            "is_marginalized",
            "is_board_member",
            "board_role",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "First Name"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Last Name"}),
            "member_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "Member ID"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "age_group": forms.Select(attrs={"class": "form-select"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone Number"}),
            "territory": forms.TextInput(attrs={"class": "form-control", "placeholder": "Territory"}),
            "groupement": forms.TextInput(attrs={"class": "form-control", "placeholder": "Groupement"}),
            "village": forms.TextInput(attrs={"class": "form-control", "placeholder": "Village"}),
            "subvillage": forms.TextInput(attrs={"class": "form-control", "placeholder": "Sub-village / Localité"}),
            "farmer_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "TCC BMB 009"}),
            "board_role": forms.Select(attrs={"class": "form-select"}),
            "cooperative": forms.Select(attrs={"class": "form-select"}),
            "is_marginalized": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_board_member": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_board_member = cleaned_data.get("is_board_member")
        board_role = cleaned_data.get("board_role")

        if is_board_member and not board_role:
            self.add_error("board_role", _("Board role is required for board members."))

        return cleaned_data


class MemberChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if obj.farmer_code:
            return f"{obj.farmer_code} – {obj.first_name} {obj.last_name}"
        return f"{obj.first_name} {obj.last_name} ({obj.member_id})"


class CherryDeliveryForm(forms.ModelForm):
    station = forms.ModelChoiceField(
        queryset=WashingStation.objects.filter(is_active=True),
        label=_("Washing station"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    member = MemberChoiceField(
        queryset=Member.objects.all(),
        label=_("Farmer (by code)"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = ProductionRecord
        fields = [
            "station",
            "member",
            "purchase_date",
            "reception_date",
            "quantity_kg",
            "receipt_number",
            "base_price_fc",
            "total_price_fc",
            "exchange_rate_fc_usd",
            "cherry_register_number",
            "delivery_report_number",
        ]
        widgets = {
            "purchase_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "reception_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "quantity_kg": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "receipt_number": forms.TextInput(attrs={"class": "form-control"}),
            "base_price_fc": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "total_price_fc": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "exchange_rate_fc_usd": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "cherry_register_number": forms.TextInput(attrs={"class": "form-control"}),
            "delivery_report_number": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {
            "purchase_date": _("Date d'achat"),
            "reception_date": _("Date de réception à la station"),
            "quantity_kg": _("Quantité cerise délivrée (kg)"),
            "receipt_number": _("N° reçu de paiement"),
            "base_price_fc": _("Prix de base (FC/unité)"),
            "total_price_fc": _("Prix total (FC)"),
            "exchange_rate_fc_usd": _("Taux de change FC/USD"),
            "cherry_register_number": _("N° du registre de cerises"),
            "delivery_report_number": _("N° du rapport de livraison"),
        }

    def __init__(self, *args, **kwargs):
        cooperative = kwargs.pop("cooperative", None)
        super().__init__(*args, **kwargs)
        if cooperative is not None:
            self.fields["station"].queryset = WashingStation.objects.filter(
                cooperative=cooperative, is_active=True
            )
            self.fields["member"].queryset = Member.objects.filter(cooperative=cooperative)

    def clean_total_price_fc(self):
        total = self.cleaned_data.get("total_price_fc")
        quantity = self.cleaned_data.get("quantity_kg")
        base_price = self.cleaned_data.get("base_price_fc")

        if quantity is not None and base_price is not None:
            calculated = (Decimal(quantity) * Decimal(base_price)).quantize(Decimal("0.01"))
            return calculated
        return total

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.record_type = ProductionRecord.RECORD_TYPE_CHERRY
        if instance.crop_type is None:
            instance.crop_type = "coffee"
        if instance.total_price_fc is None and instance.base_price_fc is not None and instance.quantity_kg is not None:
            instance.total_price_fc = instance.quantity_kg * instance.base_price_fc
        if commit:
            instance.save()
        return instance


class ProductionRecordForm(forms.ModelForm):
    """Form for generic production records (coffee/cocoa harvests)"""
    class Meta:
        model = ProductionRecord
        fields = [
            "farm",
            "crop_type",
            "harvest_date",
            "quantity_kg",
            "quality_grade",
        ]
        widgets = {
            "farm": forms.Select(attrs={"class": "form-select"}),
            "crop_type": forms.Select(attrs={"class": "form-select"}),
            "harvest_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "quantity_kg": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "quality_grade": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {
            "farm": _("Exploitation"),
            "crop_type": _("Type de culture"),
            "harvest_date": _("Date de récolte"),
            "quantity_kg": _("Quantité (kg)"),
            "quality_grade": _("Grade de qualité"),
        }

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get("quantity_kg")
        harvest_date = cleaned_data.get("harvest_date")
        
        if quantity is not None and quantity <= 0:
            self.add_error("quantity_kg", _("La quantité doit être supérieure à zéro."))
        
        if harvest_date:
            from django.utils import timezone
            if harvest_date > timezone.now().date():
                self.add_error("harvest_date", _("La date de récolte ne peut pas être dans le futur."))
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.record_type = ProductionRecord.RECORD_TYPE_GENERIC
        if commit:
            instance.save()
        return instance


class FinancialRecordForm(forms.ModelForm):
    """Form for creating and editing financial records"""
    class Meta:
        model = FinancialRecord
        fields = [
            "cooperative",
            "transaction_date",
            "transaction_type",
            "amount",
            "description",
        ]
        widgets = {
            "cooperative": forms.Select(attrs={"class": "form-select"}),
            "transaction_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "transaction_type": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
        labels = {
            "cooperative": _("Coopérative"),
            "transaction_date": _("Date de transaction"),
            "transaction_type": _("Type de transaction"),
            "amount": _("Montant (FC)"),
            "description": _("Description"),
        }

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        transaction_date = cleaned_data.get("transaction_date")
        
        if amount is not None and amount <= 0:
            self.add_error("amount", _("Le montant doit être supérieur à zéro."))
        
        if transaction_date:
            from django.utils import timezone
            if transaction_date > timezone.now().date():
                self.add_error("transaction_date", _("La date de transaction ne peut pas être dans le futur."))
        
        return cleaned_data


class BuyerForm(forms.ModelForm):
    class Meta:
        model = Buyer
        fields = ["name", "country", "email", "phone"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }


class WashingStationForm(forms.ModelForm):
    class Meta:
        model = WashingStation
        fields = ["cooperative", "name", "village", "latitude", "longitude", "is_active"]
        widgets = {
            "cooperative": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "village": forms.TextInput(attrs={"class": "form-control"}),
            "latitude": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001"}),
            "longitude": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "cooperative": _("Coopérative"),
            "name": _("Nom de la station"),
            "village": _("Village"),
            "latitude": _("Latitude"),
            "longitude": _("Longitude"),
            "is_active": _("Active"),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user is not None and not getattr(user, "is_superuser", False):
            region = getattr(user, "region", None)
            if region:
                self.fields["cooperative"].queryset = Cooperative.objects.filter(region=region).order_by("name")
            else:
                self.fields["cooperative"].queryset = Cooperative.objects.none()


class CooperativeCertificateForm(forms.ModelForm):
    class Meta:
        model = CooperativeCertificate
        fields = ["name", "issuer", "issued_date", "expires_date", "document", "notes"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "issuer": forms.TextInput(attrs={"class": "form-control"}),
            "issued_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "expires_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "document": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class CooperativeSaleForm(forms.ModelForm):
    class Meta:
        model = CooperativeSale
        fields = [
            "buyer",
            "year",
            "grade",
            "destination_country",
            "quantity_kg",
            "price_per_kg",
            "arrival_date",
            "notes",
        ]
        widgets = {
            "buyer": forms.Select(attrs={"class": "form-select"}),
            "year": forms.NumberInput(attrs={"class": "form-control", "min": 2000, "max": 2100}),
            "grade": forms.TextInput(attrs={"class": "form-control"}),
            "destination_country": forms.TextInput(attrs={"class": "form-control"}),
            "quantity_kg": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "price_per_kg": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "arrival_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get("quantity_kg")
        if quantity is not None and quantity <= 0:
            self.add_error("quantity_kg", _("La quantité doit être supérieure à zéro."))
        return cleaned_data

