from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Stock, Portfolio, Holding, Transaction, PredictionModel, PricePrediction, PredictionCache

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'is_verified',
            'risk_tolerance', 'investment_experience', 
            'created_at', 'updated_at', 'password'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_verified']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'is_verified',
            'risk_tolerance', 'investment_experience', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_verified', 'email']


class StockSerializer(serializers.ModelSerializer):
    market_cap_display = serializers.ReadOnlyField()
    
    class Meta:
        model = Stock
        fields = [
            'id', 'symbol', 'name', 'exchange', 'sector', 'industry',
            'market_cap', 'market_cap_display', 'current_price', 
            'previous_close', 'day_change', 'day_change_percent',
            'volume', 'avg_volume', 'pe_ratio', 'dividend_yield',
            'is_active', 'created_at', 'updated_at', 'last_price_update'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'last_price_update',
            'market_cap_display'
        ]


class StockBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['id', 'symbol', 'name', 'current_price', 'day_change_percent']


class HoldingSerializer(serializers.ModelSerializer):
    stock = StockBasicSerializer(read_only=True)
    stock_id = serializers.UUIDField(write_only=True)
    current_price = serializers.ReadOnlyField()
    
    class Meta:
        model = Holding
        fields = [
            'id', 'stock', 'stock_id', 'quantity', 'average_cost',
            'total_cost', 'current_value', 'current_price',
            'unrealized_gain_loss', 'unrealized_gain_loss_percent',
            'first_purchase_date', 'last_transaction_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'current_value', 'unrealized_gain_loss',
            'unrealized_gain_loss_percent', 'created_at', 'updated_at'
        ]


class PortfolioSerializer(serializers.ModelSerializer):
    holdings = HoldingSerializer(many=True, read_only=True)
    holdings_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Portfolio
        fields = [
            'id', 'name', 'description', 'total_value', 'cash_balance',
            'invested_amount', 'total_return', 'total_return_percent',
            'is_default', 'is_active', 'holdings', 'holdings_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_value', 'invested_amount', 'total_return',
            'total_return_percent', 'created_at', 'updated_at'
        ]
    
    def get_holdings_count(self, obj):
        return obj.holdings.count()


class PortfolioBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ['id', 'name', 'total_value', 'is_default']


class TransactionSerializer(serializers.ModelSerializer):
    stock = StockBasicSerializer(read_only=True)
    stock_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    portfolio = PortfolioBasicSerializer(read_only=True)
    portfolio_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'portfolio', 'portfolio_id', 'stock', 'stock_id',
            'transaction_type', 'status', 'quantity', 'price',
            'total_amount', 'fees', 'transaction_date', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('transaction_type') in ['buy', 'sell'] and not data.get('stock_id'):
            raise serializers.ValidationError("Stock is required for buy/sell transactions")
        if data.get('transaction_type') in ['buy', 'sell'] and data.get('quantity', 0) <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0 for stock transactions")
        if data.get('transaction_type') in ['buy', 'sell'] and data.get('price', 0) <= 0:
            raise serializers.ValidationError("Price must be greater than 0 for stock transactions")
        return data


class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'portfolio_id', 'stock_id', 'transaction_type', 'quantity',
            'price', 'total_amount', 'fees', 'transaction_date', 'notes'
        ]
    
    def validate(self, data):
        if data.get('transaction_type') in ['buy', 'sell'] and not data.get('stock_id'):
            raise serializers.ValidationError("Stock is required for buy/sell transactions")
        if data.get('transaction_type') in ['buy', 'sell'] and data.get('quantity', 0) <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0 for stock transactions")
        if data.get('transaction_type') in ['buy', 'sell'] and data.get('price', 0) <= 0:
            raise serializers.ValidationError("Price must be greater than 0 for stock transactions")
        return data


class PortfolioDetailSerializer(serializers.ModelSerializer):
    holdings = HoldingSerializer(many=True, read_only=True)
    recent_transactions = serializers.SerializerMethodField()
    holdings_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Portfolio
        fields = [
            'id', 'name', 'description', 'total_value', 'cash_balance',
            'invested_amount', 'total_return', 'total_return_percent',
            'is_default', 'is_active', 'holdings', 'recent_transactions',
            'holdings_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_value', 'invested_amount', 'total_return',
            'total_return_percent', 'created_at', 'updated_at'
        ]
    
    def get_holdings_count(self, obj):
        return obj.holdings.count()
    
    def get_recent_transactions(self, obj):
        recent_transactions = obj.transactions.all()[:10]
        return TransactionSerializer(recent_transactions, many=True).data


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'risk_tolerance', 'investment_experience'
        ]
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        Portfolio.objects.create(
            user=user,
            name="My Portfolio",
            description="Default portfolio",
            is_default=True,
            cash_balance=0
        )
        
        return user


class PredictionModelSerializer(serializers.ModelSerializer):
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)
    is_active = serializers.ReadOnlyField()
    training_duration_days = serializers.ReadOnlyField()
    
    class Meta:
        model = PredictionModel
        fields = [
            'id', 'stock', 'stock_symbol', 'stock_name', 'model_type', 'status',
            'sequence_length', 'training_data_points', 'training_start_date',
            'training_end_date', 'train_rmse', 'val_rmse', 'train_mae', 'val_mae',
            'model_file_path', 'scaler_file_path', 'metadata_file_path',
            'is_active', 'training_duration_days', 'created_at', 'updated_at',
            'last_prediction_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'last_prediction_at'
        ]


class PricePredictionSerializer(serializers.ModelSerializer):
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)
    model_type = serializers.CharField(source='prediction_model.model_type', read_only=True)
    is_future_prediction = serializers.ReadOnlyField()
    can_be_evaluated = serializers.ReadOnlyField()
    
    class Meta:
        model = PricePrediction
        fields = [
            'id', 'stock', 'stock_symbol', 'stock_name', 'prediction_model',
            'model_type', 'prediction_type', 'predicted_price', 'current_price',
            'price_change', 'price_change_percent', 'confidence_score',
            'confidence_level', 'prediction_date', 'prediction_timestamp',
            'actual_price', 'actual_price_change', 'actual_price_change_percent',
            'prediction_accuracy', 'input_features', 'model_metadata',
            'is_future_prediction', 'can_be_evaluated'
        ]
        read_only_fields = [
            'id', 'prediction_timestamp', 'actual_price', 'actual_price_change',
            'actual_price_change_percent', 'prediction_accuracy'
        ]


class PredictionCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionCache
        fields = [
            'id', 'stock_symbol', 'prediction_data', 'cache_key',
            'expires_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PredictionSummarySerializer(serializers.Serializer):
    """Serializer for prediction summary data"""
    symbol = serializers.CharField()
    name = serializers.CharField()
    current_price = serializers.DecimalField(max_digits=15, decimal_places=4)
    predicted_price = serializers.DecimalField(max_digits=15, decimal_places=4)
    price_change = serializers.DecimalField(max_digits=15, decimal_places=4)
    price_change_percent = serializers.DecimalField(max_digits=8, decimal_places=4)
    confidence_score = serializers.DecimalField(max_digits=5, decimal_places=4)
    confidence_level = serializers.CharField()
    prediction_date = serializers.DateField()
    prediction_timestamp = serializers.DateTimeField()
    model_type = serializers.CharField()
    is_future_prediction = serializers.BooleanField()


class ModelTrainingStatusSerializer(serializers.Serializer):
    """Serializer for model training status"""
    symbol = serializers.CharField()
    status = serializers.CharField()
    progress_percent = serializers.IntegerField()
    current_epoch = serializers.IntegerField()
    total_epochs = serializers.IntegerField()
    train_loss = serializers.DecimalField(max_digits=10, decimal_places=6)
    val_loss = serializers.DecimalField(max_digits=10, decimal_places=6)
    estimated_completion = serializers.DateTimeField()
    error_message = serializers.CharField(required=False)