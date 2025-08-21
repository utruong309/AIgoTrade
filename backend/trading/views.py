from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db.models import F
from decimal import Decimal
from django.shortcuts import render

from .models import Stock, Portfolio, Holding, Transaction
from .serializers import (
    UserSerializer, UserProfileSerializer, UserRegistrationSerializer,
    StockSerializer, PortfolioSerializer, PortfolioDetailSerializer,
    HoldingSerializer, TransactionSerializer, TransactionCreateSerializer
)
from .services import TradingService

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
    
    @action(detail=True, methods=['post']) # must have ID, /api/portfolios/<pk>/buy/
    def buy(self, request, pk=None):
        """Execute a buy order"""
        portfolio = self.get_object()
        
        try:
            stock_id = request.data.get('stock_id')
            quantity = Decimal(str(request.data.get('quantity', 0)))
            price = Decimal(str(request.data.get('price', 0)))
            fees = Decimal(str(request.data.get('fees', 0)))
            
            if not stock_id:
                return Response(
                    {'error': 'stock_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = TradingService.execute_buy_order(
                user=request.user,
                portfolio_id=str(portfolio.id),
                stock_id=stock_id,
                quantity=quantity,
                price=price,
                fees=fees
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_201_CREATED)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except (ValueError, TypeError) as e:
            return Response(
                {'error': f'Invalid input: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def sell(self, request, pk=None):
        """Execute a sell order"""
        portfolio = self.get_object()
        
        try:
            stock_id = request.data.get('stock_id')
            quantity = Decimal(str(request.data.get('quantity', 0)))
            price = Decimal(str(request.data.get('price', 0)))
            fees = Decimal(str(request.data.get('fees', 0)))
            
            if not stock_id:
                return Response(
                    {'error': 'stock_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = TradingService.execute_sell_order(
                user=request.user,
                portfolio_id=str(portfolio.id),
                stock_id=stock_id,
                quantity=quantity,
                price=price,
                fees=fees
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except (ValueError, TypeError) as e:
            return Response(
                {'error': f'Invalid input: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def add_cash(self, request, pk=None):
        """Add cash to portfolio"""
        portfolio = self.get_object()
        
        try:
            amount = Decimal(str(request.data.get('amount', 0)))
            
            result = TradingService.add_cash( # core trading logic from services.py
                user=request.user,
                portfolio_id=str(portfolio.id),
                amount=amount
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except (ValueError, TypeError) as e:
            return Response(
                {'error': f'Invalid amount: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # function name = action name in URL 

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get portfolio summary with current P/L"""
        portfolio = self.get_object()
        
        result = TradingService.get_portfolio_summary(
            user=request.user,
            portfolio_id=str(portfolio.id)
        )
        
        if result['success']:
            return Response(result['portfolio'], status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get']) # API endpoint
    def portfolio(self, request):
        """Get current holdings + P/L for default portfolio (API requirement)"""
        try:
            portfolio = Portfolio.objects.filter(
                user=request.user, 
                is_active=True
            ).order_by('-is_default', '-created_at').first()
            
            if not portfolio:
                return Response(
                    {'error': 'No active portfolio found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            result = TradingService.get_portfolio_summary(
                user=request.user,
                portfolio_id=str(portfolio.id)
            )
            
            if result['success']:
                holdings = portfolio.holdings.select_related('stock').all()
                holdings_data = []
                
                for holding in holdings:
                    holdings_data.append({
                        'id': str(holding.id),
                        'stock': {
                            'id': str(holding.stock.id),
                            'symbol': holding.stock.symbol,
                            'name': holding.stock.name,
                            'current_price': float(holding.stock.current_price),
                            'day_change_percent': float(holding.stock.day_change_percent)
                        },
                        'quantity': float(holding.quantity),
                        'average_cost': float(holding.average_cost),
                        'total_cost': float(holding.total_cost),
                        'current_value': float(holding.current_value),
                        'unrealized_gain_loss': float(holding.unrealized_gain_loss),
                        'unrealized_gain_loss_percent': float(holding.unrealized_gain_loss_percent),
                        'first_purchase_date': holding.first_purchase_date,
                        'last_transaction_date': holding.last_transaction_date
                    })
                
                response_data = result['portfolio']
                response_data['holdings'] = holdings_data
                
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def orders(self, request):
        """Get transaction history (API requirement)"""
        try:

            transactions = Transaction.objects.filter(
                portfolio__user=request.user
            ).select_related('stock', 'portfolio').order_by('-transaction_date')
            
            page = self.paginate_queryset(transactions)
            if page is not None:
                serializer = TransactionSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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

def test_websocket(request):
    return render(request, 'test_websocket.html') 