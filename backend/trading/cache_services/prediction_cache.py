import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class PredictionCacheService:
    
    def __init__(self):
        self.redis_client = None
        self.cache_timeout = 900
        self.prefix = "prediction:"
        
        try:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://redis:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Redis connection established for prediction caching")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def _get_cache_key(self, symbol: str, cache_type: str = "prediction") -> str:
        return f"{self.prefix}{cache_type}:{symbol.upper()}"
    
    def cache_prediction(self, symbol: str, prediction_data: Dict, 
                        timeout: Optional[int] = None) -> bool:
        try:
            if not self.redis_client:
                return False
            
            cache_key = self._get_cache_key(symbol, "prediction")
            timeout = timeout or self.cache_timeout
            
            cache_data = {
                'data': prediction_data,
                'timestamp': timezone.now().isoformat(),
                'symbol': symbol.upper()
            }
            
            self.redis_client.setex(
                cache_key,
                timeout,
                json.dumps(cache_data)
            )
            
            logger.debug(f"Cached prediction for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching prediction for {symbol}: {str(e)}")
            return False
    
    def get_cached_prediction(self, symbol: str) -> Optional[Dict]:
        try:
            if not self.redis_client:
                return None
            
            cache_key = self._get_cache_key(symbol, "prediction")
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Retrieved cached prediction for {symbol}")
                return data['data']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached prediction for {symbol}: {str(e)}")
            return None
    
    def cache_batch_predictions(self, predictions: List[Dict], 
                               timeout: Optional[int] = None) -> int:
        try:
            if not self.redis_client:
                return 0
            
            timeout = timeout or self.cache_timeout
            cached_count = 0
            
            pipe = self.redis_client.pipeline()
            
            for prediction in predictions:
                symbol = prediction.get('symbol', '').upper()
                if symbol:
                    cache_key = self._get_cache_key(symbol, "prediction")
                    cache_data = {
                        'data': prediction,
                        'timestamp': timezone.now().isoformat(),
                        'symbol': symbol
                    }
                    
                    pipe.setex(cache_key, timeout, json.dumps(cache_data))
                    cached_count += 1
            
            pipe.execute()
            
            logger.info(f"Cached {cached_count} batch predictions")
            return cached_count
            
        except Exception as e:
            logger.error(f"Error caching batch predictions: {str(e)}")
            return 0
    
    def get_cached_predictions(self, symbols: List[str]) -> Dict[str, Dict]:
        try:
            if not self.redis_client:
                return {}
            
            cache_keys = [self._get_cache_key(symbol, "prediction") for symbol in symbols]
            cached_data = self.redis_client.mget(cache_keys)
            
            results = {}
            for i, data in enumerate(cached_data):
                if data:
                    parsed_data = json.loads(data)
                    symbol = symbols[i].upper()
                    results[symbol] = parsed_data['data']
            
            logger.debug(f"Retrieved {len(results)} cached predictions")
            return results
            
        except Exception as e:
            logger.error(f"Error getting cached predictions: {str(e)}")
            return {}
    
    def invalidate_prediction(self, symbol: str) -> bool:
        try:
            if not self.redis_client:
                return False
            
            cache_key = self._get_cache_key(symbol, "prediction")
            result = self.redis_client.delete(cache_key)
            
            if result:
                logger.debug(f"Invalidated cached prediction for {symbol}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error invalidating prediction for {symbol}: {str(e)}")
            return False
    
    def invalidate_predictions(self, symbols: List[str]) -> int:
        try:
            if not self.redis_client:
                return 0
            
            cache_keys = [self._get_cache_key(symbol, "prediction") for symbol in symbols]
            result = self.redis_client.delete(*cache_keys)
            
            logger.info(f"Invalidated {result} cached predictions")
            return result
            
        except Exception as e:
            logger.error(f"Error invalidating predictions: {str(e)}")
            return 0
    
    def cleanup_expired(self) -> int:
        try:
            if not self.redis_client:
                return 0
            
            pattern = f"{self.prefix}prediction:*"
            keys = self.redis_client.keys(pattern)
            
            if not keys:
                return 0
            
            expired_count = 0
            current_time = timezone.now()
            
            for key in keys:
                try:
                    cached_data = self.redis_client.get(key)
                    if cached_data:
                        data = json.loads(cached_data)
                        timestamp_str = data.get('timestamp')
                        
                        if timestamp_str:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            age = current_time - timestamp
                            
                            if age.total_seconds() > self.cache_timeout:
                                self.redis_client.delete(key)
                                expired_count += 1
                
                except Exception as e:
                    logger.error(f"Error processing cache key {key}: {str(e)}")
                    continue
            
            logger.info(f"Cleaned up {expired_count} expired cache entries")
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {str(e)}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        try:
            if not self.redis_client:
                return {
                    'status': 'redis_unavailable',
                    'total_keys': 0,
                    'prediction_keys': 0,
                    'memory_usage': 0
                }
            
            pattern = f"{self.prefix}prediction:*"
            prediction_keys = self.redis_client.keys(pattern)
            
            info = self.redis_client.info()
            
            stats = {
                'status': 'active',
                'total_keys': info.get('db0', {}).get('keys', 0),
                'prediction_keys': len(prediction_keys),
                'memory_usage': info.get('used_memory_human', '0B'),
                'connected_clients': info.get('connected_clients', 0),
                'uptime': info.get('uptime_in_seconds', 0)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        try:
            if not self.redis_client:
                return False
            
            ttl = ttl or self.cache_timeout
            self.redis_client.setex(key, ttl, json.dumps(value))
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        try:
            if not self.redis_client:
                return None
            
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        try:
            if not self.redis_client:
                return False
            
            result = self.redis_client.delete(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        try:
            if not self.redis_client:
                return False
            
            return bool(self.redis_client.exists(key))
            
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {str(e)}")
            return False


prediction_cache_service = PredictionCacheService()