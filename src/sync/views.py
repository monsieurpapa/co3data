# src/sync/views.py
# ─────────────────────────────────────────────────────────────────────────────
# CoopData – Offline Synchronisation API views
# TOR §2   – offline functionality with synchronisation capabilities
# TOR §3.3 – offline data entry with syncing once internet is available
# ─────────────────────────────────────────────────────────────────────────────
import json
from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from users.models import AuditLog

from .models import Device, PendingChange, SyncConflict, SyncLog
from .serializers import (
    DeviceSerializer,
    PendingChangeSerializer,
    SyncConflictSerializer,
    SyncPullSerializer,
)


# ─────────────────────────────────────────────────────────────────────────────
# Device Registration
# ─────────────────────────────────────────────────────────────────────────────

class DeviceRegisterView(APIView):
    """
    POST /api/sync/devices/register/
    Register a new device or update an existing one.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device_id = request.data.get("device_id")
        if not device_id:
            return Response(
                {"error": "device_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        device, created = Device.objects.update_or_create(
            device_id=device_id,
            defaults={
                "user": request.user,
                "device_name": request.data.get("device_name", ""),
                "app_version": request.data.get("app_version", ""),
                "platform": request.data.get("platform", ""),
                "last_seen_at": timezone.now(),
                "is_active": True,
            },
        )
        return Response(
            {
                "device_id": device.device_id,
                "created": created,
                "last_sync_at": device.last_sync_at,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Push (device → server)
# ─────────────────────────────────────────────────────────────────────────────

class SyncPushView(APIView):
    """
    POST /api/sync/push/
    Device pushes its pending changes to the server.
    Body: { device_id, changes: [ {model, object_id, change_type, payload, local_timestamp} ] }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device_id = request.data.get("device_id")
        changes = request.data.get("changes", [])
        if not device_id:
            return Response({"error": "device_id required."}, status=400)

        device = Device.objects.filter(device_id=device_id, user=request.user).first()
        if not device:
            return Response({"error": "Device not registered."}, status=404)

        results = {"accepted": [], "conflicts": [], "errors": []}
        log = SyncLog.objects.create(device=device, connection_type=request.data.get("connection_type", ""))

        with transaction.atomic():
            for change_data in changes:
                try:
                    result = _apply_change(device, change_data, request.user)
                    if result["status"] == "conflict":
                        results["conflicts"].append(result)
                    else:
                        results["accepted"].append(change_data.get("object_id"))
                except Exception as exc:
                    results["errors"].append({
                        "object_id": change_data.get("object_id"),
                        "error": str(exc),
                    })

        log.sync_end_time = timezone.now()
        log.changes_uploaded = len(results["accepted"])
        log.conflicts_detected = len(results["conflicts"])
        log.status = (
            SyncLog.STATUS_FAILED if not results["accepted"] and results["errors"]
            else SyncLog.STATUS_PARTIAL if results["errors"] or results["conflicts"]
            else SyncLog.STATUS_SUCCESS
        )
        log.save(update_fields=["sync_end_time", "changes_uploaded", "conflicts_detected", "status"])

        device.last_sync_at = timezone.now()
        device.last_seen_at = timezone.now()
        device.save(update_fields=["last_sync_at", "last_seen_at"])

        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.ACTION_SYNC,
            description=f"Sync push: {len(results['accepted'])} accepted, "
                        f"{len(results['conflicts'])} conflicts, {len(results['errors'])} errors",
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        return Response(results, status=status.HTTP_200_OK)


def _apply_change(device: Device, change_data: dict, user) -> dict:
    """
    Apply a single PendingChange to the database.
    Returns {"status": "accepted"|"conflict", ...}
    """
    model_label = change_data.get("model")          # e.g. "cooperatives.Member"
    object_id = change_data.get("object_id")
    change_type = change_data.get("change_type")
    payload = change_data.get("payload", {})
    local_ts_str = change_data.get("local_timestamp")

    try:
        local_ts = datetime.fromisoformat(local_ts_str)
    except Exception:
        local_ts = timezone.now()

    app_label, model_name = model_label.split(".")
    ct = ContentType.objects.get(app_label=app_label, model=model_name.lower())
    Model = ct.model_class()

    # Record the pending change
    pending = PendingChange.objects.create(
        device=device,
        content_type=ct,
        object_id=object_id or 0,
        change_type=change_type,
        payload=payload,
        local_timestamp=local_ts,
    )

    if change_type == PendingChange.CHANGE_CREATE:
        try:
            obj = Model.objects.create(**_sanitize_payload(Model, payload))
            pending.state = PendingChange.STATE_SYNCED
            pending.save(update_fields=["state"])
            return {"status": "accepted", "server_id": obj.pk}
        except Exception as exc:
            pending.state = PendingChange.STATE_FAILED
            pending.last_error = str(exc)
            pending.save(update_fields=["state", "last_error"])
            raise

    elif change_type == PendingChange.CHANGE_UPDATE:
        try:
            obj = Model.objects.get(pk=object_id)
            # Conflict detection: has server updated since device last synced?
            if hasattr(obj, "updated_at") and obj.updated_at:
                if obj.updated_at > local_ts:
                    # Conflict!
                    server_snapshot = {
                        f.name: str(getattr(obj, f.name))
                        for f in Model._meta.fields
                    }
                    conflict = SyncConflict.objects.create(
                        pending_change=pending,
                        server_snapshot=server_snapshot,
                        device_snapshot=payload,
                        conflicting_fields=list(
                            set(payload.keys()) & set(server_snapshot.keys())
                        ),
                    )
                    pending.state = PendingChange.STATE_CONFLICT
                    pending.save(update_fields=["state"])
                    return {"status": "conflict", "conflict_id": conflict.pk, "object_id": object_id}
            # No conflict – apply
            for field, value in _sanitize_payload(Model, payload).items():
                setattr(obj, field, value)
            obj.save()
            pending.state = PendingChange.STATE_SYNCED
            pending.save(update_fields=["state"])
            return {"status": "accepted"}
        except Model.DoesNotExist:
            pending.state = PendingChange.STATE_FAILED
            pending.last_error = "Object not found on server"
            pending.save(update_fields=["state", "last_error"])
            raise ValueError(f"{model_label} pk={object_id} not found")

    elif change_type == PendingChange.CHANGE_DELETE:
        try:
            Model.objects.filter(pk=object_id).delete()
            pending.state = PendingChange.STATE_SYNCED
            pending.save(update_fields=["state"])
            return {"status": "accepted"}
        except Exception as exc:
            pending.state = PendingChange.STATE_FAILED
            pending.last_error = str(exc)
            pending.save(update_fields=["state", "last_error"])
            raise

    raise ValueError(f"Unknown change_type: {change_type}")


def _sanitize_payload(Model, payload: dict) -> dict:
    """Strip keys that don't correspond to writable model fields."""
    field_names = {f.name for f in Model._meta.fields if not f.primary_key}
    return {k: v for k, v in payload.items() if k in field_names}


# ─────────────────────────────────────────────────────────────────────────────
# Pull (server → device)
# ─────────────────────────────────────────────────────────────────────────────

class SyncPullView(APIView):
    """
    GET /api/sync/pull/?device_id=xxx&since=ISO_DATETIME
    Returns all records updated since the device's last sync.
    Scoped to the user's accessible data.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        device_id = request.query_params.get("device_id")
        since_str = request.query_params.get("since")
        if not device_id:
            return Response({"error": "device_id required."}, status=400)

        device = Device.objects.filter(device_id=device_id, user=request.user).first()
        if not device:
            return Response({"error": "Device not registered."}, status=404)

        since = None
        if since_str:
            try:
                since = datetime.fromisoformat(since_str)
            except ValueError:
                return Response({"error": "Invalid since datetime."}, status=400)

        # Build scoped data delta
        from cooperatives.models import Member
        from cooperatives.serializers import CooperativeSerializer, MemberSerializer

        user = request.user
        # `since` isn't applied to cooperatives/members below: neither model tracks
        # an updated_at timestamp, so pulls are always a full scoped snapshot.
        coop_qs = user.get_accessible_cooperatives()
        member_qs = Member.objects.filter(cooperative__in=coop_qs)

        delta = {
            "server_time": timezone.now().isoformat(),
            "cooperatives": CooperativeSerializer(coop_qs, many=True).data,
            "members": MemberSerializer(member_qs, many=True).data,
            "conflicts": SyncConflict.objects.filter(
                pending_change__device=device,
                resolved_at__isnull=True,
            ).values("pk", "conflicting_fields", "detected_at"),
        }

        device.last_seen_at = timezone.now()
        device.save(update_fields=["last_seen_at"])

        return Response(delta)


# ─────────────────────────────────────────────────────────────────────────────
# Conflict Resolution
# ─────────────────────────────────────────────────────────────────────────────

class SyncConflictResolveView(APIView):
    """
    POST /api/sync/conflicts/<pk>/resolve/
    Body: { resolution: "client_wins"|"server_wins"|"manual_merge", final_state: {...} }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        conflict = SyncConflict.objects.filter(pk=pk).first()
        if not conflict:
            return Response({"error": "Conflict not found."}, status=404)
        if conflict.resolved_at:
            return Response({"error": "Already resolved."}, status=400)

        resolution = request.data.get("resolution")
        final_state = request.data.get("final_state")

        if resolution == SyncConflict.RESOLUTION_CLIENT_WINS:
            final_state = conflict.device_snapshot
        elif resolution == SyncConflict.RESOLUTION_SERVER_WINS:
            final_state = conflict.server_snapshot
        elif resolution == SyncConflict.RESOLUTION_MANUAL:
            if not final_state:
                return Response({"error": "final_state required for manual_merge."}, status=400)
        else:
            return Response({"error": "Invalid resolution."}, status=400)

        # Apply the chosen state
        pending = conflict.pending_change
        ct = pending.content_type
        Model = ct.model_class()
        try:
            obj = Model.objects.get(pk=pending.object_id)
            for field, value in _sanitize_payload(Model, final_state).items():
                setattr(obj, field, value)
            obj.save()
        except Exception as exc:
            return Response({"error": str(exc)}, status=500)

        conflict.resolved_at = timezone.now()
        conflict.resolved_by = request.user
        conflict.resolution = resolution
        conflict.final_state = final_state
        conflict.save(update_fields=["resolved_at", "resolved_by", "resolution", "final_state"])

        pending.state = PendingChange.STATE_SYNCED
        pending.save(update_fields=["state"])

        return Response({"resolved": True})


# ─────────────────────────────────────────────────────────────────────────────
# Sync Status (for mobile UI indicator)
# ─────────────────────────────────────────────────────────────────────────────

class SyncStatusView(APIView):
    """GET /api/sync/status/?device_id=xxx — quick health check for mobile app."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        device_id = request.query_params.get("device_id")
        device = Device.objects.filter(device_id=device_id, user=request.user).first()
        if not device:
            return Response({"registered": False})
        pending_count = PendingChange.objects.filter(
            device=device, state=PendingChange.STATE_PENDING
        ).count()
        conflict_count = SyncConflict.objects.filter(
            pending_change__device=device, resolved_at__isnull=True
        ).count()
        return Response({
            "registered": True,
            "last_sync_at": device.last_sync_at,
            "pending_changes": pending_count,
            "unresolved_conflicts": conflict_count,
        })