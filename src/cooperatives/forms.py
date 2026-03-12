from decimal import Decimal

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Member, Cooperative, ProductionRecord, WashingStation


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
