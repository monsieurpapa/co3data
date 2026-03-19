from rest_framework import viewsets
from .models import (
    Cooperative, Member, Farm, ProductionRecord,
    WashingStation, FinancialRecord, Buyer,
    CooperativeCertificate, CooperativeSale
)
from .serializers import (
    CooperativeSerializer, MemberSerializer, FarmSerializer, ProductionRecordSerializer,
    WashingStationSerializer, FinancialRecordSerializer, BuyerSerializer,
    CooperativeCertificateSerializer, CooperativeSaleSerializer
)

class CooperativeViewSet(viewsets.ModelViewSet):
    queryset = Cooperative.objects.all()
    serializer_class = CooperativeSerializer

class WashingStationViewSet(viewsets.ModelViewSet):
    queryset = WashingStation.objects.all()
    serializer_class = WashingStationSerializer

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

class FarmViewSet(viewsets.ModelViewSet):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer

class ProductionRecordViewSet(viewsets.ModelViewSet):
    queryset = ProductionRecord.objects.all()
    serializer_class = ProductionRecordSerializer

class FinancialRecordViewSet(viewsets.ModelViewSet):
    queryset = FinancialRecord.objects.all()
    serializer_class = FinancialRecordSerializer

class BuyerViewSet(viewsets.ModelViewSet):
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer

class CooperativeCertificateViewSet(viewsets.ModelViewSet):
    queryset = CooperativeCertificate.objects.all()
    serializer_class = CooperativeCertificateSerializer

class CooperativeSaleViewSet(viewsets.ModelViewSet):
    queryset = CooperativeSale.objects.all()
    serializer_class = CooperativeSaleSerializer
