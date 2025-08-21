from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db.models import F
from decimal import Decimal
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.db import transaction

from .models import Stock, Portfolio, Holding, Transaction, MarketData
from .serializers import (
    UserSerializer, UserProfileSerializer, UserRegistrationSerializer,
    StockSerializer, PortfolioSerializer, PortfolioDetailSerializer,
    HoldingSerializer, TransactionSerializer, TransactionCreateSerializer
)
from .services import TradingService
from .live_market_service import get_live_market_service

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
        try:
            # Use live market service to get trending stocks
            live_service = get_live_market_service()
            stocks = live_service.get_stock_list()
            
            # Filter for trending stocks (high volume, significant price change)
            trending_stocks = [
                stock for stock in stocks
                if abs(stock['day_change_percent']) > 0.1 and stock['volume'] > 100000
            ]
            
            # Sort by absolute price change percentage
            trending_stocks.sort(key=lambda x: abs(x['day_change_percent']), reverse=True)
            
            return Response({
                'status': 'success',
                'data': trending_stocks[:20],
                'count': len(trending_stocks[:20])
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def top_stocks(self, request):
        """Get top stocks by volume with real-time prices"""
        try:
            live_service = get_live_market_service()
            stocks = live_service.get_stock_list()
            
            # Sort by volume
            top_stocks = sorted(stocks, key=lambda x: x['volume'], reverse=True)[:20]
            
            return Response({
                'status': 'success',
                'data': top_stocks,
                'count': len(top_stocks)
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def market_data(self, request, pk=None):
        """Get market data (OHLC) for a specific stock"""
        try:
            stock = self.get_object()
            symbol = stock.symbol
            
            # Get detailed stock data from live service
            live_service = get_live_market_service()
            stock_detail = live_service.get_stock_detail(symbol)
            
            if stock_detail:
                return Response({
                    'status': 'success',
                    'stock': stock_detail,
                    'market_data': {
                        'data': stock_detail['market_data'],
                        'count': len(stock_detail['market_data'])
                    }
                })
            else:
                return Response({
                    'status': 'error',
                    'message': 'Stock data not available'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search stocks by symbol or name"""
        try:
            query = request.query_params.get('q', '')
            if not query:
                return Response({
                    'status': 'error',
                    'message': 'Search query is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Use live market service to search stocks
            live_service = get_live_market_service()
            results = live_service.search_stocks(query)
            
            return Response({
                'status': 'success',
                'query': query,
                'data': results,
                'count': len(results)
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        """Get detailed stock information by symbol"""
        try:
            stock = self.get_object()
            symbol = stock.symbol
            
            # Get detailed stock data from live service
            live_service = get_live_market_service()
            stock_detail = live_service.get_stock_detail(symbol)
            
            if stock_detail:
                return Response({
                    'status': 'success',
                    'data': stock_detail
                })
            else:
                return Response({
                    'status': 'error',
                    'message': 'Stock data not available'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        # Debug logging
        print(f"Portfolio request - User: {request.user}")
        print(f"Portfolio request - Auth: {request.auth}")
        print(f"Portfolio request - Headers: {request.headers}")
        print(f"Portfolio request - Is authenticated: {request.user.is_authenticated}")
        
        try:
            # Use trading service to get portfolio summary
            trading_service = TradingService(request.user)
            portfolio_summary = trading_service.get_portfolio_summary()
            
            return Response({
                'status': 'success',
                'data': portfolio_summary
            })
            
        except Exception as e:
            print(f"Portfolio error: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def orders(self, request):
        """Get transaction history for portfolio"""
        try:
            trading_service = TradingService(request.user)
            transactions = trading_service.get_transaction_history()
            
            return Response({
                'status': 'success',
                'data': transactions,
                'count': len(transactions)
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def buy(self, request):
        """Execute buy order"""
        try:
            symbol = request.data.get('symbol', '').upper()
            quantity = Decimal(str(request.data.get('quantity', 0)))
            price = request.data.get('price')  # Optional, will use live price if not provided
            
            if not symbol or quantity <= 0:
                return Response({
                    'status': 'error',
                    'message': 'Valid symbol and quantity are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            trading_service = TradingService(request.user)
            result = trading_service.buy_stock(symbol, quantity, price)
            
            return Response({
                'status': 'success',
                'data': result
            })
            
        except ValueError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def sell(self, request):
        """Execute sell order"""
        try:
            symbol = request.data.get('symbol', '').upper()
            quantity = Decimal(str(request.data.get('quantity', 0)))
            price = request.data.get('price')  
            
            if not symbol or quantity <= 0:
                return Response({
                    'status': 'error',
                    'message': 'Valid symbol and quantity are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            trading_service = TradingService(request.user)
            result = trading_service.sell_stock(symbol, quantity, price)
            
            return Response({
                'status': 'success',
                'data': result
            })
            
        except ValueError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def holding(self, request):
        """Get detailed holding information for a specific stock"""
        try:
            symbol = request.query_params.get('symbol', '').upper()
            if not symbol:
                return Response({
                    'status': 'error',
                    'message': 'Stock symbol is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            trading_service = TradingService(request.user)
            holding_detail = trading_service.get_holding_detail(symbol)
            
            if holding_detail:
                return Response({
                    'status': 'success',
                    'data': holding_detail
                })
            else:
                return Response({
                    'status': 'error',
                    'message': f'No holding found for {symbol}'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

class MarketDataViewSet(viewsets.ModelViewSet):
    """ViewSet for market data"""
    queryset = Stock.objects.filter(is_active=True)
    serializer_class = StockSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get all stocks with current market data"""
        try:
            # Use live market service to get current stock data
            live_service = get_live_market_service()
            stocks = live_service.get_stock_list()
            
            return Response({
                'status': 'success',
                'data': stocks,
                'count': len(stocks)
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, pk=None):
        """Get specific stock with detailed market data"""
        try:
            stock = self.get_object()
            symbol = stock.symbol
            
            # Get detailed stock data from live service
            live_service = get_live_market_service()
            stock_detail = live_service.get_stock_detail(symbol)
            
            if stock_detail:
                return Response({
                    'status': 'success',
                    'stock': stock_detail
                })
            else:
                return Response({
                    'status': 'error',
                    'message': 'Stock data not available'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def test_websocket(request):
    return render(request, 'test_websocket.html') 

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated]) # type: ignore
def test_auth(request):
    """Test endpoint to verify authentication is working"""
    return Response({
        'success': True,
        'message': 'Authentication is working!',
        'user': request.user.username,
        'user_id': request.user.id,
        'is_authenticated': request.user.is_authenticated
    })

@api_view(['POST'])
@permission_classes([AllowAny]) # type: ignore
def register(request):
    """
    User registration endpoint
    POST /api/auth/register
    """
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            with transaction.atomic():
                user = serializer.save()
                
                token, created = Token.objects.get_or_create(user=user)
                
                initial_cash = request.data.get('initial_cash', 0)
                if initial_cash and float(initial_cash) > 0:
                    default_portfolio = Portfolio.objects.get(user=user, is_default=True)
                    default_portfolio.cash_balance = Decimal(str(initial_cash))
                    default_portfolio.save()
                
                return Response({
                    'success': True,
                    'message': 'User registered successfully',
                    'user': UserProfileSerializer(user).data,
                    'token': token.key
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST) 