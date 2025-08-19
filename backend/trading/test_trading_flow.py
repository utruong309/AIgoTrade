from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status

from .models import Portfolio, Stock, Holding, Transaction
from .services import TradingService

User = get_user_model()


class TradingServiceTests(TestCase):
    """Unit tests for trading order flow"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name='Test Portfolio',
            cash_balance=Decimal('10000.00'),
            is_default=True
        )
        
        self.stock = Stock.objects.create(
            symbol='AAPL',
            name='Apple Inc.',
            exchange='NASDAQ',
            current_price=Decimal('150.00'),
            is_active=True
        )
    
    def test_buy_order_success(self):
        """Test successful buy order execution"""
        result = TradingService.execute_buy_order(
            user=self.user,
            portfolio_id=str(self.portfolio.id),
            stock_id=str(self.stock.id),
            quantity=Decimal('10'),
            price=Decimal('150.00'),
            fees=Decimal('0.99')
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['new_quantity'], 10.0)
        self.assertEqual(result['new_average_cost'], 150.0)
        
        # Check portfolio cash balance
        self.portfolio.refresh_from_db()
        expected_balance = Decimal('10000.00') - (Decimal('10') * Decimal('150.00') + Decimal('0.99'))
        self.assertEqual(self.portfolio.cash_balance, expected_balance)
        
        # Check holding created
        holding = Holding.objects.get(portfolio=self.portfolio, stock=self.stock)
        self.assertEqual(holding.quantity, Decimal('10'))
        self.assertEqual(holding.average_cost, Decimal('150.0000'))
    
    def test_buy_order_insufficient_funds(self):
        """Test buy order with insufficient funds"""
        result = TradingService.execute_buy_order(
            user=self.user,
            portfolio_id=str(self.portfolio.id),
            stock_id=str(self.stock.id),
            quantity=Decimal('100'),  # $15,000 + fees > $10,000 balance
            price=Decimal('150.00'),
            fees=Decimal('0.99')
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Insufficient funds')
        
        # Portfolio should be unchanged
        self.portfolio.refresh_from_db()
        self.assertEqual(self.portfolio.cash_balance, Decimal('10000.00'))
    
    def test_average_cost_calculation(self):
        """Test average cost recalculation on multiple buys"""
        # First buy: 10 shares at $150
        TradingService.execute_buy_order(
            user=self.user,
            portfolio_id=str(self.portfolio.id),
            stock_id=str(self.stock.id),
            quantity=Decimal('10'),
            price=Decimal('150.00')
        )
        
        # Second buy: 5 shares at $160
        result = TradingService.execute_buy_order(
            user=self.user,
            portfolio_id=str(self.portfolio.id),
            stock_id=str(self.stock.id),
            quantity=Decimal('5'),
            price=Decimal('160.00')
        )
        
        # Average cost should be (10*150 + 5*160) / 15 = 153.33
        expected_avg_cost = (Decimal('1500') + Decimal('800')) / Decimal('15')
        self.assertEqual(result['new_quantity'], 15.0)
        self.assertAlmostEqual(float(result['new_average_cost']), float(expected_avg_cost), places=2)
    
    def test_sell_order_success(self):
        """Test successful sell order execution"""
        # First buy some shares
        TradingService.execute_buy_order(
            user=self.user,
            portfolio_id=str(self.portfolio.id),
            stock_id=str(self.stock.id),
            quantity=Decimal('10'),
            price=Decimal('150.00')
        )
        
        initial_balance = self.portfolio.cash_balance
        
        # Now sell some shares
        result = TradingService.execute_sell_order(
            user=self.user,
            portfolio_id=str(self.portfolio.id),
            stock_id=str(self.stock.id),
            quantity=Decimal('5'),
            price=Decimal('160.00'),
            fees=Decimal('0.99')
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['remaining_quantity'], 5.0)
        
        # Check realized gain/loss: (160 - 150) * 5 = $50 gain
        expected_gain = (Decimal('160.00') - Decimal('150.00')) * Decimal('5')
        self.assertEqual(result['realized_gain_loss'], float(expected_gain))
        
        # Check cash balance increased
        self.portfolio.refresh_from_db()
        expected_proceeds = Decimal('5') * Decimal('160.00') - Decimal('0.99')
        self.assertEqual(self.portfolio.cash_balance, initial_balance + expected_proceeds)
    
    def test_sell_order_insufficient_shares(self):
        """Test sell order with insufficient shares"""
        result = TradingService.execute_sell_order(
            user=self.user,
            portfolio_id=str(self.portfolio.id),
            stock_id=str(self.stock.id),
            quantity=Decimal('10'),
            price=Decimal('160.00')
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'No holding found for this stock')
    
    def test_complete_position_sale(self):
        """Test selling entire position removes holding"""
        # Buy shares
        TradingService.execute_buy_order(
            user=self.user,
            portfolio_id=str(self.portfolio.id),
            stock_id=str(self.stock.id),
            quantity=Decimal('10'),
            price=Decimal('150.00')
        )
        
        # Sell all shares
        result = TradingService.execute_sell_order(
            user=self.user,
            portfolio_id=str(self.portfolio.id),
            stock_id=str(self.stock.id),
            quantity=Decimal('10'),
            price=Decimal('160.00')
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['remaining_quantity'], 0.0)
        
        # Holding should be deleted
        with self.assertRaises(Holding.DoesNotExist):
            Holding.objects.get(portfolio=self.portfolio, stock=self.stock)
    
    def test_transaction_records_created(self):
        """Test that transaction records are properly created"""
        initial_count = Transaction.objects.count()
        
        # Execute buy order
        TradingService.execute_buy_order(
            user=self.user,
            portfolio_id=str(self.portfolio.id),
            stock_id=str(self.stock.id),
            quantity=Decimal('10'),
            price=Decimal('150.00')
        )
        
        # Should have one new transaction
        self.assertEqual(Transaction.objects.count(), initial_count + 1)
        
        transaction = Transaction.objects.latest('created_at')
        self.assertEqual(transaction.transaction_type, 'buy')
        self.assertEqual(transaction.status, 'executed')
        self.assertEqual(transaction.quantity, Decimal('10'))
        self.assertEqual(transaction.price, Decimal('150.00'))
    
    def test_portfolio_metrics_update(self):
        """Test that portfolio metrics are updated after trades"""
        # Buy shares
        TradingService.execute_buy_order(
            user=self.user,
            portfolio_id=str(self.portfolio.id),
            stock_id=str(self.stock.id),
            quantity=Decimal('10'),
            price=Decimal('150.00')
        )
        
        self.portfolio.refresh_from_db()
        
        # Check invested amount
        self.assertEqual(self.portfolio.invested_amount, Decimal('1500.00'))
        
        # Check total value (cash + holdings)
        expected_total = self.portfolio.cash_balance + (Decimal('10') * self.stock.current_price)
        self.assertEqual(self.portfolio.total_value, expected_total)


class PortfolioAPITests(APITestCase):
    """Unit tests for Portfolio API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name='Test Portfolio',
            cash_balance=Decimal('10000.00'),
            is_default=True
        )
        
        self.stock = Stock.objects.create(
            symbol='AAPL',
            name='Apple Inc.',
            exchange='NASDAQ',
            current_price=Decimal('150.00'),
            is_active=True
        )
    
    def test_get_portfolio_endpoint(self):
        """Test GET /api/portfolios/portfolio/ endpoint"""
        response = self.client.get('/api/portfolios/portfolio/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['name'], 'Test Portfolio')
        self.assertEqual(data['cash_balance'], 10000.0)
        self.assertEqual(data['holdings_count'], 0)
        self.assertIsInstance(data['holdings'], list)
    
    def test_get_orders_endpoint(self):
        """Test GET /api/portfolios/orders/ endpoint"""
        # Create a transaction first
        Transaction.objects.create(
            portfolio=self.portfolio,
            stock=self.stock,
            transaction_type='buy',
            status='executed',
            quantity=Decimal('10'),
            price=Decimal('150.00'),
            total_amount=Decimal('1500.00'),
            transaction_date='2024-01-01T12:00:00Z'
        )
        
        response = self.client.get('/api/portfolios/orders/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertGreater(len(data['results']), 0)
        transaction = data['results'][0]
        self.assertEqual(transaction['transaction_type'], 'buy')
        self.assertEqual(transaction['status'], 'executed')
    
    def test_buy_order_endpoint(self):
        """Test POST /api/portfolios/{id}/buy/ endpoint"""
        url = f'/api/portfolios/{self.portfolio.id}/buy/'
        data = {
            'stock_id': str(self.stock.id),
            'quantity': '10',
            'price': '150.00',
            'fees': '0.99'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = response.json()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['new_quantity'], 10.0)
    
    def test_sell_order_endpoint(self):
        """Test POST /api/portfolios/{id}/sell/ endpoint"""
        # First buy some shares
        TradingService.execute_buy_order(
            user=self.user,
            portfolio_id=str(self.portfolio.id),
            stock_id=str(self.stock.id),
            quantity=Decimal('10'),
            price=Decimal('150.00')
        )
        
        url = f'/api/portfolios/{self.portfolio.id}/sell/'
        data = {
            'stock_id': str(self.stock.id),
            'quantity': '5',
            'price': '160.00',
            'fees': '0.99'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['remaining_quantity'], 5.0)
    
    def test_unauthorized_access(self):
        """Test that endpoints require authentication"""
        self.client.credentials()  # Remove authentication
        
        response = self.client.get('/api/portfolios/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        response = self.client.get('/api/portfolios/orders/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)