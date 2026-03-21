from rest_framework import serializers
from .models import Device, PendingChange, SyncConflict

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = "__all__"

class PendingChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingChange
        fields = "__all__"

class SyncConflictSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncConflict
        fields = "__all__"

class SyncPullSerializer(serializers.Serializer):
    """
    Serializer for the /api/sync/pull/ response.
    Note: The view currently builds the response manually.
    """
    server_time = serializers.DateTimeField()
    cooperatives = serializers.ListField()
    members = serializers.ListField()
    conflicts = serializers.ListField()
