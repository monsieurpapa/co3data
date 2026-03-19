"""CO3DATA — Celery Background Tasks"""
import logging
from datetime import date, timedelta
from io import BytesIO

from celery import shared_task
from django.db.models import Sum
from django.utils import timezone

logger = logging.getLogger("co3data.tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def compute_kpis_for_cooperative(self, cooperative_id: int, period_start: str, period_end: str):
    from cooperatives.models import Cooperative, Member, ProductionRecord
    from analytics.models import KPI, KPIResult
    try:
        cooperative = Cooperative.objects.get(pk=cooperative_id)
        start, end = date.fromisoformat(period_start), date.fromisoformat(period_end)
        members   = Member.objects.filter(cooperative=cooperative, is_active=True)
        production = ProductionRecord.objects.filter(station__cooperative=cooperative,
                                                     harvest_date__gte=start, harvest_date__lte=end)
        financials = cooperative.financial_records.filter(transaction_date__gte=start,
                                                          transaction_date__lte=end)
        total_kg   = float(production.aggregate(t=Sum("quantity_kg"))["t"] or 0)
        total_m    = members.count()
        female_m   = members.filter(gender="female", is_active=True).count()
        youth_m    = members.filter(age_group="youth", is_active=True).count()
        income     = float(financials.filter(transaction_type="income").aggregate(t=Sum("amount"))["t"] or 0)
        expenses   = float(financials.filter(transaction_type="expense").aggregate(t=Sum("amount"))["t"] or 0)
        context = {
            "total_production_kg": total_kg,
            "total_members": total_m,
            "female_members": female_m,
            "youth_members": youth_m,
            "total_income": income,
            "total_expenses": expenses,
            "production_per_member": total_kg / total_m if total_m else 0,
            "female_participation_rate": (female_m / total_m * 100) if total_m else 0,
            "youth_participation_rate":  (youth_m  / total_m * 100) if total_m else 0,
            "net_income": income - expenses,
        }
        computed = 0
        for kpi in KPI.objects.filter(is_active=True):
            # We assume KPI model will have a method to evaluate logic based on context
            # or we compute specific predefined KPIs
            pass
        
        # For now, let's just log and return
        logger.info(f"Computed KPIs for {cooperative.name} [{start}–{end}]")
        return {"cooperative": cooperative.name, "kpis_computed": computed}
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def compute_all_cooperative_kpis():
    from cooperatives.models import Cooperative
    today      = timezone.now().date()
    period_end = today.replace(day=1) - timedelta(days=1)
    period_start = period_end.replace(day=1)
    for coop in Cooperative.objects.all():
        compute_kpis_for_cooperative.delay(coop.pk, period_start.isoformat(), period_end.isoformat())


@shared_task(bind=True, max_retries=3)
def run_data_quality_checks(self, cooperative_id: int = None):
    from cooperatives.models import Cooperative, ProductionRecord
    from analytics.models import DataValidationRule, DataQualityAlert
    rules = DataValidationRule.objects.filter(is_active=True)
    coops = Cooperative.objects.all()
    if cooperative_id:
        coops = coops.filter(pk=cooperative_id)
    alerts_created = 0
    for coop in coops:
        for rule in rules:
            if "ProductionRecord" in rule.applies_to_model:
                for record in ProductionRecord.objects.filter(station__cooperative=coop):
                    data = {"quantity_kg": float(record.quantity_kg),
                            "base_price_fc": float(record.base_price_fc or 0)}
                    # rule.evaluate logic should be implemented
                    pass
    logger.info(f"Data quality check completed")
    return {"alerts_created": alerts_created}


@shared_task
def cleanup_old_sync_logs(days_to_keep: int = 90):
    from sync.models import SyncLog
    cutoff = timezone.now() - timedelta(days=days_to_keep)
    deleted, _ = SyncLog.objects.filter(sync_start_time__lt=cutoff).delete()
    logger.info(f"Deleted {deleted} old sync logs")
    return {"deleted": deleted}
