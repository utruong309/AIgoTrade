import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.db import transaction

from .models import Stock, PredictionModel, PricePrediction, PredictionCache
from .ml_models.lstm_model import StockPricePredictor
from .data_preprocessing import DataPreprocessingService
from .cache_services.prediction_cache import prediction_cache_service

logger = logging.getLogger(__name__)


class PredictionService:
    
    def __init__(self):
        self.data_preprocessor = DataPreprocessingService()
        self.model_path = "models/"
    
    def get_active_model(self, symbol: str) -> Optional[PredictionModel]:
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
            model = PredictionModel.objects.filter(
                stock=stock,
                status='trained',
                model_type='lstm'
            ).first()
            
            if model and model.is_active:
                return model
            
            return None
            
        except Stock.DoesNotExist:
            logger.error(f"Stock {symbol} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting active model for {symbol}: {str(e)}")
            return None
    
    def make_prediction(self, symbol: str, use_cache: bool = True) -> Dict:
        try:
            logger.info(f"Making prediction for {symbol}")
            
            if use_cache:
                cached_prediction = self._get_cached_prediction(symbol)
                if cached_prediction:
                    logger.info(f"Using cached prediction for {symbol}")
                    return {
                        'status': 'success',
                        'data': cached_prediction,
                        'source': 'cache'
                    }
            
            model = self.get_active_model(symbol)
            if not model:
                return {
                    'status': 'error',
                    'message': f'No trained model found for {symbol}'
                }
            
            df = self.data_preprocessor.get_historical_data(symbol, days=365)
            if df is None or len(df) < 60:
                return {
                    'status': 'error',
                    'message': f'Insufficient data for {symbol}'
                }
            
            model_path = f"{self.model_path}/{symbol.lower()}"
            predictor = StockPricePredictor(model_path=model_path)
            
            try:
                predictor.load_model(symbol)
            except FileNotFoundError:
                return {
                    'status': 'error',
                    'message': f'Model file not found for {symbol}'
                }
            
            prediction_result = predictor.predict_next_price(df)
            
            prediction_data = {
                'symbol': symbol,
                'predicted_price': prediction_result['predicted_price'],
                'current_price': prediction_result['current_price'],
                'price_change': prediction_result['price_change'],
                'price_change_percent': prediction_result['price_change_percent'],
                'confidence_score': prediction_result['confidence'],
                'confidence_level': self._get_confidence_level(prediction_result['confidence']),
                'model_type': 'lstm',
                'prediction_date': timezone.now().date(),
                'prediction_timestamp': timezone.now()
            }
            
            with transaction.atomic():
                prediction = PricePrediction.objects.create(
                    stock=Stock.objects.get(symbol=symbol.upper()),
                    model=model,
                    predicted_price=Decimal(str(prediction_data['predicted_price'])),
                    current_price=Decimal(str(prediction_data['current_price'])),
                    price_change=Decimal(str(prediction_data['price_change'])),
                    price_change_percent=Decimal(str(prediction_data['price_change_percent'])),
                    confidence_score=Decimal(str(prediction_data['confidence_score'])),
                    confidence_level=prediction_data['confidence_level'],
                    prediction_date=prediction_data['prediction_date'],
                    prediction_timestamp=prediction_data['prediction_timestamp']
                )
                
                prediction_data['id'] = prediction.id
            
            self._cache_prediction(symbol, prediction_data)
            
            logger.info(f"Prediction completed for {symbol}: ${prediction_data['predicted_price']:.2f}")
            
            return {
                'status': 'success',
                'data': prediction_data,
                'source': 'model'
            }
            
        except Exception as e:
            logger.error(f"Error making prediction for {symbol}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _get_cached_prediction(self, symbol: str) -> Optional[Dict]:
        try:
            cache_key = f"prediction:{symbol.lower()}"
            cached_data = prediction_cache_service.get(cache_key)
            
            if cached_data:
                cache_age = timezone.now() - cached_data['timestamp']
                if cache_age.total_seconds() < 3600:
                    return cached_data['data']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached prediction for {symbol}: {str(e)}")
            return None
    
    def _cache_prediction(self, symbol: str, prediction_data: Dict):
        try:
            cache_key = f"prediction:{symbol.lower()}"
            cache_data = {
                'data': prediction_data,
                'timestamp': timezone.now()
            }
            
            prediction_cache_service.set(cache_key, cache_data, ttl=3600)
            
        except Exception as e:
            logger.error(f"Error caching prediction for {symbol}: {str(e)}")
    
    def _get_confidence_level(self, confidence_score: float) -> str:
        if confidence_score >= 0.8:
            return 'high'
        elif confidence_score >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def get_prediction_history(self, symbol: str, limit: int = 20) -> List[Dict]:
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
            
            predictions = PricePrediction.objects.filter(
                stock=stock
            ).order_by('-prediction_timestamp')[:limit]
            
            history = []
            for pred in predictions:
                history.append({
                    'id': pred.id,
                    'predicted_price': float(pred.predicted_price),
                    'current_price': float(pred.current_price),
                    'actual_price': float(pred.actual_price) if pred.actual_price else None,
                    'price_change': float(pred.price_change),
                    'price_change_percent': float(pred.price_change_percent),
                    'confidence_score': float(pred.confidence_score),
                    'confidence_level': pred.confidence_level,
                    'prediction_accuracy': float(pred.prediction_accuracy) if pred.prediction_accuracy else None,
                    'prediction_date': pred.prediction_date,
                    'prediction_timestamp': pred.prediction_timestamp,
                    'model_type': pred.model.model_type if pred.model else 'unknown'
                })
            
            return history
            
        except Stock.DoesNotExist:
            logger.error(f"Stock {symbol} not found")
            return []
        except Exception as e:
            logger.error(f"Error getting prediction history for {symbol}: {str(e)}")
            return []
    
    def get_model_performance(self, symbol: str) -> Dict:
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
            
            predictions = PricePrediction.objects.filter(
                stock=stock,
                actual_price__isnull=False,
                prediction_accuracy__isnull=False
            ).order_by('-prediction_timestamp')
            
            if not predictions.exists():
                return {
                    'status': 'error',
                    'message': 'No completed predictions available for performance analysis'
                }
            
            accuracies = [float(p.prediction_accuracy) for p in predictions]
            
            performance_data = {
                'status': 'success',
                'symbol': symbol,
                'total_predictions': len(accuracies),
                'average_accuracy': sum(accuracies) / len(accuracies),
                'max_accuracy': max(accuracies),
                'min_accuracy': min(accuracies),
                'accuracy_trend': accuracies[:10],
                'recent_performance': accuracies[:5] if len(accuracies) >= 5 else accuracies
            }
            
            return performance_data
            
        except Stock.DoesNotExist:
            return {
                'status': 'error',
                'message': f'Stock {symbol} not found'
            }
        except Exception as e:
            logger.error(f"Error getting model performance for {symbol}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def cleanup_old_predictions(self, days: int = 30):
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            
            old_predictions = PricePrediction.objects.filter(
                prediction_timestamp__lt=cutoff_date
            )
            
            count = old_predictions.count()
            old_predictions.delete()
            
            logger.info(f"Cleaned up {count} old predictions")
            
            return {
                'status': 'success',
                'cleaned_count': count
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old predictions: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_prediction_summary(self, symbol: str) -> Dict:
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
            
            latest_prediction = PricePrediction.objects.filter(
                stock=stock
            ).order_by('-prediction_timestamp').first()
            
            if not latest_prediction:
                return {
                    'status': 'error',
                    'message': 'No predictions available'
                }
            
            model = self.get_active_model(symbol)
            
            summary = {
                'status': 'success',
                'symbol': symbol,
                'name': stock.name,
                'current_price': float(latest_prediction.current_price),
                'predicted_price': float(latest_prediction.predicted_price),
                'price_change': float(latest_prediction.price_change),
                'price_change_percent': float(latest_prediction.price_change_percent),
                'confidence_score': float(latest_prediction.confidence_score),
                'confidence_level': latest_prediction.confidence_level,
                'model_type': latest_prediction.prediction_model.model_type if latest_prediction.prediction_model else 'unknown',
                'prediction_timestamp': latest_prediction.prediction_timestamp,
                'model_status': model.status if model else 'not_available',
                'last_training': model.training_end_date if model else None
            }
            
            return summary
            
        except Stock.DoesNotExist:
            return {
                'status': 'error',
                'message': f'Stock {symbol} not found'
            }
        except Exception as e:
            logger.error(f"Error getting prediction summary for {symbol}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_available_predictions(self, limit: int = 20) -> List[Dict]:
        try:
            logger.info(f"Getting available predictions with limit {limit}")
            
            recent_predictions = PricePrediction.objects.filter(
                prediction_model__status='trained'
            ).select_related('stock', 'prediction_model').order_by('-prediction_timestamp')[:limit]
            
            predictions = []
            for prediction in recent_predictions:
                try:
                    summary = self.get_prediction_summary(prediction.stock.symbol)
                    if summary.get('status') == 'success':
                        summary_data = {k: v for k, v in summary.items() if k != 'status'}
                        predictions.append(summary_data)
                except Exception as e:
                    logger.warning(f"Error getting summary for {prediction.stock.symbol}: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(predictions)} available predictions")
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting available predictions: {str(e)}")
            return []