import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aigo_trade.settings')

app = Celery('aigo_trade')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

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

from celery.schedules import crontab

app.conf.beat_schedule = {
    'update-predictions-every-15-minutes': {
        'task': 'trading.ml_tasks.periodic_prediction_update',
        'schedule': crontab(minute='*/15'),  
    },
    'cleanup-caches-every-hour': {
        'task': 'trading.ml_tasks.periodic_cache_cleanup',
        'schedule': crontab(minute=0),  
    },
    'update-prediction-accuracy-daily': {
        'task': 'trading.ml_tasks.update_prediction_accuracy',
        'schedule': crontab(hour=1, minute=0),  
    },
}

app.conf.timezone = 'UTC'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')