from rest_framework import serializers
from .models import (
    Cooperative, Member, Farm, ProductionRecord,
    WashingStation, FinancialRecord, Buyer,
    CooperativeCertificate, CooperativeSale
)

class CooperativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cooperative
        fields = '__all__'

class WashingStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WashingStation
        fields = '__all__'

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = '__all__'

class FarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = '__all__'

class ProductionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionRecord
        fields = '__all__'

class FinancialRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialRecord
        fields = '__all__'

class BuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = '__all__'

class CooperativeCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CooperativeCertificate
        fields = '__all__'

class CooperativeSaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CooperativeSale
        fields = '__all__'
