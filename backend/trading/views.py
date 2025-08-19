from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db.models import F

from .models import Stock, Portfolio, Holding, Transaction
from .serializers import (
    UserSerializer, UserProfileSerializer, UserRegistrationSerializer,
    StockSerializer, PortfolioSerializer, PortfolioDetailSerializer,
    HoldingSerializer, TransactionSerializer, TransactionCreateSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user management"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'username']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action in ['update', 'partial_update']:
            return UserProfileSerializer
        return UserSerializer
    
    def get_queryset(self):
        # Users can only see their own profile
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class StockViewSet(viewsets.ModelViewSet):
    """ViewSet for stock management"""
    queryset = Stock.objects.filter(is_active=True)
    serializer_class = StockSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['exchange', 'sector', 'industry']
    search_fields = ['symbol', 'name', 'sector', 'industry']
    ordering_fields = ['symbol', 'current_price', 'day_change_percent', 'volume']
    ordering = ['symbol']
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending stocks based on volume and price change"""
        trending_stocks = self.queryset.filter(
            volume__gt=F('avg_volume'),
            day_change_percent__gt=5
        ).order_by('-day_change_percent')[:20]
        
        serializer = self.get_serializer(trending_stocks, many=True)
        return Response(serializer.data)


class PortfolioViewSet(viewsets.ModelViewSet):
    """ViewSet for portfolio management"""
    serializer_class = PortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'total_value', 'total_return_percent']
    ordering = ['-is_default', '-created_at']
    
    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user, is_active=True)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PortfolioDetailSerializer
        return PortfolioSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HoldingViewSet(viewsets.ModelViewSet):
    """ViewSet for holding management"""
    serializer_class = HoldingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['portfolio', 'stock']
    ordering_fields = ['current_value', 'unrealized_gain_loss_percent', 'quantity']
    ordering = ['-current_value']
    
    def get_queryset(self):
        return Holding.objects.filter(
            portfolio__user=self.request.user,
            quantity__gt=0
        ).select_related('stock', 'portfolio')


class TransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for transaction management"""
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['portfolio', 'stock', 'transaction_type', 'status']
    search_fields = ['notes']
    ordering_fields = ['transaction_date', 'total_amount']
    ordering = ['-transaction_date']
    
    def get_queryset(self):
        return Transaction.objects.filter(
            portfolio__user=self.request.user
        ).select_related('stock', 'portfolio')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TransactionCreateSerializer
        return TransactionSerializer