from django.core.management.base import BaseCommand
from trading.models import Stock
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Populate database with sample stock data'

    def handle(self, *args, **options):

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
                'volume': 50000000,
                'avg_volume': 55000000,
                'market_cap': 2750000000000,
                'pe_ratio': Decimal('28.50'),
                'dividend_yield': Decimal('0.50')
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
                'avg_volume': 28000000,
                'market_cap': 2850000000000,
                'pe_ratio': Decimal('32.10'),
                'dividend_yield': Decimal('0.80')
            },
            {
                'symbol': 'GOOGL',
                'name': 'Alphabet Inc.',
                'exchange': 'NASDAQ',
                'sector': 'Technology',
                'industry': 'Internet Services',
                'current_price': Decimal('142.80'),
                'previous_close': Decimal('141.50'),
                'day_change': Decimal('1.30'),
                'day_change_percent': Decimal('0.92'),
                'volume': 20000000,
                'avg_volume': 22000000,
                'market_cap': 1800000000000,
                'pe_ratio': Decimal('25.40'),
                'dividend_yield': Decimal('0.00')
            },
            {
                'symbol': 'AMZN',
                'name': 'Amazon.com Inc.',
                'exchange': 'NASDAQ',
                'sector': 'Consumer Discretionary',
                'industry': 'Internet Retail',
                'current_price': Decimal('145.20'),
                'previous_close': Decimal('144.80'),
                'day_change': Decimal('0.40'),
                'day_change_percent': Decimal('0.28'),
                'volume': 35000000,
                'avg_volume': 38000000,
                'market_cap': 1500000000000,
                'pe_ratio': Decimal('45.20'),
                'dividend_yield': Decimal('0.00')
            },
            {
                'symbol': 'TSLA',
                'name': 'Tesla Inc.',
                'exchange': 'NASDAQ',
                'sector': 'Consumer Discretionary',
                'industry': 'Auto Manufacturers',
                'current_price': Decimal('245.60'),
                'previous_close': Decimal('242.30'),
                'day_change': Decimal('3.30'),
                'day_change_percent': Decimal('1.36'),
                'volume': 80000000,
                'avg_volume': 85000000,
                'market_cap': 780000000000,
                'pe_ratio': Decimal('65.80'),
                'dividend_yield': Decimal('0.00')
            },
            {
                'symbol': 'META',
                'name': 'Meta Platforms Inc.',
                'exchange': 'NASDAQ',
                'sector': 'Technology',
                'industry': 'Internet Services',
                'current_price': Decimal('320.40'),
                'previous_close': Decimal('318.90'),
                'day_change': Decimal('1.50'),
                'day_change_percent': Decimal('0.47'),
                'volume': 18000000,
                'avg_volume': 20000000,
                'market_cap': 820000000000,
                'pe_ratio': Decimal('22.30'),
                'dividend_yield': Decimal('0.00')
            },
            {
                'symbol': 'NVDA',
                'name': 'NVIDIA Corporation',
                'exchange': 'NASDAQ',
                'sector': 'Technology',
                'industry': 'Semiconductors',
                'current_price': Decimal('485.90'),
                'previous_close': Decimal('482.50'),
                'day_change': Decimal('3.40'),
                'day_change_percent': Decimal('0.70'),
                'volume': 45000000,
                'avg_volume': 48000000,
                'market_cap': 1200000000000,
                'pe_ratio': Decimal('75.20'),
                'dividend_yield': Decimal('0.15')
            }
        ]

        created_count = 0
        updated_count = 0

        for stock_data in sample_stocks:
            stock, created = Stock.objects.update_or_create(
                symbol=stock_data['symbol'],
                defaults=stock_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created stock: {stock.symbol} - {stock.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated stock: {stock.symbol} - {stock.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(sample_stocks)} stocks. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )
