from django.db.models import Avg, Sum, Count
from cooperatives.models import Member
from .models import KPI, DataValidationRule, DataQualityAlert
from simpleeval import simple_eval

class KPIService:
    """Service for calculating Key Performance Indicators."""

    @staticmethod
    def get_cooperatives_with_youth_data(queryset):
        """Returns cooperative queryset annotated with total_members and youth_members counts."""
        from django.db.models import Count, Q
        return queryset.annotate(
            total_members_count=Count('members', distinct=True),
            youth_members_count=Count('members', filter=Q(members__age_group='youth'), distinct=True)
        )

    @staticmethod
    def get_cooperatives_with_yield_data(queryset):
        """
        [STUBBED] Legacy yield data calculation.
        Original logic relied on ProductionRecord and Farm models which are removed.
        """
        from django.db.models import Value
        return queryset.annotate(
            total_production_kg=Value(0.0),
            total_farm_size_ha=Value(0.0)
        )

class ValidationService:
    """Service for executing dynamic data validation rules."""

    @staticmethod
    def validate_record(record):
        """Validates a model instance against active rules."""
        model_name = f"{record._meta.app_label}.{record._meta.object_name}"
        rules = DataValidationRule.objects.filter(applies_to_model=model_name, is_active=True)
        
        # Determine the cooperative association
        cooperative = getattr(record, 'cooperative', None)
        if not cooperative and record._meta.model_name == 'cooperative':
            cooperative = record

        for rule in rules:
            try:
                # Simple evaluation context
                context = {
                    'record': record, 
                    'value': getattr(record, rule.applies_to_field) if rule.applies_to_field else None
                }
                
                # If validation fails
                try:
                    is_valid = simple_eval(rule.rule_expression, names=context)
                except Exception as eval_err:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Rule '{rule.name}' evaluation error: {eval_err}")
                    is_valid = False

                if not is_valid:
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
                
                try:
                    is_valid = simple_eval(rule.rule_expression, names=context)
                except Exception as eval_err:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Questionnaire Rule '{rule.name}' evaluation error: {eval_err}")
                    is_valid = False

                if not is_valid:
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
