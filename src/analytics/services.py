from django.db.models import Avg, Sum, Count
from cooperatives.models import ProductionRecord, Member, Farm
from .models import KPI, DataValidationRule, DataQualityAlert

class KPIService:
    """Service for calculating Key Performance Indicators."""

    @staticmethod
    def calculate_yield_per_hectare(cooperative):
        """Calculates average yield (kg) per hectare for a cooperative."""
        total_quantity = ProductionRecord.objects.filter(
            farm__member__cooperative=cooperative
        ).aggregate(total=Sum('quantity_kg'))['total'] or 0
        
        total_size = Farm.objects.filter(
            member__cooperative=cooperative
        ).aggregate(total=Sum('size_hectares'))['total'] or 0
        
        if total_size > 0:
            return total_quantity / total_size
        return 0

    @staticmethod
    def calculate_youth_participation(cooperative):
        """Calculates percentage of youth members (18-35) in a cooperative."""
        total_members = Member.objects.filter(cooperative=cooperative).count()
        if total_members == 0:
            return 0
        
        youth_count = Member.objects.filter(
            cooperative=cooperative, 
            age_group='youth'
        ).count()
        
        return (youth_count / total_members) * 100

class ValidationService:
    """Service for executing dynamic data validation rules."""

    @staticmethod
    def validate_record(record):
        """Validates a model instance against active rules."""
        model_name = f"{record._meta.app_label}.{record._meta.object_name}"
        rules = DataValidationRule.objects.filter(applies_to_model=model_name, is_active=True)
        
        # Determine the cooperative association
        cooperative = getattr(record, 'cooperative', None)
        if not cooperative and hasattr(record, 'farm'):
            cooperative = record.farm.member.cooperative
        elif not cooperative and record._meta.model_name == 'cooperative':
            cooperative = record

        for rule in rules:
            try:
                # Simple evaluation context
                context = {
                    'record': record, 
                    'value': getattr(record, rule.applies_to_field) if rule.applies_to_field else None
                }
                
                # If validation fails
                if not eval(rule.rule_expression, {"__builtins__": {}}, context):
                    # Check for existing unresolved alert for this record/rule
                    alert, created = DataQualityAlert.objects.get_or_create(
                        rule=rule,
                        cooperative=cooperative,
                        record_id=record.id,
                        is_resolved=False,
                        defaults={'message': f"Validation failed: {rule.name}"}
                    )
                else:
                    # Validation passed - resolve any existing alerts for this record/rule
                    DataQualityAlert.objects.filter(
                        rule=rule, 
                        record_id=record.id, 
                        is_resolved=False
                    ).update(is_resolved=True)
                    
            except Exception as e:
                # Log error but don't break the save process
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error evaluating rule {rule.id} on {model_name} {record.id}: {e}")

    @staticmethod
    def validate_submission(submission):
        """Validates a questionnaire submission and its answers."""
        from questionnaires.models import Answer
        rules = DataValidationRule.objects.filter(applies_to_model='questionnaires.Submission', is_active=True)
        
        # Build answer map for easy access in rules
        answers = {}
        for answer in submission.answers.all():
            # Use question text/id or a slug as key if possible
            # For now, we use a simple key based on question ID
            key = f"q_{answer.question.id}"
            if answer.value_text:
                answers[key] = answer.value_text
            elif answer.value_number is not None:
                answers[key] = float(answer.value_number)
            elif answer.value_date:
                answers[key] = answer.value_date
            elif answer.value_boolean is not None:
                answers[key] = answer.value_boolean

        # Get cooperative from target object
        target = submission.content_object
        cooperative = getattr(target, 'cooperative', None)
        if not cooperative and hasattr(target, 'name') and target._meta.model_name == 'cooperative':
            cooperative = target

        for rule in rules:
            try:
                context = {
                    'submission': submission,
                    'answers': answers,
                }
                
                if not eval(rule.rule_expression, {"__builtins__": {}}, context):
                    DataQualityAlert.objects.get_or_create(
                        rule=rule,
                        cooperative=cooperative,
                        record_id=submission.id,
                        is_resolved=False,
                        defaults={'message': f"Questionnaire Validation failed: {rule.name}"}
                    )
                else:
                    DataQualityAlert.objects.filter(
                        rule=rule,
                        record_id=submission.id,
                        is_resolved=False
                    ).update(is_resolved=True)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error evaluating submission rule {rule.id} on {submission.id}: {e}")
