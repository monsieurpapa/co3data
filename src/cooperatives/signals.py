from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ProductionRecord, FinancialRecord, Member, Cooperative
from analytics.services import ValidationService

@receiver(post_save, sender=ProductionRecord)
@receiver(post_save, sender=FinancialRecord)
@receiver(post_save, sender=Member)
@receiver(post_save, sender=Cooperative)
def validate_cooperative_records(sender, instance, **kwargs):
    """Trigger validation service on every save."""
    ValidationService.validate_record(instance)
