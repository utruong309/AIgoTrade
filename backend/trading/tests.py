from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from datetime import datetime, date
from django.utils import timezone

from .models import Stock, Portfolio, Holding, Transaction

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for User model"""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'risk_tolerance': 'moderate',
            'investment_experience': 'beginner'
        }
    
    def test_create_user(self):
        """Test creating a user"""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.risk_tolerance, 'moderate')
        self.assertEqual(user.investment_experience, 'beginner')
        self.assertFalse(user.is_verified)
        self.assertTrue(user.check_password('testpass123'))
    
    def test_user_str_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(**self.user_data)
        expected_str = f"{user.username} ({user.email})"
        self.assertEqual(str(user), expected_str)
    
    def test_email_unique_constraint(self):
        """Test that email must be unique"""
        User.objects.create_user(**self.user_data)
        
        duplicate_user_data = self.user_data.copy()
        duplicate_user_data['username'] = 'different_username'
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(**duplicate_user_data)
    
    def test_default_risk_tolerance(self):
        """Test default risk tolerance"""
        user_data = self.user_data.copy()
        del user_data['risk_tolerance']
        
        user = User.objects.create_user(**user_data)
        self.assertEqual(user.risk_tolerance, 'moderate')


class StockModelTest(TestCase):
    """Test cases for Stock model"""
    
    def setUp(self):
        self.stock_data = {
            'symbol': 'AAPL',
            'name': 'Apple Inc.',
            'exchange': 'NASDAQ',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'market_cap': 3000000000000,  # $3T
            'current_price': Decimal('150.25'),
            'previous_close': Decimal('149.50'),
            'day_change': Decimal('0.75'),
            'day_change_percent': Decimal('0.50'),
            'volume': 50000000,
            'avg_volume': 45000000
        }
    
    def test_create_stock(self):
        """Test creating a stock"""
        stock = Stock.objects.create(**self.stock_data)
        
        self.assertEqual(stock.symbol, 'AAPL')
        self.assertEqual(stock.name, 'Apple Inc.')
        self.assertEqual(stock.current_price, Decimal('150.25'))
        self.assertTrue(stock.is_active)
    
    def test_stock_str_representation(self):
        """Test stock string representation"""
        stock = Stock.objects.create(**self.stock_data)
        expected_str = f"{stock.symbol} - {stock.name}"
        self.assertEqual(str(stock), expected_str)
    
    def test_symbol_unique_constraint(self):
        """Test that stock symbol must be unique"""
        Stock.objects.create(**self.stock_data)
        
        with self.assertRaises(IntegrityError):
            Stock.objects.create(**self.stock_data)
    
    def test_market_cap_display_property(self):
        """Test market cap display formatting"""
        # Test trillion
        stock = Stock.objects.create(**self.stock_data)
        self.assertEqual(stock.market_cap_display, "$3.0T")
        
        # Test billion
        stock.market_cap = 500000000000  # $500B
        self.assertEqual(stock.market_cap_display, "$500.0B")
        
        # Test million
        stock.market_cap = 5000000000  # $5B
        self.assertEqual(stock.market_cap_display, "$5.0B")
        
        # Test None
        stock.market_cap = None
        self.assertEqual(stock.market_cap_display, "N/A")


class PortfolioModelTest(TestCase):
    """Test cases for Portfolio model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.portfolio_data = {
            'user': self.user,
            'name': 'Test Portfolio',
            'description': 'A test portfolio',
            'cash_balance': Decimal('10000.00')
        }
    
    def test_create_portfolio(self):
        """Test creating a portfolio"""
        portfolio = Portfolio.objects.create(**self.portfolio_data)
        
        self.assertEqual(portfolio.name, 'Test Portfolio')
        self.assertEqual(portfolio.user, self.user)
        self.assertEqual(portfolio.cash_balance, Decimal('10000.00'))
        self.assertFalse(portfolio.is_default)
        self.assertTrue(portfolio.is_active)
    
    def test_portfolio_str_representation(self):
        """Test portfolio string representation"""
        portfolio = Portfolio.objects.create(**self.portfolio_data)
        expected_str = f"{self.user.username} - {portfolio.name}"
        self.assertEqual(str(portfolio), expected_str)
    
    def test_unique_portfolio_name_per_user(self):
        """Test that portfolio names must be unique per user"""
        Portfolio.objects.create(**self.portfolio_data)
        
        with self.assertRaises(IntegrityError):
            Portfolio.objects.create(**self.portfolio_data)
    
    def test_default_portfolio_constraint(self):
        """Test that only one portfolio can be default per user"""
        portfolio1 = Portfolio.objects.create(**self.portfolio_data)
        portfolio1.is_default = True
        portfolio1.save()
        
        portfolio2_data = self.portfolio_data.copy()
        portfolio2_data['name'] = 'Second Portfolio'
        portfolio2 = Portfolio.objects.create(**portfolio2_data)
        portfolio2.is_default = True
        portfolio2.save()
        
        # Refresh portfolio1 from database
        portfolio1.refresh_from_db()
        
        # portfolio1 should no longer be default
        self.assertFalse(portfolio1.is_default)
        self.assertTrue(portfolio2.is_default)


class HoldingModelTest(TestCase):
    """Test cases for Holding model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name='Test Portfolio',
            cash_balance=Decimal('10000.00')
        )
        self.stock = Stock.objects.create(
            symbol='AAPL',
            name='Apple Inc.',
            exchange='NASDAQ',
            current_price=Decimal('150.00')
        )
        self.holding_data = {
            'portfolio': self.portfolio,
            'stock': self.stock,
            'quantity': Decimal('10.0'),
            'average_cost': Decimal('145.00'),
            'total_cost': Decimal('1450.00'),
            'first_purchase_date': timezone.now(),
            'last_transaction_date': timezone.now()
        }
    
    def test_create_holding(self):
        """Test creating a holding"""
        holding = Holding.objects.create(**self.holding_data)
        
        self.assertEqual(holding.portfolio, self.portfolio)
        self.assertEqual(holding.stock, self.stock)
        self.assertEqual(holding.quantity, Decimal('10.0'))
        self.assertEqual(holding.average_cost, Decimal('145.00'))
    
    def test_holding_str_representation(self):
        """Test holding string representation"""
        holding = Holding.objects.create(**self.holding_data)
        expected_str = f"{self.portfolio.name} - {self.stock.symbol}: {holding.quantity} shares"
        self.assertEqual(str(holding), expected_str)
    
    def test_current_price_property(self):
        """Test current price property"""
        holding = Holding.objects.create(**self.holding_data)
        self.assertEqual(holding.current_price, self.stock.current_price)
    
    def test_update_metrics_method(self):
        """Test update metrics method"""
        holding = Holding.objects.create(**self.holding_data)
        holding.update_metrics()
        
        expected_current_value = holding.quantity * self.stock.current_price
        expected_gain_loss = expected_current_value - holding.total_cost
        expected_gain_loss_percent = (expected_gain_loss / holding.total_cost) * 100
        
        self.assertEqual(holding.current_value, expected_current_value)
        self.assertEqual(holding.unrealized_gain_loss, expected_gain_loss)
        self.assertEqual(holding.unrealized_gain_loss_percent, expected_gain_loss_percent)
    
    def test_unique_holding_per_portfolio_stock(self):
        """Test that holdings are unique per portfolio-stock combination"""
        Holding.objects.create(**self.holding_data)
        
        with self.assertRaises(IntegrityError):
            Holding.objects.create(**self.holding_data)


class TransactionModelTest(TestCase):
    """Test cases for Transaction model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name='Test Portfolio',
            cash_balance=Decimal('10000.00')
        )
        self.stock = Stock.objects.create(
            symbol='AAPL',
            name='Apple Inc.',
            exchange='NASDAQ',
            current_price=Decimal('150.00')
        )
        self.transaction_data = {
            'portfolio': self.portfolio,
            'stock': self.stock,
            'transaction_type': 'buy',
            'status': 'executed',
            'quantity': Decimal('10.0'),
            'price': Decimal('145.00'),
            'total_amount': Decimal('1450.00'),
            'fees': Decimal('1.00'),
            'transaction_date': timezone.now()
        }
    
    def test_create_buy_transaction(self):
        """Test creating a buy transaction"""
        transaction = Transaction.objects.create(**self.transaction_data)
        
        self.assertEqual(transaction.portfolio, self.portfolio)
        self.assertEqual(transaction.stock, self.stock)
        self.assertEqual(transaction.transaction_type, 'buy')
        self.assertEqual(transaction.quantity, Decimal('10.0'))
        self.assertEqual(transaction.price, Decimal('145.00'))
    
    def test_create_deposit_transaction(self):
        """Test creating a deposit transaction (no stock)"""
        deposit_data = {
            'portfolio': self.portfolio,
            'transaction_type': 'deposit',
            'status': 'executed',
            'total_amount': Decimal('5000.00'),
            'fees': Decimal('0.00'),
            'transaction_date': timezone.now()
        }
        transaction = Transaction.objects.create(**deposit_data)
        
        self.assertEqual(transaction.transaction_type, 'deposit')
        self.assertIsNone(transaction.stock)
        self.assertEqual(transaction.total_amount, Decimal('5000.00'))
    
    def test_transaction_str_representation(self):
        """Test transaction string representation"""
        transaction = Transaction.objects.create(**self.transaction_data)
        expected_str = f"Buy: {transaction.quantity} {self.stock.symbol} @ ${transaction.price}"
        self.assertEqual(str(transaction), expected_str)
        
        # Test transaction without stock
        deposit_data = self.transaction_data.copy()
        deposit_data['transaction_type'] = 'deposit'
        deposit_data['stock'] = None
        deposit_transaction = Transaction.objects.create(**deposit_data)
        expected_str = f"Deposit: ${deposit_transaction.total_amount}"
        self.assertEqual(str(deposit_transaction), expected_str)