import os
import json
import asyncio
import websocket
import threading
import time
import logging
import requests
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from decouple import config
from .models import Stock, MarketData
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

class LiveMarketService:
    
    def __init__(self):
        self.api_key = config('TWELVEDATA_API_KEY')
        if not self.api_key:
            raise ValueError("TWELVEDATA_API_KEY not found in environment variables")
        
        self.base_url = "https://api.twelvedata.com"
        self.ws_url = "wss://ws.twelvedata.com/v1/quotes/price"
        self.ws = None
        self.connected = False
        self.subscribed_symbols = set()
        self.channel_layer = get_channel_layer()
        
        self.default_symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", 
            "BRK.A", "JPM", "JNJ", "V", "PG", "UNH", "HD", "MA"
        ]
        
        self.price_update_interval = 5  #seconds
        self.ohlc_update_interval = 300  #5 minutes
        
        self.price_update_thread = None
        self.ohlc_update_thread = None
        self.running = False

    def start(self):
        if self.running:
            return
            
        self.running = True
        logger.info("Starting Live Market Service...")
        
        self.start_websocket()
        
        self.start_price_updates()
        
        self.start_ohlc_updates()
        
        self.populate_initial_data()

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()
        
        if self.price_update_thread:
            self.price_update_thread.join(timeout=1)
        
        if self.ohlc_update_thread:
            self.ohlc_update_thread.join(timeout=1)
        
        logger.info("Live Market Service stopped")

    def start_websocket(self):
        try:
            self.ws = websocket.WebSocketApp(
                f"{self.ws_url}?apikey={self.api_key}",
                on_open=self.on_websocket_open,
                on_message=self.on_websocket_message,
                on_error=self.on_websocket_error,
                on_close=self.on_websocket_close
            )
            
            ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            ws_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket: {e}")

    def on_websocket_open(self, ws):
        logger.info("WebSocket connected to Twelvedata")
        self.connected = True
        
        for symbol in self.default_symbols:
            self.subscribe_symbol(symbol)

    def on_websocket_message(self, ws, message):
        try:
            data = json.loads(message)
            event_type = data.get('event', 'unknown')
            
            if event_type == 'price':
                self.handle_price_update(data)
            elif event_type == 'subscribe-status':
                self.handle_subscription_status(data)
            elif event_type == 'heartbeat':
                logger.debug("Heartbeat received")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    def on_websocket_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")

    def on_websocket_close(self, ws, close_status_code, close_msg):
        logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.connected = False
        
        if self.running:
            time.sleep(5)
            self.start_websocket()

    def subscribe_symbol(self, symbol):
        if not self.connected:
            return False
        
        try:
            subscribe_message = {
                "action": "subscribe",
                "params": {
                    "symbols": symbol
                }
            }
            
            self.ws.send(json.dumps(subscribe_message))
            self.subscribed_symbols.add(symbol)
            logger.info(f"Subscribed to {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to {symbol}: {e}")
            return False

    def handle_price_update(self, data):
        try:
            symbol = data.get('symbol')
            price = data.get('price')
            timestamp = data.get('timestamp')
            volume = data.get('day_volume', 0)
            change = data.get('change', 0)
            change_percent = data.get('change_percent', 0)
            
            if symbol and price:
                logger.info(f"Price update: {symbol} = ${price}")
                
                self.update_stock_price(symbol, price, change, change_percent, volume)
                
                self.broadcast_price_update(symbol, price, change, change_percent, volume, timestamp)
                
        except Exception as e:
            logger.error(f"Error handling price update: {e}")

    def handle_subscription_status(self, data):
        try:
            status = data.get('status')
            success_symbols = data.get('success', [])
            failed_symbols = data.get('fails', [])
            
            if status == 'ok' and success_symbols:
                for symbol_info in success_symbols:
                    symbol = symbol_info.get('symbol')
                    if symbol:
                        self.subscribed_symbols.add(symbol)
                        logger.info(f"Successfully subscribed to {symbol}")
            
            elif status == 'error' and failed_symbols:
                for symbol_info in failed_symbols:
                    symbol = symbol_info.get('symbol')
                    if symbol:
                        logger.warning(f"Failed to subscribe to {symbol}")
                        
        except Exception as e:
            logger.error(f"Error handling subscription status: {e}")

    def update_stock_price(self, symbol, price, change, change_percent, volume):
        try:
            stock = Stock.objects.filter(symbol=symbol).first()
            if stock:
                previous_close = stock.current_price

                stock.previous_close = previous_close
                stock.current_price = Decimal(str(price))
                stock.day_change = Decimal(str(change))
                stock.day_change_percent = Decimal(str(change_percent))
                stock.volume = int(volume)
                stock.last_price_update = timezone.now()
                stock.save()
                
                logger.info(f"Updated {symbol} price to ${price}")
                
        except Exception as e:
            logger.error(f"Failed to update stock price for {symbol}: {e}")

    def broadcast_price_update(self, symbol, price, change, change_percent, volume, timestamp):
        try:
            message = {
                'type': 'price_update',
                'symbol': symbol,
                'price': float(price),
                'change': float(change),
                'change_percent': float(change_percent),
                'volume': int(volume),
                'timestamp': timestamp
            }
            
            async_to_sync(self.channel_layer.group_send)(
                'market_data',
                {
                    'type': 'market_update',
                    'message': message
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to broadcast price update: {e}")

    def start_price_updates(self):
        def price_update_loop():
            while self.running:
                try:
                    for symbol in self.subscribed_symbols:
                        self.fetch_latest_price(symbol)
                    
                    time.sleep(self.price_update_interval)
                    
                except Exception as e:
                    logger.error(f"Error in price update loop: {e}")
                    time.sleep(10)
        
        self.price_update_thread = threading.Thread(target=price_update_loop, daemon=True)
        self.price_update_thread.start()
        logger.info("Price update thread started")

    def start_ohlc_updates(self):
        def ohlc_update_loop():
            while self.running:
                try:
                    for symbol in self.subscribed_symbols:
                        self.fetch_ohlc_data(symbol)
                    
                    time.sleep(self.ohlc_update_interval)
                    
                except Exception as e:
                    logger.error(f"Error in OHLC update loop: {e}")
                    time.sleep(60)
        
        self.ohlc_update_thread = threading.Thread(target=ohlc_update_loop, daemon=True)
        self.ohlc_update_thread.start()
        logger.info("OHLC update thread started")

    def fetch_latest_price(self, symbol):
        try:
            url = f"{self.base_url}/price"
            params = {
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'ok':
                    price = data.get('price')
                    if price:

                        self.update_stock_price(symbol, price, 0, 0, 0)
                        
        except Exception as e:
            logger.error(f"Failed to fetch price for {symbol}: {e}")

    def fetch_ohlc_data(self, symbol):
        try:
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': symbol,
                'interval': '1day',
                'outputsize': '30',  
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'ok':
                    values = data.get('values', [])
                    self.process_ohlc_data(symbol, values)
                    
        except Exception as e:
            logger.error(f"Failed to fetch OHLC data for {symbol}: {e}")

    def process_ohlc_data(self, symbol, values):
        try:
            stock = Stock.objects.filter(symbol=symbol).first()
            if not stock:
                return
            
            for value in values:
                date_str = value.get('datetime')
                open_price = value.get('open')
                high_price = value.get('high')
                low_price = value.get('low')
                close_price = value.get('close')
                volume = value.get('volume')
                
                if all([date_str, open_price, high_price, low_price, close_price]):
                    try:
                        date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
                    except:
                        continue
                    
                    market_data, created = MarketData.objects.get_or_create(
                        stock=stock,
                        date=date,
                        defaults={
                            'open_price': Decimal(str(open_price)),
                            'high_price': Decimal(str(high_price)),
                            'low_price': Decimal(str(low_price)),
                            'close_price': Decimal(str(close_price)),
                            'volume': int(volume) if volume else 0,
                            'adjusted_close': Decimal(str(close_price))
                        }
                    )
                    
                    if not created:

                        market_data.open_price = Decimal(str(open_price))
                        market_data.high_price = Decimal(str(high_price))
                        market_data.low_price = Decimal(str(low_price))
                        market_data.close_price = Decimal(str(close_price))
                        market_data.volume = int(volume) if volume else 0
                        market_data.adjusted_close = Decimal(str(close_price))
                        market_data.save()
            
            logger.info(f"Updated OHLC data for {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to process OHLC data for {symbol}: {e}")

    def populate_initial_data(self):
        try:
            for symbol in self.default_symbols:

                self.fetch_latest_price(symbol)
                
                self.fetch_ohlc_data(symbol)
                
                time.sleep(1)  
                
            logger.info("Initial data population completed")
            
        except Exception as e:
            logger.error(f"Failed to populate initial data: {e}")

    def get_stock_list(self):
        try:
            stocks = Stock.objects.filter(is_active=True).order_by('symbol')
            return [
                {
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'current_price': float(stock.current_price),
                    'day_change': float(stock.day_change),
                    'day_change_percent': float(stock.day_change_percent),
                    'volume': stock.volume,
                    'market_cap': stock.market_cap,
                    'pe_ratio': float(stock.pe_ratio) if stock.pe_ratio else None,
                    'dividend_yield': float(stock.dividend_yield) if stock.dividend_yield else None
                }
                for stock in stocks
            ]
        except Exception as e:
            logger.error(f"Failed to get stock list: {e}")
            return []

    def get_stock_detail(self, symbol):
        try:
            stock = Stock.objects.filter(symbol=symbol, is_active=True).first()
            if not stock:
                return None
            
            market_data = MarketData.objects.filter(stock=stock).order_by('-date')[:30]
            
            return {
                'symbol': stock.symbol,
                'name': stock.name,
                'exchange': stock.exchange,
                'sector': stock.sector,
                'industry': stock.industry,
                'current_price': float(stock.current_price),
                'previous_close': float(stock.previous_close),
                'day_change': float(stock.day_change),
                'day_change_percent': float(stock.day_change_percent),
                'volume': stock.volume,
                'avg_volume': stock.avg_volume,
                'market_cap': stock.market_cap,
                'pe_ratio': float(stock.pe_ratio) if stock.pe_ratio else None,
                'dividend_yield': float(stock.dividend_yield) if stock.pe_ratio else None,
                'last_price_update': stock.last_price_update.isoformat() if stock.last_price_update else None,
                'market_data': [
                    {
                        'date': data.date.isoformat(),
                        'open': float(data.open_price),
                        'high': float(data.high_price),
                        'low': float(data.low_price),
                        'close': float(data.close_price),
                        'volume': data.volume,
                        'adjusted_close': float(data.adjusted_close) if data.adjusted_close else None
                    }
                    for data in market_data
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get stock detail for {symbol}: {e}")
            return None

    def search_stocks(self, query):
        try:
            stocks = Stock.objects.filter(
                is_active=True
            ).filter(
                symbol__icontains=query
            ) | Stock.objects.filter(
                is_active=True
            ).filter(
                name__icontains=query
            )
            
            return [
                {
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'current_price': float(stock.current_price),
                    'day_change': float(stock.day_change),
                    'day_change_percent': float(stock.day_change_percent),
                    'volume': stock.volume
                }
                for stock in stocks[:20]  
            ]
            
        except Exception as e:
            logger.error(f"Failed to search stocks: {e}")
            return []

live_market_service = None

def get_live_market_service():
    global live_market_service
    if live_market_service is None:
        live_market_service = LiveMarketService()
    return live_market_service
