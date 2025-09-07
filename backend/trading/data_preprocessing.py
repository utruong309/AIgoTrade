import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from django.utils import timezone
from django.db.models import Q

from .models import MarketData, Stock, PredictionModel, PricePrediction
from .live_market_service import get_live_market_service

logger = logging.getLogger(__name__)


class DataPreprocessingService:
    
    def __init__(self):
        self.live_service = get_live_market_service()
    
    def get_historical_data(self, symbol: str, days: int = 365, 
                          time_period: str = '1day') -> Optional[pd.DataFrame]:
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
            
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            market_data = MarketData.objects.filter(
                stock=stock,
                timestamp__date__range=[start_date, end_date]
            ).order_by('timestamp')
            
            if len(market_data) < 30:
                logger.warning(f"Insufficient data for {symbol}: {len(market_data)} records")
                return None
            
            data = []
            for record in market_data:
                data.append({
                    'timestamp': record.timestamp,
                    'open_price': float(record.open_price),
                    'high_price': float(record.high_price),
                    'low_price': float(record.low_price),
                    'close_price': float(record.close_price),
                    'volume': float(record.volume)
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            
            df = self._clean_data(df)
            df = self._add_features(df)
            
            return df
            
        except Stock.DoesNotExist:
            logger.error(f"Stock {symbol} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return None
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.dropna()
        
        df = df[df['volume'] > 0]
        
        df = df[df['open_price'] > 0]
        df = df[df['high_price'] > 0]
        df = df[df['low_price'] > 0]
        df = df[df['close_price'] > 0]
        
        df = df[df['high_price'] >= df['low_price']]
        df = df[df['high_price'] >= df['open_price']]
        df = df[df['high_price'] >= df['close_price']]
        df = df[df['low_price'] <= df['open_price']]
        df = df[df['low_price'] <= df['close_price']]
        
        return df
    
    def _add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df['price_change'] = df['close_price'].pct_change()
        df['volume_change'] = df['volume'].pct_change()
        
        df['high_low_ratio'] = df['high_price'] / df['low_price']
        df['open_close_ratio'] = df['open_price'] / df['close_price']
        
        df['sma_5'] = df['close_price'].rolling(window=5).mean()
        df['sma_20'] = df['close_price'].rolling(window=20).mean()
        df['sma_50'] = df['close_price'].rolling(window=50).mean()
        
        df['rsi'] = self._calculate_rsi(df['close_price'])
        df['bollinger_upper'], df['bollinger_lower'] = self._calculate_bollinger_bands(df['close_price'])
        
        df = df.dropna()
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series]:
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return upper_band, lower_band
    
    def get_training_data_summary(self, symbol: str, days: int = 365) -> Dict:
        try:
            df = self.get_historical_data(symbol, days)
            
            if df is None or len(df) == 0:
                return {
                    'status': 'error',
                    'message': 'No data available'
                }
            
            summary = {
                'status': 'success',
                'symbol': symbol,
                'data_points': len(df),
                'date_range': {
                    'start': df.index.min().strftime('%Y-%m-%d'),
                    'end': df.index.max().strftime('%Y-%m-%d')
                },
                'price_stats': {
                    'min_price': float(df['close_price'].min()),
                    'max_price': float(df['close_price'].max()),
                    'avg_price': float(df['close_price'].mean()),
                    'std_price': float(df['close_price'].std())
                },
                'volume_stats': {
                    'min_volume': float(df['volume'].min()),
                    'max_volume': float(df['volume'].max()),
                    'avg_volume': float(df['volume'].mean()),
                    'std_volume': float(df['volume'].std())
                },
                'features': list(df.columns),
                'missing_data': df.isnull().sum().to_dict(),
                'data_quality': self._assess_data_quality(df)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting training data summary for {symbol}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _assess_data_quality(self, df: pd.DataFrame) -> Dict:
        quality_score = 100
        
        if len(df) < 100:
            quality_score -= 20
        
        missing_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
        quality_score -= missing_ratio * 50
        
        price_volatility = df['close_price'].pct_change().std()
        if price_volatility > 0.1:
            quality_score -= 10
        
        volume_consistency = df['volume'].std() / df['volume'].mean()
        if volume_consistency > 2:
            quality_score -= 10
        
        quality_score = max(0, min(100, quality_score))
        
        return {
            'score': quality_score,
            'rating': 'excellent' if quality_score >= 90 else
                     'good' if quality_score >= 70 else
                     'fair' if quality_score >= 50 else 'poor',
            'issues': self._identify_data_issues(df)
        }
    
    def _identify_data_issues(self, df: pd.DataFrame) -> List[str]:
        issues = []
        
        if len(df) < 100:
            issues.append("Insufficient data points")
        
        if df.isnull().sum().sum() > 0:
            issues.append("Missing values detected")
        
        if df['volume'].min() <= 0:
            issues.append("Zero or negative volume values")
        
        if df['close_price'].min() <= 0:
            issues.append("Zero or negative price values")
        
        price_changes = df['close_price'].pct_change().dropna()
        extreme_changes = price_changes[abs(price_changes) > 0.2]
        if len(extreme_changes) > len(df) * 0.05:
            issues.append("Excessive price volatility")
        
        return issues
    
    def validate_prediction_data(self, symbol: str) -> Dict:
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
            
            recent_data = MarketData.objects.filter(
                stock=stock
            ).order_by('-timestamp')[:60]
            
            if len(recent_data) < 30:
                return {
                    'status': 'error',
                    'message': 'Insufficient recent data for prediction'
                }
            
            latest_record = recent_data[0]
            
            validation_result = {
                'status': 'success',
                'symbol': symbol,
                'data_points': len(recent_data),
                'latest_timestamp': latest_record.timestamp.isoformat(),
                'latest_price': float(latest_record.close_price),
                'data_freshness': self._check_data_freshness(latest_record.timestamp),
                'data_completeness': self._check_data_completeness(recent_data)
            }
            
            return validation_result
            
        except Stock.DoesNotExist:
            return {
                'status': 'error',
                'message': f'Stock {symbol} not found'
            }
        except Exception as e:
            logger.error(f"Error validating prediction data for {symbol}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _check_data_freshness(self, timestamp) -> Dict:
        now = timezone.now()
        time_diff = now - timestamp
        
        if time_diff.total_seconds() < 3600:
            freshness = 'excellent'
        elif time_diff.total_seconds() < 86400:
            freshness = 'good'
        elif time_diff.total_seconds() < 604800:
            freshness = 'fair'
        else:
            freshness = 'poor'
        
        return {
            'status': freshness,
            'hours_old': time_diff.total_seconds() / 3600,
            'timestamp': timestamp.isoformat()
        }
    
    def _check_data_completeness(self, data) -> Dict:
        required_fields = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
        completeness_scores = {}
        
        for field in required_fields:
            valid_count = sum(1 for record in data if getattr(record, field) is not None and getattr(record, field) > 0)
            completeness_scores[field] = (valid_count / len(data)) * 100
        
        overall_completeness = sum(completeness_scores.values()) / len(completeness_scores)
        
        return {
            'overall_score': overall_completeness,
            'field_scores': completeness_scores,
            'rating': 'excellent' if overall_completeness >= 95 else
                     'good' if overall_completeness >= 85 else
                     'fair' if overall_completeness >= 70 else 'poor'
        }