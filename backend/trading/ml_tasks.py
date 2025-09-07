import os
import sys
import django
import asyncio
from celery import shared_task
from celery.exceptions import Retry
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aigo_trade.settings')
django.setup()

from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from .models import Stock, PredictionModel, PricePrediction
from .ml_models.lstm_model import StockPricePredictor
from .data_preprocessing import DataPreprocessingService
from .prediction_service import PredictionService
from .cache_services.prediction_cache import prediction_cache_service
from .prediction_consumers import (
    send_prediction_update, send_batch_prediction_update,
    send_model_training_status, send_cache_update
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def train_lstm_model(self, symbol: str, days: int = 365, epochs: int = 100):
    try:
        logger.info(f"Starting LSTM training for {symbol}")
        
        stock = Stock.objects.get(symbol=symbol)
        
        model, created = PredictionModel.objects.get_or_create(
            symbol=stock,
            model_type='lstm',
            defaults={
                'status': 'training',
                'training_data_points': 0,
                'training_duration_days': days,
                'last_training_at': timezone.now(),
            }
        )
        
        if not created:
            model.status = 'training'
            model.last_training_at = timezone.now()
            model.save()
        
        asyncio.create_task(send_model_training_status(
            symbol, {'status': 'training', 'progress': 0}
        ))
        
        data_service = DataPreprocessingService()
        df = data_service.get_historical_data(symbol, days)
        
        if df is None or len(df) < 100:
            raise ValueError(f"Insufficient data for {symbol}")
        
        model_path = f"models/{symbol.lower()}"
        predictor = StockPricePredictor(model_path=model_path)
        
        metrics = predictor.train_model(df, epochs=epochs)
        
        model.status = 'trained'
        model.training_data_points = len(df)
        model.train_rmse = Decimal(str(metrics['train_rmse']))
        model.val_rmse = Decimal(str(metrics['val_rmse']))
        model.last_training_at = timezone.now()
        model.save()
        
        asyncio.create_task(send_model_training_status(
            symbol, {'status': 'completed', 'metrics': metrics}
        ))
        
        logger.info(f"LSTM training completed for {symbol}")
        return {'status': 'success', 'metrics': metrics}
        
    except Exception as exc:
        logger.error(f"LSTM training failed for {symbol}: {str(exc)}")
        
        try:
            model = PredictionModel.objects.get(symbol__symbol=symbol, model_type='lstm')
            model.status = 'failed'
            model.save()
        except:
            pass
        
        asyncio.create_task(send_model_training_status(
            symbol, {'status': 'failed', 'error': str(exc)}
        ))
        
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def make_prediction_task(self, symbol: str):
    try:
        logger.info(f"Making prediction for {symbol}")
        
        prediction_service = PredictionService()
        result = prediction_service.make_prediction(symbol)
        
        if result['status'] == 'success':
            asyncio.create_task(send_prediction_update(symbol, result['data']))
            logger.info(f"Prediction completed for {symbol}")
        else:
            logger.warning(f"Prediction failed for {symbol}: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as exc:
        logger.error(f"Prediction task failed for {symbol}: {str(exc)}")
        raise self.retry(exc=exc, countdown=30)


@shared_task
def update_predictions_batch(symbols: List[str]):
    try:
        logger.info(f"Updating predictions for {len(symbols)} symbols")
        
        prediction_service = PredictionService()
        results = []
        
        for symbol in symbols:
            try:
                result = prediction_service.make_prediction(symbol)
                results.append({'symbol': symbol, 'result': result})
            except Exception as e:
                logger.error(f"Failed to predict for {symbol}: {str(e)}")
                results.append({'symbol': symbol, 'error': str(e)})
        
        successful_predictions = [r for r in results if 'result' in r and r['result']['status'] == 'success']
        
        if successful_predictions:
            asyncio.create_task(send_batch_prediction_update(successful_predictions))
        
        logger.info(f"Batch prediction update completed: {len(successful_predictions)}/{len(symbols)} successful")
        
        return {'status': 'completed', 'results': results}
        
    except Exception as exc:
        logger.error(f"Batch prediction update failed: {str(exc)}")
        raise exc


@shared_task
def train_models_batch(symbols: List[str], days: int = 365, epochs: int = 100):
    try:
        logger.info(f"Training models for {len(symbols)} symbols")
        
        results = []
        for symbol in symbols:
            try:
                result = train_lstm_model.delay(symbol, days, epochs)
                results.append({'symbol': symbol, 'task_id': result.id})
            except Exception as e:
                logger.error(f"Failed to start training for {symbol}: {str(e)}")
                results.append({'symbol': symbol, 'error': str(e)})
        
        logger.info(f"Batch training started for {len(results)} symbols")
        return {'status': 'started', 'results': results}
        
    except Exception as exc:
        logger.error(f"Batch training failed: {str(exc)}")
        raise exc


@shared_task
def cleanup_expired_caches():
    try:
        logger.info("Cleaning up expired prediction caches")
        
        expired_time = timezone.now() - timedelta(hours=1)
        
        with transaction.atomic():
            expired_caches = PricePrediction.objects.filter(
                prediction_timestamp__lt=expired_time
            )
            count = expired_caches.count()
            expired_caches.delete()
        
        prediction_cache_service.cleanup_expired()
        
        logger.info(f"Cleaned up {count} expired prediction caches")
        return {'status': 'success', 'cleaned_count': count}
        
    except Exception as exc:
        logger.error(f"Cache cleanup failed: {str(exc)}")
        raise exc


@shared_task
def update_prediction_accuracy():
    try:
        logger.info("Updating prediction accuracy metrics")
        
        predictions = PricePrediction.objects.filter(
            actual_price__isnull=False,
            accuracy_updated=False
        )
        
        updated_count = 0
        for prediction in predictions:
            try:
                actual_price = float(prediction.actual_price)
                predicted_price = float(prediction.predicted_price)
                
                accuracy = 100 - abs(actual_price - predicted_price) / actual_price * 100
                accuracy = max(0, min(100, accuracy))
                
                prediction.prediction_accuracy = Decimal(str(accuracy))
                prediction.accuracy_updated = True
                prediction.save()
                
                updated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to update accuracy for prediction {prediction.id}: {str(e)}")
        
        logger.info(f"Updated accuracy for {updated_count} predictions")
        return {'status': 'success', 'updated_count': updated_count}
        
    except Exception as exc:
        logger.error(f"Accuracy update failed: {str(exc)}")
        raise exc


@shared_task
def periodic_prediction_update():
    try:
        logger.info("Running periodic prediction update")
        
        active_symbols = Stock.objects.filter(is_active=True).values_list('symbol', flat=True)
        
        if active_symbols:
            update_predictions_batch.delay(list(active_symbols))
        
        logger.info(f"Scheduled prediction update for {len(active_symbols)} symbols")
        return {'status': 'scheduled', 'symbol_count': len(active_symbols)}
        
    except Exception as exc:
        logger.error(f"Periodic prediction update failed: {str(exc)}")
        raise exc


@shared_task
def periodic_cache_cleanup():
    try:
        logger.info("Running periodic cache cleanup")
        
        cleanup_expired_caches.delay()
        update_prediction_accuracy.delay()
        
        logger.info("Scheduled cache cleanup and accuracy update")
        return {'status': 'scheduled'}
        
    except Exception as exc:
        logger.error(f"Periodic cache cleanup failed: {str(exc)}")
        raise exc