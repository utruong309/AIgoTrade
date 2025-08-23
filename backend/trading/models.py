from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=10, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    exchange = models.CharField(max_length=20)
    sector = models.CharField(max_length=50, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    market_cap = models.BigIntegerField(blank=True, null=True)
    
    current_price = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    previous_close = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    day_change = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    day_change_percent = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    
    volume = models.BigIntegerField(default=0)
    avg_volume = models.BigIntegerField(default=0)
    
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dividend_yield = models.DecimalField(max_digits=8, decimal_places=4, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_price_update = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'trading_stocks'
        ordering = ['symbol']
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"


class MarketData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='market_data')
    
    open_price = models.DecimalField(max_digits=15, decimal_places=4)
    high_price = models.DecimalField(max_digits=15, decimal_places=4)
    low_price = models.DecimalField(max_digits=15, decimal_places=4)
    close_price = models.DecimalField(max_digits=15, decimal_places=4)
    
    volume = models.BigIntegerField()
    adjusted_close = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True)
    
    date = models.DateField()
    time_period = models.CharField(
        max_length=10,
        choices=[
            ('1min', '1 Minute'),
            ('5min', '5 Minutes'),
            ('15min', '15 Minutes'),
            ('30min', '30 Minutes'),
            ('1hour', '1 Hour'),
            ('1day', '1 Day'),
            ('1week', '1 Week'),
            ('1month', '1 Month'),
        ],
        default='1day'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trading_market_data'
        ordering = ['-date', '-time_period']
        unique_together = [['stock', 'date', 'time_period']]
        indexes = [
            models.Index(fields=['stock', 'date']),
            models.Index(fields=['stock', 'time_period']),
        ]
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.date} ({self.time_period})"


class Portfolio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolios')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cash_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    invested_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_return = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_return_percent = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trading_portfolios'
        ordering = ['-is_default', '-created_at']
        unique_together = [['user', 'name']]
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"


class Holding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='holdings')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='holdings')
    
    quantity = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    average_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    unrealized_gain_loss = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    unrealized_gain_loss_percent = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    
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
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    quantity = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    price = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    transaction_date = models.DateTimeField()
    
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

class NewsArticle(models.Model):
    symbol = models.CharField(max_length=10, db_index=True)
    title = models.TextField()
    description = models.TextField(blank=True, null=True)
    url = models.URLField()
    source = models.CharField(max_length=100)
    published_at = models.DateTimeField()
    cached_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['symbol', 'cached_at']),
            models.Index(fields=['published_at']),
        ]
        
        unique_together = ['symbol', 'url']  
        ordering = ['-published_at']
    
    def __str__(self):
        return f"{self.symbol}: {self.title[:50]}..."
    
    @classmethod
    def is_cache_valid(cls, symbol, hours=24):
        cutoff_time = timezone.now() - timedelta(hours=hours)
        return cls.objects.filter(
            symbol=symbol,
            cached_at__gte=cutoff_time
        ).exists()