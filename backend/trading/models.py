from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class User(AbstractUser):
    """Extended user model for trading platform"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Trading specific fields
    risk_tolerance = models.CharField(
        max_length=20,
        choices=[
            ('conservative', 'Conservative'),
            ('moderate', 'Moderate'),
            ('aggressive', 'Aggressive'),
        ],
        default='moderate'
    )
    investment_experience = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'trading_users'
    
    def __str__(self):
        return f"{self.username} ({self.email})"


class Stock(models.Model):
    """Stock/Security information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=10, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    exchange = models.CharField(max_length=20)
    sector = models.CharField(max_length=50, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    market_cap = models.BigIntegerField(blank=True, null=True)
    
    # Current market data
    current_price = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    previous_close = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    day_change = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    day_change_percent = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    
    # Trading info
    volume = models.BigIntegerField(default=0)
    avg_volume = models.BigIntegerField(default=0)
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dividend_yield = models.DecimalField(max_digits=8, decimal_places=4, blank=True, null=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_price_update = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'trading_stocks'
        ordering = ['symbol']
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"


class Portfolio(models.Model):
    """User's portfolio"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolios')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Portfolio metrics
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cash_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    invested_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_return = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_return_percent = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    
    # Settings
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trading_portfolios'
        ordering = ['-is_default', '-created_at']
        unique_together = [['user', 'name']]
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"


class Holding(models.Model):
    """Individual stock holdings in a portfolio"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='holdings')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='holdings')
    
    # Position details
    quantity = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    average_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Performance metrics
    unrealized_gain_loss = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    unrealized_gain_loss_percent = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    
    # Metadata
    first_purchase_date = models.DateTimeField()
    last_transaction_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trading_holdings'
        unique_together = [['portfolio', 'stock']]
        ordering = ['-current_value']
    
    def __str__(self):
        return f"{self.portfolio.name} - {self.stock.symbol}: {self.quantity} shares"


class Transaction(models.Model):
    """Transaction records for all trading activities"""
    
    TRANSACTION_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('dividend', 'Dividend'),
        ('deposit', 'Cash Deposit'),
        ('withdrawal', 'Cash Withdrawal'),
        ('fee', 'Fee'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('executed', 'Executed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='transactions')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='transactions', blank=True, null=True)
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Financial details
    quantity = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    price = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timing
    transaction_date = models.DateTimeField()
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trading_transactions'
        ordering = ['-transaction_date']
    
    def __str__(self):
        if self.stock:
            return f"{self.get_transaction_type_display()}: {self.quantity} {self.stock.symbol} @ ${self.price}"
        else:
            return f"{self.get_transaction_type_display()}: ${self.total_amount}"