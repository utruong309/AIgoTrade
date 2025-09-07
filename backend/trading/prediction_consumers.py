import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from typing import Dict, Any, List

from .models import PricePrediction, PredictionModel
from .prediction_service import PredictionService
from .cache_services.prediction_cache import prediction_cache_service

logger = logging.getLogger(__name__)


class PredictionConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.room_group_name = 'predictions'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        logger.info(f"WebSocket connected: {self.channel_name}")
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to prediction updates',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(f"WebSocket disconnected: {self.channel_name}")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'subscribe_symbol':
                symbol = data.get('symbol', '').upper()
                if symbol:
                    await self.subscribe_to_symbol(symbol)
            
            elif message_type == 'unsubscribe_symbol':
                symbol = data.get('symbol', '').upper()
                if symbol:
                    await self.unsubscribe_from_symbol(symbol)
            
            elif message_type == 'get_latest_prediction':
                symbol = data.get('symbol', '').upper()
                if symbol:
                    await self.send_latest_prediction(symbol)
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
    
    async def subscribe_to_symbol(self, symbol: str):
        symbol_group = f'predictions_{symbol.lower()}'
        
        await self.channel_layer.group_add(
            symbol_group,
            self.channel_name
        )
        
        await self.send(text_data=json.dumps({
            'type': 'subscription_confirmed',
            'symbol': symbol,
            'message': f'Subscribed to {symbol} updates'
        }))
    
    async def unsubscribe_from_symbol(self, symbol: str):
        symbol_group = f'predictions_{symbol.lower()}'
        
        await self.channel_layer.group_discard(
            symbol_group,
            self.channel_name
        )
        
        await self.send(text_data=json.dumps({
            'type': 'unsubscription_confirmed',
            'symbol': symbol,
            'message': f'Unsubscribed from {symbol} updates'
        }))
    
    async def send_latest_prediction(self, symbol: str):
        try:
            prediction_service = PredictionService()
            summary = prediction_service.get_prediction_summary(symbol)
            
            await self.send(text_data=json.dumps({
                'type': 'latest_prediction',
                'symbol': symbol,
                'data': summary,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error sending latest prediction for {symbol}: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'symbol': symbol,
                'message': 'Failed to get latest prediction'
            }))
    
    async def prediction_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'prediction_update',
            'symbol': event['symbol'],
            'data': event['data'],
            'timestamp': event['timestamp']
        }))
    
    async def batch_prediction_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'batch_prediction_update',
            'predictions': event['predictions'],
            'timestamp': event['timestamp']
        }))
    
    async def cache_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'cache_update',
            'symbol': event['symbol'],
            'data': event['data'],
            'timestamp': event['timestamp']
        }))


class ModelTrainingConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.room_group_name = 'model_training'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        logger.info(f"Model training WebSocket connected: {self.channel_name}")
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to model training updates',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(f"Model training WebSocket disconnected: {self.channel_name}")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'subscribe_training':
                symbol = data.get('symbol', '').upper()
                if symbol:
                    await self.subscribe_to_training(symbol)
            
            elif message_type == 'get_training_status':
                symbol = data.get('symbol', '').upper()
                if symbol:
                    await self.send_training_status(symbol)
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error processing training WebSocket message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
    
    async def subscribe_to_training(self, symbol: str):
        training_group = f'training_{symbol.lower()}'
        
        await self.channel_layer.group_add(
            training_group,
            self.channel_name
        )
        
        await self.send(text_data=json.dumps({
            'type': 'training_subscription_confirmed',
            'symbol': symbol,
            'message': f'Subscribed to {symbol} training updates'
        }))
    
    async def send_training_status(self, symbol: str):
        try:
            model = await self.get_model_status(symbol)
            
            await self.send(text_data=json.dumps({
                'type': 'training_status',
                'symbol': symbol,
                'data': model,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error sending training status for {symbol}: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'symbol': symbol,
                'message': 'Failed to get training status'
            }))
    
    @database_sync_to_async
    def get_model_status(self, symbol: str) -> Dict:
        try:
            from .models import Stock, PredictionModel
            
            stock = Stock.objects.get(symbol=symbol.upper())
            model = PredictionModel.objects.filter(
                stock=stock,
                model_type='lstm'
            ).order_by('-last_training_at').first()
            
            if model:
                return {
                    'status': model.status,
                    'last_training_at': model.last_training_at.isoformat() if model.last_training_at else None,
                    'training_data_points': model.training_data_points,
                    'train_rmse': float(model.train_rmse) if model.train_rmse else None,
                    'val_rmse': float(model.val_rmse) if model.val_rmse else None,
                    'is_active': model.is_active
                }
            else:
                return {
                    'status': 'not_found',
                    'message': 'No model found for this symbol'
                }
                
        except Exception as e:
            logger.error(f"Error getting model status for {symbol}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def training_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'training_status_update',
            'symbol': event['symbol'],
            'data': event['data'],
            'timestamp': event['timestamp']
        }))


async def send_prediction_update(symbol: str, prediction_data: Dict):
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    
    await channel_layer.group_send(
        f'predictions_{symbol.lower()}',
        {
            'type': 'prediction_update',
            'symbol': symbol,
            'data': prediction_data,
            'timestamp': timezone.now().isoformat()
        }
    )


async def send_batch_prediction_update(predictions: List[Dict]):
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    
    await channel_layer.group_send(
        'predictions',
        {
            'type': 'batch_prediction_update',
            'predictions': predictions,
            'timestamp': timezone.now().isoformat()
        }
    )


async def send_model_training_status(symbol: str, status_data: Dict):
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    
    await channel_layer.group_send(
        f'training_{symbol.lower()}',
        {
            'type': 'training_status_update',
            'symbol': symbol,
            'data': status_data,
            'timestamp': timezone.now().isoformat()
        }
    )


async def send_cache_update(symbol: str, cache_data: Dict):
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    
    await channel_layer.group_send(
        f'predictions_{symbol.lower()}',
        {
            'type': 'cache_update',
            'symbol': symbol,
            'data': cache_data,
            'timestamp': timezone.now().isoformat()
        }
    )