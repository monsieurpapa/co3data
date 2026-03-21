# src/cooperatives/serializers.py
from rest_framework import serializers
from .models import Cooperative, Member, SACCOFinancialSummary, LoanAccount, SavingsAccount


class CooperativeSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source="region.name", read_only=True)

    class Meta:
        model = Cooperative
        fields = [
            "id", "name", "registration_number", "type", "status",
            "sector", "region", "region_name", "physical_address",
            "phone", "email", "establishment_date",
            "mambu_encoded_key", "updated_at",
        ]


class MemberSerializer(serializers.ModelSerializer):
    cooperative_name = serializers.CharField(source="cooperative.name", read_only=True)

    class Meta:
        model = Member
        fields = [
            "id", "cooperative", "cooperative_name",
            "first_name", "last_name", "member_id", "national_id",
            "date_of_birth", "gender", "age_group",
            "is_youth", "is_marginalized", "is_board_member",
            "phone_number", "email", "date_joined", "is_active",
        ]


class SACCOFinancialSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = SACCOFinancialSummary
        fields = "__all__"
        read_only_fields = [
            "submitted_by", "submitted_at", "is_verified", "verified_by",
            "kpi_delinquency_rate", "kpi_liquidity_ratio", "kpi_capital_adequacy",
            "kpi_roa", "kpi_cost_per_borrower", "kpi_portfolio_yield",
            "kpi_operational_self_sufficiency",
            "kpi_youth_participation_rate", "kpi_female_participation_rate",
        ]


class LoanAccountSerializer(serializers.ModelSerializer):
    member_name = serializers.SerializerMethodField()

    class Meta:
        model = LoanAccount
        fields = "__all__"

    def get_member_name(self, obj):
        return f"{obj.member.first_name} {obj.member.last_name}"


class SavingsAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsAccount
        fields = "__all__"