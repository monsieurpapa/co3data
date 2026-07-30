from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

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


class CooperativeScopedViewSet(viewsets.ModelViewSet):
    """Base ViewSet that scopes querysets to the requesting user's accessible cooperatives."""
    permission_classes = [IsAuthenticated]
    cooperative_lookup = "cooperative"  # ORM path from the model to Cooperative; "pk" for Cooperative itself

    def get_queryset(self):
        qs = super().get_queryset()
        coops = self.request.user.get_accessible_cooperatives()
        return qs.filter(**{f"{self.cooperative_lookup}__in": coops})


class CooperativeViewSet(CooperativeScopedViewSet):
    queryset = Cooperative.objects.all()
    serializer_class = CooperativeSerializer
    cooperative_lookup = "pk"


class WashingStationViewSet(CooperativeScopedViewSet):
    queryset = WashingStation.objects.all()
    serializer_class = WashingStationSerializer
    cooperative_lookup = "cooperative"


class MemberViewSet(CooperativeScopedViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    cooperative_lookup = "cooperative"


class FarmViewSet(CooperativeScopedViewSet):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer
    cooperative_lookup = "member__cooperative"


class ProductionRecordViewSet(CooperativeScopedViewSet):
    queryset = ProductionRecord.objects.all()
    serializer_class = ProductionRecordSerializer

    def get_queryset(self):
        # cherry deliveries link via `member`; generic records link via `farm.member` — cover both.
        coops = self.request.user.get_accessible_cooperatives()
        return ProductionRecord.objects.filter(
            Q(member__cooperative__in=coops) | Q(farm__member__cooperative__in=coops)
        ).distinct()


class FinancialRecordViewSet(CooperativeScopedViewSet):
    queryset = FinancialRecord.objects.all()
    serializer_class = FinancialRecordSerializer
    cooperative_lookup = "cooperative"


class BuyerViewSet(viewsets.ModelViewSet):
    # Buyers aren't scoped to a single cooperative — visible to any authenticated user.
    permission_classes = [IsAuthenticated]
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer


class CooperativeCertificateViewSet(CooperativeScopedViewSet):
    queryset = CooperativeCertificate.objects.all()
    serializer_class = CooperativeCertificateSerializer
    cooperative_lookup = "cooperative"


class CooperativeSaleViewSet(CooperativeScopedViewSet):
    queryset = CooperativeSale.objects.all()
    serializer_class = CooperativeSaleSerializer
    cooperative_lookup = "cooperative"
