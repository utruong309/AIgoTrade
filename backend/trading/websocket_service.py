import json
import asyncio
import websocket
import time
import threading
from django.conf import settings
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class TwelveDataWebSocketService:
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY')
        if not self.api_key:
            raise ValueError("TWELVEDATA_API_KEY not found in environment variables")
            
        self.base_url = f"wss://ws.twelvedata.com/v1/quotes/price?apikey={self.api_key}"
        self.ws = None
        self.connected = False
        self.subscribed_symbols = set()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5
        self.heartbeat_interval = 10
        self.last_heartbeat = time.time()
        
        self.default_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "BRK.A", "JPM", "JNJ"]
        
    def connect(self):
        try:
            logger.info("Attempting to connect to TwelveData WebSocket...")
            
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            self.ws = websocket.WebSocketApp(
                self.base_url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            
            self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.connected = False
            self._handle_reconnection()
            
    def on_open(self, _ws):
        logger.info("WebSocket connected to TwelveData!")
        self.connected = True
        self.reconnect_attempts = 0
        
        for symbol in self.default_symbols:
            self.subscribe_symbol(symbol)
            
        self._start_heartbeat()
        
    def on_message(self, _ws, message):
        try:
            data = json.loads(message)
            logger.info(f"Received: {data}")
            
            event_type = data.get('event', 'unknown')
            
            if event_type == 'price':
                self.handle_price_update(data)
            elif event_type == 'status':
                self.handle_status_event(data)
            elif event_type == 'subscribe-status':
                self.handle_subscribe_status(data)
            elif event_type == 'heartbeat':
                logger.debug("Heartbeat received from server")
            elif event_type == 'message-processing':
                if self._handle_rate_limit(data):
                    return
            else:
                logger.info(f"Unknown event type: {event_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            
    def on_error(self, _ws, error):
        logger.error(f"WebSocket error: {error}")
        self.connected = False
        
    def on_close(self, _ws, close_status_code, close_msg):
        logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.connected = False
        
        if close_status_code != 1000:
            self._handle_reconnection()
            
    def handle_status_event(self, data):
        action = data.get('action', '')
        symbols = data.get('symbols', '')
        status = data.get('status', '')
        
        if action == 'subscribe' and status == 'subscribed':
            logger.info(f"Successfully subscribed to: {symbols}")
            if symbols:
                for symbol in symbols.split(','):
                    self.subscribed_symbols.add(symbol.strip())
        elif action == 'unsubscribe':
            logger.info(f"Unsubscribed from: {symbols}")
            if symbols:
                for symbol in symbols.split(','):
                    self.subscribed_symbols.discard(symbol.strip())
        elif action == 'reset':
            logger.info("All subscriptions reset")
            self.subscribed_symbols.clear()
            
    def handle_subscribe_status(self, data):
        status = data.get('status', '')
        success = data.get('success', [])
        fails = data.get('fails', [])
        
        if status == 'ok':
            if success:
                for item in success:
                    symbol = item.get('symbol', '')
                    if symbol:
                        logger.info(f"Successfully subscribed to {symbol}")
                        self.subscribed_symbols.add(symbol)
        elif status == 'error':
            if fails:
                for item in fails:
                    symbol = item.get('symbol', '')
                    if symbol:
                        logger.warning(f"Failed to subscribe to {symbol}")
                        self._retry_subscription(symbol)
                        
    def _retry_subscription(self, symbol):
        try:
            retry_symbols = [symbol, symbol.upper(), symbol.lower()]
            
            for retry_symbol in retry_symbols:
                subscribe_message = {
                    "action": "subscribe",
                    "params": {
                        "symbols": retry_symbol
                    }
                }
                self.ws.send(json.dumps(subscribe_message))
                logger.info(f"Retrying subscription for {retry_symbol}")
                break
                
        except Exception as e:
            logger.error(f"Retry subscription failed for {symbol}: {e}")
    def _handle_rate_limit(self, data):
        messages = data.get('messages', [])
        for message in messages:
            if 'exceeds the limit of 100 events per minute' in message:
                logger.warning("Rate limit exceeded. Waiting 60 seconds before retrying...")
                time.sleep(60)
            return True
        return False
            
    def subscribe_symbol(self, symbol):
        if self.connected and self.ws:
            try:
                subscribe_message = {
                    "action": "subscribe",
                    "params": {
                        "symbols": symbol
                    }
                }
                
                self.ws.send(json.dumps(subscribe_message))
                logger.info(f"Subscribed to {symbol}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to subscribe to {symbol}: {e}")
                return False
        else:
            logger.warning(f"Cannot subscribe to {symbol}: not connected")
            return False
            
    def unsubscribe_symbol(self, symbol):
        if self.connected and self.ws:
            try:
                unsubscribe_message = {
                    "action": "unsubscribe",
                    "params": {
                        "symbols": symbol
                    }
                }
                
                self.ws.send(json.dumps(unsubscribe_message))
                self.subscribed_symbols.discard(symbol)
                logger.info(f"Unsubscribed from {symbol}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to unsubscribe from {symbol}: {e}")
                return False
        return False
        
    def handle_price_update(self, data):
        try:
            symbol = data.get('symbol')
            price = data.get('price')
            timestamp = data.get('timestamp')
            day_volume = data.get('day_volume', 0)
            instrument_type = data.get('type', 'unknown')
            
            if symbol and price:
                logger.info(f"Price update: {symbol} = ${price} (Volume: {day_volume}) at {timestamp}")
                
                dt = self._convert_timestamp(timestamp)
                self._update_database(symbol, price, dt, day_volume, instrument_type)
                
            else:
                logger.warning(f"Incomplete price data: {data}")
                
        except Exception as e:
            logger.error(f"Error handling price update: {e}")
            
    def _convert_timestamp(self, timestamp):
        from django.utils import timezone
        from datetime import datetime
        
        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        else:
            return timezone.now()
            
    def _update_database(self, symbol, price, timestamp, day_volume, instrument_type):
        try:
            from .models import Stock, MarketData
            
            stock, created = Stock.objects.get_or_create(
                symbol=symbol,
                defaults={
                    'name': symbol,
                    'current_price': price,
                    'last_updated': timestamp,
                    'volume': day_volume,
                    'instrument_type': instrument_type
                }
            )
            
            if not created:
                stock.current_price = price
                stock.last_updated = timestamp
                stock.volume = day_volume
                stock.save()
                
            MarketData.objects.create(
                stock=stock,
                open_price=price,
                high_price=price,
                low_price=price,
                close_price=price,
                volume=day_volume,
                timestamp=timestamp
            )
            
            logger.info(f"Database updated for {symbol}")
            
        except Exception as e:
            logger.error(f"Database update failed for {symbol}: {e}")
            
    def _emit_price_event(self, symbol, price, timestamp, day_volume, change, change_percent):
        try:
            event_data = {
                'type': 'price_update',
                'symbol': symbol,
                'price': price,
                'timestamp': timestamp,
                'volume': day_volume,
                'change': change,
                'change_percent': change_percent
            }
            
            logger.debug(f"Price event emitted for {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to emit price event: {e}")
            
    def _start_heartbeat(self):
        def heartbeat_loop():
            while self.connected:
                try:
                    current_time = time.time()
                    if current_time - self.last_heartbeat >= self.heartbeat_interval:
                        self._send_heartbeat()
                        self.last_heartbeat = current_time
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
                    break
                    
        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        logger.info("Heartbeat thread started")
        
    def _send_heartbeat(self):
        if self.connected and self.ws:
            try:
                heartbeat_message = {"action": "heartbeat"}
                self.ws.send(json.dumps(heartbeat_message))
                logger.debug("Heartbeat sent")
            except Exception as e:
                logger.error(f"Heartbeat send failed: {e}")
                
    def _handle_reconnection(self):
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            wait_time = min(60, self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)))
            
            logger.info(f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} in {wait_time} seconds...")
            
            time.sleep(wait_time)
            self.connect()
        else:
            logger.error(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached")
            
    def reset_subscriptions(self):
        if self.connected and self.ws:
            try:
                reset_message = {"action": "reset"}
                self.ws.send(json.dumps(reset_message))
                self.subscribed_symbols.clear()
                logger.info("All subscriptions reset")
                return True
            except Exception as e:
                logger.error(f"Reset failed: {e}")
                return False
        return False
        
    def send_message(self, message):
        if self.connected and self.ws:
            try:
                self.ws.send(json.dumps(message))
                logger.info(f"Message sent: {message}")
                return True
            except Exception as e:
                logger.error(f"Send error: {e}")
                return False
        else:
            logger.warning("Cannot send message: not connected")
            return False
            
    def disconnect(self):
        if self.ws:
            logger.info("Disconnecting from TwelveData...")
            self.ws.close()
            self.connected = False
            self.subscribed_symbols.clear()
            
    def is_connected(self):
        return self.connected
        
    def get_subscribed_symbols(self):
        return list(self.subscribed_symbols)
        
    def get_connection_status(self):
        return {
            'connected': self.connected,
            'subscribed_symbols': list(self.subscribed_symbols),
            'reconnect_attempts': self.reconnect_attempts,
            'last_heartbeat': self.last_heartbeat
        }
        
    def start_background_connection(self):
        def run_websocket():
            while True:
                try:
                    if not self.connected:
                        logger.info("Background connection: attempting to connect...")
                        self.connect()
                    time.sleep(5)
                except Exception as e:
                    logger.error(f"Background connection error: {e}")
                    time.sleep(10)
                    
        thread = threading.Thread(target=run_websocket, daemon=True)
        thread.start()
        logger.info("Background WebSocket thread started")
        return thread