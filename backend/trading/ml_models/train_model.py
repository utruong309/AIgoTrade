import os
import sys
import django
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aigo_trade.settings')
django.setup()

from trading.models import MarketData, Stock
from trading.ml_models.lstm_model import StockPricePredictor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_training_data(symbol: str, days: int = 365) -> pd.DataFrame:
    
    try:
        stock = Stock.objects.get(symbol=symbol.upper())
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        market_data = MarketData.objects.filter(
            stock=stock,
            date__gte=start_date,
            date__lte=end_date,
            time_period='1day'
        ).order_by('date')
        
        if len(market_data) < 100:  
            logger.warning(f"Insufficient data for {symbol}: {len(market_data)} records")
            return None
        
        data = []
        for record in market_data:
            data.append({
                'date': record.date,
                'open_price': float(record.open_price),
                'high_price': float(record.high_price),
                'low_price': float(record.low_price),
                'close_price': float(record.close_price),
                'volume': float(record.volume)
            })
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        logger.info(f"Retrieved {len(df)} records for {symbol}")
        return df
        
    except Stock.DoesNotExist:
        logger.error(f"Stock {symbol} not found in database")
        return None
    except Exception as e:
        logger.error(f"Error retrieving data for {symbol}: {e}")
        return None


def train_model_for_symbol(symbol: str, days: int = 365, epochs: int = 100) -> bool:
    
    try:
        logger.info(f"Starting training for {symbol}")
        
        df = get_training_data(symbol, days)
        if df is None or len(df) < 100:
            logger.error(f"Insufficient data for {symbol}")
            return False
        
        model_path = f"models/{symbol.lower()}/"
        predictor = StockPricePredictor(model_path=model_path)
        
        metrics = predictor.train_model(df, epochs=epochs)
        
        logger.info(f"Training completed for {symbol}")
        logger.info(f"Final metrics - Train RMSE: {metrics['train_rmse']:.4f}, Val RMSE: {metrics['val_rmse']:.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error training model for {symbol}: {e}")
        return False


def train_models_for_active_stocks(days: int = 365, epochs: int = 100, limit: int = 10):
    
    try:
        stocks = Stock.objects.filter(is_active=True)[:limit]
        
        successful_trains = 0
        failed_trains = 0
        
        for stock in stocks:
            logger.info(f"Training model for {stock.symbol} ({stock.name})")
            
            success = train_model_for_symbol(stock.symbol, days, epochs)
            
            if success:
                successful_trains += 1
            else:
                failed_trains += 1
        
        logger.info(f"Training completed. Success: {successful_trains}, Failed: {failed_trains}")
        
    except Exception as e:
        logger.error(f"Error in batch training: {e}")


def test_prediction(symbol: str) -> dict:
    try:
        model_path = f"models/{symbol.lower()}/"
        predictor = StockPricePredictor(model_path=model_path)
        predictor.load_model(symbol)

        df = get_training_data(symbol, days=90)  
        if df is None:
            return {'error': 'No data available'}
        
        prediction = predictor.predict_next_price(df)
        
        logger.info(f"Prediction for {symbol}: {prediction}")
        return prediction
        
    except Exception as e:
        logger.error(f"Error testing prediction for {symbol}: {e}")
        return {'error': str(e)}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train LSTM models for stock prediction')
    parser.add_argument('--symbol', type=str, help='Stock symbol to train')
    parser.add_argument('--days', type=int, default=365, help='Days of historical data')
    parser.add_argument('--epochs', type=int, default=100, help='Training epochs')
    parser.add_argument('--batch', action='store_true', help='Train models for multiple stocks')
    parser.add_argument('--test', type=str, help='Test prediction for symbol')
    parser.add_argument('--limit', type=int, default=10, help='Limit for batch training')
    
    args = parser.parse_args()
    
    if args.test:
        result = test_prediction(args.test)
        print(f"Test result for {args.test}: {result}")
    elif args.symbol:
        success = train_model_for_symbol(args.symbol, args.days, args.epochs)
        print(f"Training {'successful' if success else 'failed'} for {args.symbol}")
    elif args.batch:
        train_models_for_active_stocks(args.days, args.epochs, args.limit)
    else:
        print("Please specify --symbol, --batch, or --test")