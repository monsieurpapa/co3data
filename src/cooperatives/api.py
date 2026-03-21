from rest_framework import viewsets
from .models import (
    Cooperative, Member, SACCOFinancialSummary, 
    LoanAccount, SavingsAccount, BoardMember, TrainingRecord
)
from .serializers import (
    CooperativeSerializer, MemberSerializer, 
    SACCOFinancialSummarySerializer, LoanAccountSerializer, 
    SavingsAccountSerializer
)

class CooperativeViewSet(viewsets.ModelViewSet):
    queryset = Cooperative.objects.all()
    serializer_class = CooperativeSerializer

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

class SACCOFinancialSummaryViewSet(viewsets.ModelViewSet):
    queryset = SACCOFinancialSummary.objects.all()
    serializer_class = SACCOFinancialSummarySerializer

class LoanAccountViewSet(viewsets.ModelViewSet):
    queryset = LoanAccount.objects.all()
    serializer_class = LoanAccountSerializer

class SavingsAccountViewSet(viewsets.ModelViewSet):
    queryset = SavingsAccount.objects.all()
    serializer_class = SavingsAccountSerializer

class BoardMemberViewSet(viewsets.ModelViewSet):
    queryset = BoardMember.objects.all()
    from rest_framework import serializers
    class BoardMemberSerializer(serializers.ModelSerializer):
        class Meta:
            model = BoardMember
            fields = "__all__"
    serializer_class = BoardMemberSerializer

class TrainingRecordViewSet(viewsets.ModelViewSet):
    queryset = TrainingRecord.objects.all()
    from rest_framework import serializers
    class TrainingRecordSerializer(serializers.ModelSerializer):
        class Meta:
            model = TrainingRecord
            fields = "__all__"
    serializer_class = TrainingRecordSerializer
