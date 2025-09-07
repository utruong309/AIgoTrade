from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from celery.result import AsyncResult

from .ml_tasks import (
    train_lstm_model, make_prediction_task, update_predictions_batch,
    train_models_batch, cleanup_expired_caches, update_prediction_accuracy
)


class MLTaskViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def train_model(self, request):
        try:
            symbol = request.data.get('symbol', '').upper()
            days = int(request.data.get('days', 365))
            epochs = int(request.data.get('epochs', 100))
            
            if not symbol:
                return Response({
                    'status': 'error',
                    'message': 'Symbol parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            task = train_lstm_model.delay(symbol, days, epochs)
            
            return Response({
                'status': 'started',
                'symbol': symbol,
                'task_id': task.id,
                'message': f'Model training started for {symbol}'
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def train_models_batch(self, request):
        try:
            symbols = request.data.get('symbols', [])
            days = int(request.data.get('days', 365))
            epochs = int(request.data.get('epochs', 100))
            
            if not symbols:
                return Response({
                    'status': 'error',
                    'message': 'Symbols list is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            task = train_models_batch.delay(symbols, days, epochs)
            
            return Response({
                'status': 'started',
                'symbols': symbols,
                'task_id': task.id,
                'message': f'Batch model training started for {len(symbols)} stocks'
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def update_predictions_batch(self, request):
        try:
            symbols = request.data.get('symbols', [])
            use_cache = request.data.get('use_cache', True)
            
            if not symbols:
                return Response({
                    'status': 'error',
                    'message': 'Symbols list is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            task = update_predictions_batch.delay(symbols, use_cache)
            
            return Response({
                'status': 'started',
                'symbols': symbols,
                'task_id': task.id,
                'message': f'Batch prediction update started for {len(symbols)} stocks'
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def cleanup_caches(self, request):
        try:
            task = cleanup_expired_caches.delay()
            
            return Response({
                'status': 'started',
                'task_id': task.id,
                'message': 'Cache cleanup started'
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def update_prediction_accuracy(self, request):
        try:
            task = update_prediction_accuracy.delay()
            
            return Response({
                'status': 'started',
                'task_id': task.id,
                'message': 'Prediction accuracy update started'
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def task_status(self, request):
        try:
            task_id = request.query_params.get('task_id')
            
            if not task_id:
                return Response({
                    'status': 'error',
                    'message': 'task_id parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            task_result = AsyncResult(task_id)
            
            return Response({
                'status': 'success',
                'task_id': task_id,
                'task_status': task_result.status,
                'task_result': task_result.result if task_result.ready() else None,
                'task_info': task_result.info if not task_result.ready() else None
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)