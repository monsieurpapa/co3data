# src/cooperatives/forms.py
# ─────────────────────────────────────────────────────────────────────────────
# CoopData – Cooperative module forms (Eswatini / SUCOSA II)
# ─────────────────────────────────────────────────────────────────────────────
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    BoardMember,
    Cooperative,
    LoanAccount,
    Member,
    SACCOFinancialSummary,
    SavingsAccount,
    TrainingRecord,
)


class CooperativeForm(forms.ModelForm):
    class Meta:
        model = Cooperative
        fields = [
            "name", "registration_number", "type", "status", "sector",
            "region", "physical_address", "postal_address",
            "contact_person", "phone", "email", "website",
            "establishment_date", "registration_date", "apex_body",
            "mambu_encoded_key",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "registration_number": forms.TextInput(attrs={"class": "form-control"}),
            "type": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "sector": forms.TextInput(attrs={"class": "form-control"}),
            "region": forms.Select(attrs={"class": "form-select"}),
            "physical_address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "postal_address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "contact_person": forms.Select(attrs={"class": "form-select"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "+268..."}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(attrs={"class": "form-control"}),
            "establishment_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "registration_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "apex_body": forms.Select(attrs={"class": "form-select"}),
            "mambu_encoded_key": forms.TextInput(attrs={"class": "form-control font-monospace"}),
        }


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            "cooperative", "first_name", "last_name", "member_id",
            "national_id", "date_of_birth", "gender", "age_group",
            "is_youth", "is_marginalized", "is_board_member",
            "phone_number", "email", "physical_address",
            "is_active", "exit_date", "exit_reason",
        ]
        widgets = {
            "cooperative": forms.Select(attrs={"class": "form-select"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "member_id": forms.TextInput(attrs={"class": "form-control"}),
            "national_id": forms.TextInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "age_group": forms.Select(attrs={"class": "form-select"}),
            "is_youth": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_marginalized": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_board_member": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "+268..."}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "physical_address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "exit_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "exit_reason": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, cooperative=None, **kwargs):
        super().__init__(*args, **kwargs)
        if cooperative:
            self.fields["cooperative"].initial = cooperative
            self.fields["cooperative"].widget = forms.HiddenInput()

    def clean(self):
        cleaned = super().clean()
        # Auto-set is_youth based on age_group
        if cleaned.get("age_group") == "youth":
            cleaned["is_youth"] = True
        return cleaned


class SACCOFinancialSummaryForm(forms.ModelForm):
    """
    Data-entry form for a SACCO period-end financial report.
    KPI fields are read-only — computed by Celery after save.
    """

    class Meta:
        model = SACCOFinancialSummary
        fields = [
            "cooperative", "period_type", "period_start", "period_end",
            # Balance Sheet
            "total_assets", "total_liabilities", "total_equity",
            "share_capital", "retained_earnings",
            "total_savings", "total_deposits",
            # Loan Portfolio
            "gross_loan_portfolio", "loans_disbursed_period",
            "loan_repayments_received",
            "par_30_days", "par_90_days",
            "write_offs_period", "loan_loss_provisions",
            # Income Statement
            "interest_income", "fee_income", "other_income",
            "total_income", "operating_expenses",
            "interest_expense", "net_surplus",
            # Membership
            "total_members", "active_borrowers", "active_savers",
            "new_members_period", "female_members", "youth_members",
            "notes",
        ]
        widgets = {
            "cooperative": forms.Select(attrs={"class": "form-select"}),
            "period_type": forms.Select(attrs={"class": "form-select"}),
            "period_start": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "period_end": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply form-control class to all decimal/integer fields
        decimal_fields = [
            f.name for f in SACCOFinancialSummary._meta.fields
            if f.get_internal_type() in ("DecimalField", "PositiveIntegerField", "IntegerField")
            and f.name not in ("id",)
        ]
        for fname in decimal_fields:
            if fname in self.fields:
                self.fields[fname].widget.attrs.update({"class": "form-control text-end"})

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("period_start")
        end = cleaned.get("period_end")
        if start and end and end <= start:
            raise forms.ValidationError(_("Period end must be after period start."))
        # Basic sanity checks
        assets = cleaned.get("total_assets", 0) or 0
        liab = cleaned.get("total_liabilities", 0) or 0
        equity = cleaned.get("total_equity", 0) or 0
        if assets and abs(float(assets) - float(liab + equity)) > 1:
            self.add_error(
                "total_equity",
                _("Assets ≠ Liabilities + Equity. Please check your figures."),
            )
        return cleaned


class BoardMemberForm(forms.ModelForm):
    class Meta:
        model = BoardMember
        fields = [
            "cooperative", "member", "position",
            "term_start", "term_end", "gender", "is_youth", "is_active",
        ]
        widgets = {
            "cooperative": forms.Select(attrs={"class": "form-select"}),
            "member": forms.Select(attrs={"class": "form-select"}),
            "position": forms.Select(attrs={"class": "form-select"}),
            "term_start": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "term_end": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "is_youth": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class TrainingRecordForm(forms.ModelForm):
    class Meta:
        model = TrainingRecord
        fields = [
            "cooperative", "title", "training_date", "duration_hours",
            "provider", "topic",
            "total_participants", "female_participants", "youth_participants",
            "notes",
        ]
        widgets = {
            "cooperative": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "training_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "duration_hours": forms.NumberInput(attrs={"class": "form-control", "step": "0.5"}),
            "provider": forms.TextInput(attrs={"class": "form-control"}),
            "topic": forms.TextInput(attrs={"class": "form-control"}),
            "total_participants": forms.NumberInput(attrs={"class": "form-control"}),
            "female_participants": forms.NumberInput(attrs={"class": "form-control"}),
            "youth_participants": forms.NumberInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean(self):
        cleaned = super().clean()
        total = cleaned.get("total_participants", 0) or 0
        female = cleaned.get("female_participants", 0) or 0
        youth = cleaned.get("youth_participants", 0) or 0
        if female > total:
            self.add_error("female_participants", _("Cannot exceed total participants."))
        if youth > total:
            self.add_error("youth_participants", _("Cannot exceed total participants."))
        return cleaned


class LoanAccountForm(forms.ModelForm):
    class Meta:
        model = LoanAccount
        fields = [
            "member", "loan_id", "disbursement_date",
            "principal_amount", "interest_rate", "term_months",
            "outstanding_balance", "arrears_amount", "days_in_arrears",
            "status", "purpose", "maturity_date",
        ]
        widgets = {
            "member": forms.Select(attrs={"class": "form-select"}),
            "loan_id": forms.TextInput(attrs={"class": "form-control font-monospace"}),
            "disbursement_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "principal_amount": forms.NumberInput(attrs={"class": "form-control text-end"}),
            "interest_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
            "term_months": forms.NumberInput(attrs={"class": "form-control"}),
            "outstanding_balance": forms.NumberInput(attrs={"class": "form-control text-end"}),
            "arrears_amount": forms.NumberInput(attrs={"class": "form-control text-end"}),
            "days_in_arrears": forms.NumberInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "purpose": forms.TextInput(attrs={"class": "form-control"}),
            "maturity_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class SavingsAccountForm(forms.ModelForm):
    class Meta:
        model = SavingsAccount
        fields = [
            "member", "account_number", "account_type",
            "balance", "interest_rate", "opened_date", "is_active",
        ]
        widgets = {
            "member": forms.Select(attrs={"class": "form-select"}),
            "account_number": forms.TextInput(attrs={"class": "form-control font-monospace"}),
            "account_type": forms.Select(attrs={"class": "form-select"}),
            "balance": forms.NumberInput(attrs={"class": "form-control text-end"}),
            "interest_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
            "opened_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }