from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Stock, Portfolio, Holding, Transaction

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
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
    """Serializer for user profile (without sensitive data)"""
    
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
    """Serializer for Stock model"""
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
    """Basic stock serializer for nested relationships"""
    
    class Meta:
        model = Stock
        fields = ['id', 'symbol', 'name', 'current_price', 'day_change_percent']


class HoldingSerializer(serializers.ModelSerializer):
    """Serializer for Holding model"""
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
    """Serializer for Portfolio model"""
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
    """Basic portfolio serializer for nested relationships"""
    
    class Meta:
        model = Portfolio
        fields = ['id', 'name', 'total_value', 'is_default']


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
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
        # Validate that stock is provided for buy/sell transactions
        if data.get('transaction_type') in ['buy', 'sell'] and not data.get('stock_id'):
            raise serializers.ValidationError(
                "Stock is required for buy/sell transactions"
            )
        
        # Validate quantity for stock transactions
        if data.get('transaction_type') in ['buy', 'sell'] and data.get('quantity', 0) <= 0:
            raise serializers.ValidationError(
                "Quantity must be greater than 0 for stock transactions"
            )
        
        # Validate price for stock transactions
        if data.get('transaction_type') in ['buy', 'sell'] and data.get('price', 0) <= 0:
            raise serializers.ValidationError(
                "Price must be greater than 0 for stock transactions"
            )
        
        return data


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transactions"""
    
    class Meta:
        model = Transaction
        fields = [
            'portfolio_id', 'stock_id', 'transaction_type', 'quantity',
            'price', 'total_amount', 'fees', 'transaction_date', 'notes'
        ]
    
    def validate(self, data):
        # Same validation as TransactionSerializer
        if data.get('transaction_type') in ['buy', 'sell'] and not data.get('stock_id'):
            raise serializers.ValidationError(
                "Stock is required for buy/sell transactions"
            )
        
        if data.get('transaction_type') in ['buy', 'sell'] and data.get('quantity', 0) <= 0:
            raise serializers.ValidationError(
                "Quantity must be greater than 0 for stock transactions"
            )
        
        if data.get('transaction_type') in ['buy', 'sell'] and data.get('price', 0) <= 0:
            raise serializers.ValidationError(
                "Price must be greater than 0 for stock transactions"
            )
        
        return data


class PortfolioDetailSerializer(serializers.ModelSerializer):
    """Detailed portfolio serializer with transactions"""
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
    """Serializer for user registration"""
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