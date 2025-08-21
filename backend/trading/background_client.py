import time
import threading
import logging
from .websocket_service import TwelveDataWebSocketService

logger = logging.getLogger(__name__)

class BackgroundWebSocketClient:
    def __init__(self):
        self.service = TwelveDataWebSocketService()
        self.running = False
        self.thread = None
        self.connection_thread = None
        
    def start(self):
        """Start the background WebSocket client"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            logger.info("Background WebSocket client started")
            
    def stop(self):
        """Stop the background WebSocket client"""
        self.running = False
        if self.service:
            self.service.disconnect()
        logger.info("Background WebSocket client stopped")
        
    def _run(self):
        """Main background loop for connection management"""
        while self.running:
            try:
                if not self.service.is_connected():
                    logger.info("Background client: attempting to connect...")
                    self._start_connection_thread()
                time.sleep(5)  # Check connection every 5 seconds
            except Exception as e:
                logger.error(f"Background client error: {e}")
                time.sleep(10)  # Wait longer on error
                
    def _start_connection_thread(self):
        """Start WebSocket connection in separate thread"""
        if self.connection_thread and self.connection_thread.is_alive():
            return
            
        self.connection_thread = threading.Thread(
            target=self._connection_worker, 
            daemon=True
        )
        self.connection_thread.start()
        
    def _connection_worker(self):
        """Worker thread for WebSocket connection"""
        try:
            logger.info("Starting WebSocket connection...")
            self.service.connect()
        except Exception as e:
            logger.error(f"Connection worker error: {e}")
            
    def get_service(self):
        """Get the WebSocket service instance"""
        return self.service
        
    def is_running(self):
        """Check if client is running"""
        return self.running
        
    def get_status(self):
        """Get comprehensive client status"""
        return {
            'client_running': self.running,
            'service_connected': self.service.is_connected() if self.service else False,
            'subscribed_symbols': self.service.get_subscribed_symbols() if self.service else [],
            'connection_status': self.service.get_connection_status() if self.service else {}
        }
        
    def add_symbol(self, symbol):
        """Add symbol to subscription list"""
        if self.service and self.service.is_connected():
            return self.service.subscribe_symbol(symbol)
        return False
        
    def remove_symbol(self, symbol):
        """Remove symbol from subscription list"""
        if self.service and self.service.is_connected():
            return self.service.unsubscribe_symbol(symbol)
        return False
        
    def reset_subscriptions(self):
        """Reset all subscriptions"""
        if self.service and self.service.is_connected():
            return self.service.reset_subscriptions()
        return False