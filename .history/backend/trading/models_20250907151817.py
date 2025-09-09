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


class PredictionModel(models.Model):
    """Model to store trained ML models metadata"""
    
    MODEL_TYPES = [
        ('lstm', 'LSTM Neural Network'),
        ('linear', 'Linear Regression'),
        ('random_forest', 'Random Forest'),
    ]
    
    STATUS_CHOICES = [
        ('training', 'Training'),
        ('trained', 'Trained'),
        ('failed', 'Failed'),
        ('outdated', 'Outdated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='prediction_models')
    
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES, default='lstm')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='training')
    
    # Model metadata
    sequence_length = models.IntegerField(default=60)
    training_data_points = models.IntegerField()
    training_start_date = models.DateField()
    training_end_date = models.DateField()
    
    # Training metrics
    train_rmse = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    val_rmse = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    train_mae = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    val_mae = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    
    # Model file paths
    model_file_path = models.CharField(max_length=500)
    scaler_file_path = models.CharField(max_length=500)
    metadata_file_path = models.CharField(max_length=500)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_prediction_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'trading_prediction_models'
        ordering = ['-created_at']
        unique_together = [['stock', 'model_type']]
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.get_model_type_display()} ({self.status})"
    
    @property
    def is_active(self):
        """Check if model is active and ready for predictions"""
        return self.status == 'trained' and self.model_file_path
    
    @property
    def training_duration_days(self):
        """Calculate training data duration in days"""
        return (self.training_end_date - self.training_start_date).days


class PricePrediction(models.Model):
    """Model to store price predictions"""
    
    PREDICTION_TYPES = [
        ('next_day', 'Next Day'),
        ('next_week', 'Next Week'),
        ('next_month', 'Next Month'),
    ]
    
    CONFIDENCE_LEVELS = [
        ('low', 'Low (< 0.3)'),
        ('medium', 'Medium (0.3 - 0.7)'),
        ('high', 'High (> 0.7)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='predictions')
    prediction_model = models.ForeignKey(PredictionModel, on_delete=models.CASCADE, related_name='predictions')
    
    prediction_type = models.CharField(max_length=20, choices=PREDICTION_TYPES, default='next_day')
    
    # Prediction data
    predicted_price = models.DecimalField(max_digits=15, decimal_places=4)
    current_price = models.DecimalField(max_digits=15, decimal_places=4)
    price_change = models.DecimalField(max_digits=15, decimal_places=4)
    price_change_percent = models.DecimalField(max_digits=8, decimal_places=4)
    
    # Confidence and accuracy
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4)  # 0-1 scale
    confidence_level = models.CharField(max_length=10, choices=CONFIDENCE_LEVELS)
    
    # Prediction target date
    prediction_date = models.DateField()
    prediction_timestamp = models.DateTimeField(auto_now_add=True)
    
    # Actual results (filled when prediction date passes)
    actual_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    actual_price_change = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    actual_price_change_percent = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    prediction_accuracy = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    
    # Metadata
    input_features = models.JSONField(default=dict, blank=True)  # Store input OHLCV data
    model_metadata = models.JSONField(default=dict, blank=True)  # Store model-specific metadata
    
    class Meta:
        db_table = 'trading_price_predictions'
        ordering = ['-prediction_timestamp']
        indexes = [
            models.Index(fields=['stock', 'prediction_date']),
            models.Index(fields=['prediction_timestamp']),
            models.Index(fields=['confidence_level']),
        ]
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.predicted_price} ({self.prediction_date})"
    
    @property
    def is_future_prediction(self):
        """Check if this is a future prediction (not yet occurred)"""
        return self.prediction_date > timezone.now().date()
    
    @property
    def can_be_evaluated(self):
        """Check if prediction can be evaluated (date has passed and actual price available)"""
        return (not self.is_future_prediction and 
                self.actual_price is not None and 
                self.prediction_accuracy is None)
    
    def calculate_accuracy(self):
        """Calculate prediction accuracy if actual price is available"""
        if not self.can_be_evaluated:
            return None
        
        # Calculate accuracy as percentage error
        error = abs(float(self.predicted_price - self.actual_price))
        accuracy = max(0, 100 - (error / float(self.actual_price) * 100))
        
        self.prediction_accuracy = accuracy
        self.save()
        
        return accuracy
    
    def update_with_actual_price(self, actual_price):
        """Update prediction with actual price and calculate accuracy"""
        self.actual_price = actual_price
        self.actual_price_change = actual_price - self.current_price
        self.actual_price_change_percent = (self.actual_price_change / self.current_price) * 100
        
        self.calculate_accuracy()
        self.save()


class PredictionCache(models.Model):
    """Redis-like cache for frequently accessed predictions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_symbol = models.CharField(max_length=10, db_index=True)
    
    # Cached prediction data
    prediction_data = models.JSONField()
    
    # Cache metadata
    cache_key = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'trading_prediction_cache'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stock_symbol', 'expires_at']),
            models.Index(fields=['cache_key']),
        ]
    
    def __str__(self):
        return f"Cache for {self.stock_symbol} - {self.cache_key}"
    
    @classmethod
    def is_valid(cls, cache_key):
        """Check if cache entry is still valid"""
        try:
            cache_entry = cls.objects.get(cache_key=cache_key)
            return cache_entry.expires_at > timezone.now()
        except cls.DoesNotExist:
            return False
    
    @classmethod
    def get_cached_prediction(cls, stock_symbol):
        """Get cached prediction for a stock"""
        cache_key = f"prediction_{stock_symbol.lower()}"
        
        if cls.is_valid(cache_key):
            try:
                cache_entry = cls.objects.get(cache_key=cache_key)
                return cache_entry.prediction_data
            except cls.DoesNotExist:
                return None
        
        return None
    
    @classmethod
    def set_cached_prediction(cls, stock_symbol, prediction_data, expires_in_minutes=15):
        """Cache prediction data"""
        cache_key = f"prediction_{stock_symbol.lower()}"
        expires_at = timezone.now() + timedelta(minutes=expires_in_minutes)
        
        # Delete existing cache entry
        cls.objects.filter(cache_key=cache_key).delete()
        
        # Create new cache entry
        cls.objects.create(
            stock_symbol=stock_symbol.upper(),
            prediction_data=prediction_data,
            cache_key=cache_key,
            expires_at=expires_at
        )
    
    @classmethod
    def cleanup_expired(cls):
        """Clean up expired cache entries"""
        expired_count = cls.objects.filter(expires_at__lt=timezone.now()).delete()[0]
        return expired_count