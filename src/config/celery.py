"""
Celery configuration for the Accounting System.

Configures the Celery app with Django settings (CELERY_* namespace)
and auto-discovers tasks from all registered Django apps.
Broker and result backend are set via CELERY_BROKER_URL and CELERY_RESULT_BACKEND.
"""
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
from celery.schedules import crontab
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Compute KPIs for all cooperatives every night at 02:00 Africa/Kinshasa
    "nightly-kpi-computation": {
        "task": "core.tasks.compute_all_cooperative_kpis",
        "schedule": crontab(hour=2, minute=0),
    },
    # Data quality sweep every 6 hours
    "data-quality-checks": {
        "task": "core.tasks.run_data_quality_checks",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # Purge sync logs older than 90 days — weekly
    "cleanup-sync-logs": {
        "task": "core.tasks.cleanup_old_sync_logs",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),
    },
}
