import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aigo_trade.settings')

app = Celery('aigo_trade')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Import ML tasks
from trading.ml_tasks import (
    train_lstm_model,
    make_prediction_task,
    update_predictions_batch,
    train_models_batch,
    cleanup_expired_caches,
    update_prediction_accuracy,
    periodic_prediction_update,
    periodic_cache_cleanup
)

# Register periodic tasks
from celery.schedules import crontab

app.conf.beat_schedule = {
    'update-predictions-every-15-minutes': {
        'task': 'trading.ml_tasks.periodic_prediction_update',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'cleanup-caches-every-hour': {
        'task': 'trading.ml_tasks.periodic_cache_cleanup',
        'schedule': crontab(minute=0),  # Every hour
    },
    'update-prediction-accuracy-daily': {
        'task': 'trading.ml_tasks.update_prediction_accuracy',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
}

app.conf.timezone = 'UTC'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
