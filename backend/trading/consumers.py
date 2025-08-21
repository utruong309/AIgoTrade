import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Stock
from .live_market_service import get_live_market_service
import logging

logger = logging.getLogger(__name__)

class MarketDataConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None

    async def connect(self):
        """Connect to WebSocket and start receiving market data"""
        self.room_name = "market_data"
        self.room_group_name = f"market_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to live market data feed'
        }))

        # Start live market service if not already running
        await self.start_live_market_service()

    async def disconnect(self, close_code):
        """Leave room group"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'unknown')
            
            if message_type == 'subscribe_symbol':
                symbol = text_data_json.get('symbol')
                if symbol:
                    await self.subscribe_to_symbol(symbol)
            elif message_type == 'unsubscribe_symbol':
                symbol = text_data_json.get('symbol')
                if symbol:
                    await self.unsubscribe_from_symbol(symbol)
            elif message_type == 'get_stocks':
                await self.send_stock_list()
            elif message_type == 'search_stocks':
                query = text_data_json.get('query', '')
                if query:
                    await self.search_stocks(query)
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def start_live_market_service(self):
        """Start the live market service"""
        try:
            # Start the live market service in a background task
            asyncio.create_task(self._start_service())
            
            await self.send(text_data=json.dumps({
                'type': 'service_status',
                'message': 'Starting live market data service...'
            }))
            
        except Exception as e:
            logger.error(f"Failed to start live market service: {e}")

    async def _start_service(self):
        """Start the live market service in background"""
        try:
            # Start the service
            live_service = get_live_market_service()
            live_service.start()
            
            # Wait a moment for initial data
            await asyncio.sleep(2)
            
            # Send initial stock list
            await self.send_stock_list()
            
        except Exception as e:
            logger.error(f"Error starting live market service: {e}")

    async def subscribe_to_symbol(self, symbol):
        """Subscribe to real-time updates for a specific symbol"""
        try:
            # Add symbol to room group
            symbol_group = f"symbol_{symbol}"
            await self.channel_layer.group_add(
                symbol_group,
                self.channel_name
            )
            
            # Subscribe to live updates
            live_service = get_live_market_service()
            live_service.subscribe_symbol(symbol)
            
            await self.send(text_data=json.dumps({
                'type': 'subscription_confirmed',
                'symbol': symbol,
                'message': f'Subscribed to {symbol} live updates'
            }))
            
        except Exception as e:
            logger.error(f"Failed to subscribe to {symbol}: {e}")

    async def unsubscribe_from_symbol(self, symbol):
        """Unsubscribe from updates for a specific symbol"""
        try:
            symbol_group = f"symbol_{symbol}"
            await self.channel_layer.group_discard(
                symbol_group,
                self.channel_name
            )
            
            await self.send(text_data=json.dumps({
                'type': 'unsubscription_confirmed',
                'symbol': symbol,
                'message': f'Unsubscribed from {symbol} updates'
            }))
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from {symbol}: {e}")

    async def send_stock_list(self):
        """Send current stock list to client"""
        try:
            stocks = await self.get_stocks_from_live_service()
            await self.send(text_data=json.dumps({
                'type': 'stock_list',
                'stocks': stocks
            }))
        except Exception as e:
            logger.error(f"Failed to send stock list: {e}")

    async def search_stocks(self, query):
        """Search stocks and send results"""
        try:
            stocks = await self.search_stocks_from_live_service(query)
            await self.send(text_data=json.dumps({
                'type': 'search_results',
                'query': query,
                'stocks': stocks
            }))
        except Exception as e:
            logger.error(f"Failed to search stocks: {e}")

    @database_sync_to_async
    def get_stocks_from_live_service(self):
        """Get stocks from live market service"""
        live_service = get_live_market_service()
        return live_service.get_stock_list()

    @database_sync_to_async
    def search_stocks_from_live_service(self, query):
        """Search stocks from live market service"""
        live_service = get_live_market_service()
        return live_service.search_stocks(query)

    async def market_update(self, event):
        """Send market update to WebSocket"""
        message = event['message']
        await self.send(text_data=json.dumps(message))

class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({
            'message': 'WebSocket connected successfully!'
        }))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        await self.send(text_data=json.dumps({
            'message': f'Received: {message}'
        }))