from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone

from .models import Stock, Portfolio, Holding, Transaction

User = get_user_model()


class UserAPITest(APITestCase):
    """Test cases for User API endpoints"""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'risk_tolerance': 'moderate',
            'investment_experience': 'beginner'
        }
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='existingpass123'
        )
    
    def test_user_registration(self):
        """Test user registration"""
        url = reverse('user-list')
        response = self.client.post(url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)  # existing + new user
        
        # Check that default portfolio was created
        new_user = User.objects.get(email=self.user_data['email'])
        self.assertTrue(new_user.portfolios.filter(is_default=True).exists())
    
    def test_user_registration_password_mismatch(self):
        """Test user registration with password mismatch"""
        data = self.user_data.copy()
        data['password_confirm'] = 'differentpass'
        
        url = reverse('user-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', str(response.data).lower())
    
    def test_get_user_profile_authenticated(self):
        """Test getting user profile when authenticated"""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-me')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
    
    def test_get_user_profile_unauthenticated(self):
        """Test getting user profile when not authenticated"""
        url = reverse('user-me')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class StockAPITest(APITestCase):
    """Test cases for Stock API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.stock = Stock.objects.create(
            symbol='AAPL',
            name='Apple Inc.',
            exchange='NASDAQ',
            sector='Technology',
            current_price=Decimal('150.00'),
            day_change_percent=Decimal('2.5'),
            volume=50000000,
            avg_volume=45000000
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_stocks(self):
        """Test listing stocks"""
        url = reverse('stock-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['symbol'], 'AAPL')
    
    def test_get_stock_detail(self):
        """Test getting stock detail"""
        url = reverse('stock-detail', kwargs={'pk': self.stock.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['symbol'], 'AAPL')
        self.assertEqual(response.data['name'], 'Apple Inc.')
    
    def test_search_stocks(self):
        """Test searching stocks"""
        url = reverse('stock-list')
        response = self.client.get(url, {'search': 'Apple'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_trending_stocks(self):
        """Test getting trending stocks"""
        url = reverse('stock-trending')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_stocks_unauthenticated(self):
        """Test accessing stocks without authentication"""
        self.client.force_authenticate(user=None)
        url = reverse('stock-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PortfolioAPITest(APITestCase):
    """Test cases for Portfolio API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name='Test Portfolio',
            description='A test portfolio',
            cash_balance=Decimal('10000.00'),
            is_default=True
        )
        self.other_portfolio = Portfolio.objects.create(
            user=self.other_user,
            name='Other Portfolio',
            cash_balance=Decimal('5000.00')
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_user_portfolios(self):
        """Test listing user's portfolios"""
        url = reverse('portfolio-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Portfolio')
    
    def test_create_portfolio(self):
        """Test creating a new portfolio"""
        data = {
            'name': 'New Portfolio',
            'description': 'A new test portfolio',
            'cash_balance': '5000.00'
        }
        url = reverse('portfolio-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Portfolio.objects.filter(user=self.user).count(), 2)
    
    def test_get_portfolio_detail(self):
        """Test getting portfolio detail"""
        url = reverse('portfolio-detail', kwargs={'pk': self.portfolio.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Portfolio')
        self.assertIn('holdings', response.data)
    
    def test_cannot_access_other_user_portfolio(self):
        """Test that users cannot access other users' portfolios"""
        url = reverse('portfolio-detail', kwargs={'pk': self.other_portfolio.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_portfolio(self):
        """Test updating a portfolio"""
        data = {'name': 'Updated Portfolio'}
        url = reverse('portfolio-detail', kwargs={'pk': self.portfolio.pk})
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.portfolio.refresh_from_db()
        self.assertEqual(self.portfolio.name, 'Updated Portfolio')


class TransactionAPITest(APITestCase):
    """Test cases for Transaction API endpoints"""
    
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
        self.transaction = Transaction.objects.create(
            portfolio=self.portfolio,
            stock=self.stock,
            transaction_type='buy',
            status='executed',
            quantity=Decimal('10.0'),
            price=Decimal('145.00'),
            total_amount=Decimal('1450.00'),
            fees=Decimal('1.00'),
            transaction_date=timezone.now()
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_transactions(self):
        """Test listing transactions"""
        url = reverse('transaction-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_buy_transaction(self):
        """Test creating a buy transaction"""
        data = {
            'portfolio_id': str(self.portfolio.pk),
            'stock_id': str(self.stock.pk),
            'transaction_type': 'buy',
            'quantity': '5.0',
            'price': '150.00',
            'total_amount': '750.00',
            'fees': '1.00',
            'transaction_date': timezone.now().isoformat()
        }
        url = reverse('transaction-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 2)
    
    def test_create_deposit_transaction(self):
        """Test creating a deposit transaction (no stock)"""
        data = {
            'portfolio_id': str(self.portfolio.pk),
            'transaction_type': 'deposit',
            'total_amount': '1000.00',
            'fees': '0.00',
            'transaction_date': timezone.now().isoformat()
        }
        url = reverse('transaction-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_transaction_validation(self):
        """Test transaction validation"""
        # Test buy transaction without stock
        data = {
            'portfolio_id': str(self.portfolio.pk),
            'transaction_type': 'buy',
            'quantity': '5.0',
            'price': '150.00',
            'total_amount': '750.00',
            'transaction_date': timezone.now().isoformat()
        }
        url = reverse('transaction-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_filter_transactions_by_portfolio(self):
        """Test filtering transactions by portfolio"""
        url = reverse('transaction-list')
        response = self.client.get(url, {'portfolio': self.portfolio.pk})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class HoldingAPITest(APITestCase):
    """Test cases for Holding API endpoints"""
    
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
        self.holding = Holding.objects.create(
            portfolio=self.portfolio,
            stock=self.stock,
            quantity=Decimal('10.0'),
            average_cost=Decimal('145.00'),
            total_cost=Decimal('1450.00'),
            first_purchase_date=timezone.now(),
            last_transaction_date=timezone.now()
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_holdings(self):
        """Test listing holdings"""
        url = reverse('holding-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['stock']['symbol'], 'AAPL')
    
    def test_get_holding_detail(self):
        """Test getting holding detail"""
        url = reverse('holding-detail', kwargs={'pk': self.holding.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], '10.000000')
    
    def test_filter_holdings_by_portfolio(self):
        """Test filtering holdings by portfolio"""
        url = reverse('holding-list')
        response = self.client.get(url, {'portfolio': self.portfolio.pk})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)