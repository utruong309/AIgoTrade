from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from trading.models import Stock, PredictionModel, PricePrediction
import uuid


class Command(BaseCommand):
    help = 'Create sample stocks and predictions for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample stocks and predictions...')
        
        sample_stocks = [
            {
                'symbol': 'AAPL',
                'name': 'Apple Inc.',
                'exchange': 'NASDAQ',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'current_price': Decimal('175.50'),
                'previous_close': Decimal('174.20'),
                'day_change': Decimal('1.30'),
                'day_change_percent': Decimal('0.75'),
                'volume': 45000000,
                'avg_volume': 50000000,
                'pe_ratio': Decimal('28.5'),
                'market_cap': 2800000000000,
            },
            {
                'symbol': 'MSFT',
                'name': 'Microsoft Corporation',
                'exchange': 'NASDAQ',
                'sector': 'Technology',
                'industry': 'Software',
                'current_price': Decimal('380.25'),
                'previous_close': Decimal('378.90'),
                'day_change': Decimal('1.35'),
                'day_change_percent': Decimal('0.36'),
                'volume': 25000000,
                'avg_volume': 30000000,
                'pe_ratio': Decimal('32.1'),
                'market_cap': 2800000000000,
            },
            {
                'symbol': 'GOOGL',
                'name': 'Alphabet Inc.',
                'exchange': 'NASDAQ',
                'sector': 'Technology',
                'industry': 'Internet',
                'current_price': Decimal('142.80'),
                'previous_close': Decimal('141.50'),
                'day_change': Decimal('1.30'),
                'day_change_percent': Decimal('0.92'),
                'volume': 20000000,
                'avg_volume': 25000000,
                'pe_ratio': Decimal('25.8'),
                'market_cap': 1800000000000,
            },
            {
                'symbol': 'AMZN',
                'name': 'Amazon.com Inc.',
                'exchange': 'NASDAQ',
                'sector': 'Consumer Discretionary',
                'industry': 'E-commerce',
                'current_price': Decimal('155.40'),
                'previous_close': Decimal('154.20'),
                'day_change': Decimal('1.20'),
                'day_change_percent': Decimal('0.78'),
                'volume': 30000000,
                'avg_volume': 35000000,
                'pe_ratio': Decimal('45.2'),
                'market_cap': 1600000000000,
            },
            {
                'symbol': 'TSLA',
                'name': 'Tesla Inc.',
                'exchange': 'NASDAQ',
                'sector': 'Consumer Discretionary',
                'industry': 'Electric Vehicles',
                'current_price': Decimal('245.60'),
                'previous_close': Decimal('242.30'),
                'day_change': Decimal('3.30'),
                'day_change_percent': Decimal('1.36'),
                'volume': 60000000,
                'avg_volume': 70000000,
                'pe_ratio': Decimal('65.4'),
                'market_cap': 780000000000,
            },
            {
                'symbol': 'NVDA',
                'name': 'NVIDIA Corporation',
                'exchange': 'NASDAQ',
                'sector': 'Technology',
                'industry': 'Semiconductors',
                'current_price': Decimal('485.20'),
                'previous_close': Decimal('478.90'),
                'day_change': Decimal('6.30'),
                'day_change_percent': Decimal('1.32'),
                'volume': 40000000,
                'avg_volume': 45000000,
                'pe_ratio': Decimal('68.9'),
                'market_cap': 1200000000000,
            }
        ]
        
        created_stocks = []
        for stock_data in sample_stocks:
            stock, created = Stock.objects.get_or_create(
                symbol=stock_data['symbol'],
                defaults=stock_data
            )
            if created:
                self.stdout.write(f'Created stock: {stock.symbol}')
            else:
                self.stdout.write(f'Stock already exists: {stock.symbol}')
            created_stocks.append(stock)
        
        for stock in created_stocks:
            model, created = PredictionModel.objects.get_or_create(
                stock=stock,
                model_type='lstm',
                defaults={
                    'status': 'trained',
                    'sequence_length': 60,
                    'training_data_points': 1000,
                    'training_start_date': timezone.now().date(),
                    'training_end_date': timezone.now().date(),
                    'train_rmse': Decimal('2.5'),
                    'val_rmse': Decimal('3.1'),
                    'train_mae': Decimal('1.8'),
                    'val_mae': Decimal('2.2'),
                    'model_file_path': f'models/{stock.symbol.lower()}_lstm_model.pkl',
                    'scaler_file_path': f'models/{stock.symbol.lower()}_scaler.pkl',
                    'metadata_file_path': f'models/{stock.symbol.lower()}_metadata.json',
                }
            )
            if created:
                self.stdout.write(f'Created prediction model for: {stock.symbol}')
            else:
                self.stdout.write(f'Prediction model already exists for: {stock.symbol}')
        
        for stock in created_stocks:
            for i in range(3):
                prediction_time = timezone.now() - timezone.timedelta(hours=i*2)

                base_price = float(stock.current_price)
                variation = (i - 1) * 0.02  
                predicted_price = Decimal(str(base_price * (1 + variation)))
                
                price_change = predicted_price - stock.current_price
                price_change_percent = (price_change / stock.current_price) * 100
                
                if abs(variation) < 0.01:
                    confidence_score = Decimal('0.85')
                    confidence_level = 'high'
                elif abs(variation) < 0.02:
                    confidence_score = Decimal('0.72')
                    confidence_level = 'medium'
                else:
                    confidence_score = Decimal('0.58')
                    confidence_level = 'low'
                
                prediction, created = PricePrediction.objects.get_or_create(
                    stock=stock,
                    prediction_model=PredictionModel.objects.get(stock=stock, model_type='lstm'),
                    prediction_type='future',
                    prediction_timestamp=prediction_time,
                    defaults={
                        'predicted_price': predicted_price,
                        'current_price': stock.current_price,
                        'price_change': price_change,
                        'price_change_percent': price_change_percent,
                        'confidence_score': confidence_score,
                        'confidence_level': confidence_level,
                        'prediction_date': prediction_time.date(),
                        'input_features': {'volume': stock.volume, 'price': float(stock.current_price)},
                        'model_metadata': {'model_type': 'lstm', 'version': '1.0'},
                    }
                )
                if created:
                    self.stdout.write(f'Created prediction for: {stock.symbol} at {prediction_time}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(created_stocks)} stocks with predictions!'
            )
        )