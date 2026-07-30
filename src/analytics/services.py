import logging

from django.db.models import Count, Q, Sum
from simpleeval import simple_eval

from .models import DataQualityAlert, DataValidationRule

logger = logging.getLogger(__name__)


class KPIService:
    """Service for calculating Key Performance Indicators."""

    @staticmethod
    def get_cooperatives_with_youth_data(queryset):
        """Returns cooperative queryset annotated with total_members and youth_members counts."""
        return queryset.annotate(
            total_members_count=Count('members', distinct=True),
            youth_members_count=Count('members', filter=Q(members__age_group='youth'), distinct=True)
        )

    @staticmethod
    def get_cooperatives_with_yield_data(queryset):
        """Returns cooperative queryset annotated with total production (kg) and farm area (ha)."""
        return queryset.annotate(
            total_production_kg=Sum('members__production_records__quantity_kg'),
            total_farm_size_ha=Sum('members__farms__size_hectares'),
        )


def _resolve_cooperative(record):
    """Best-effort lookup of the Cooperative a record belongs to, for alert scoping."""
    cooperative = getattr(record, 'cooperative', None)
    if cooperative:
        return cooperative
    if record._meta.model_name == 'cooperative':
        return record
    member = getattr(record, 'member', None) or getattr(getattr(record, 'farm', None), 'member', None)
    if member:
        return member.cooperative
    return None


class ValidationService:
    """Service for executing dynamic data validation rules."""

    @staticmethod
    def _apply_result(rule, record_id, cooperative, is_valid, message):
        if not is_valid:
            DataQualityAlert.objects.get_or_create(
                rule=rule,
                content_type_label=rule.applies_to_model,
                record_id=record_id,
                is_resolved=False,
                defaults={
                    "cooperative_id": cooperative.pk if cooperative else 0,
                    "field_name": rule.applies_to_field or "",
                    "message": message,
                },
            )
        else:
            DataQualityAlert.objects.filter(
                rule=rule,
                content_type_label=rule.applies_to_model,
                record_id=record_id,
                is_resolved=False,
            ).update(is_resolved=True)

    @staticmethod
    def validate_record(record):
        """Validates a model instance against active rules."""
        model_name = f"{record._meta.app_label}.{record._meta.object_name}"
        rules = DataValidationRule.objects.filter(applies_to_model=model_name, is_active=True)
        if not rules:
            return

        cooperative = _resolve_cooperative(record)

        for rule in rules:
            try:
                context = {
                    'record': record,
                    'value': getattr(record, rule.applies_to_field) if rule.applies_to_field else None,
                }
                try:
                    is_valid = simple_eval(rule.rule_expression, names=context)
                except Exception as eval_err:
                    logger.error(f"Rule '{rule.name}' evaluation error: {eval_err}")
                    is_valid = False

                ValidationService._apply_result(
                    rule, record.id, cooperative, is_valid, f"Validation failed: {rule.name}"
                )
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id} on {model_name} {record.id}: {e}")

    @staticmethod
    def validate_submission(submission):
        """Validates a questionnaire submission and its answers."""
        rules = DataValidationRule.objects.filter(applies_to_model='questionnaires.Submission', is_active=True)
        if not rules:
            return

        answers = {}
        for answer in submission.answers.all():
            key = f"q_{answer.question.id}"
            if answer.value_text:
                answers[key] = answer.value_text
            elif answer.value_number is not None:
                answers[key] = float(answer.value_number)
            elif answer.value_date:
                answers[key] = answer.value_date
            elif answer.value_boolean is not None:
                answers[key] = answer.value_boolean

        target = submission.content_object
        cooperative = _resolve_cooperative(target) if target is not None else None

        for rule in rules:
            try:
                context = {'submission': submission, 'answers': answers}
                try:
                    is_valid = simple_eval(rule.rule_expression, names=context)
                except Exception as eval_err:
                    logger.error(f"Questionnaire Rule '{rule.name}' evaluation error: {eval_err}")
                    is_valid = False

                ValidationService._apply_result(
                    rule, submission.id, cooperative, is_valid, f"Questionnaire validation failed: {rule.name}"
                )
            except Exception as e:
                logger.error(f"Error evaluating submission rule {rule.id} on {submission.id}: {e}")
