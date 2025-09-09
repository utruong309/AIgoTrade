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
from .models import Stock, Portfolio, Holding, Transaction, MarketData, PredictionModel, PricePrediction
from .serializers import (
    UserSerializer, UserProfileSerializer, UserRegistrationSerializer,
    StockSerializer, PortfolioSerializer, PortfolioDetailSerializer,
    HoldingSerializer, TransactionSerializer, TransactionCreateSerializer,
    PredictionModelSerializer, PricePredictionSerializer, PredictionSummarySerializer
)
from .services import TradingService
from .live_market_service import get_live_market_service
from .prediction_service import PredictionService
from .data_preprocessing import DataPreprocessingService
from .ml_tasks import (
    train_lstm_model, make_prediction_task, update_predictions_batch,
    train_models_batch, cleanup_expired_caches, update_prediction_accuracy
)
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.views import ObtainAuthToken

User = get_user_model()

class CustomObtainAuthToken(ObtainAuthToken):
    permission_classes = [AllowAny]

class UserViewSet(viewsets.ModelViewSet):
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
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class StockViewSet(viewsets.ModelViewSet):
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
        try:
            live_service = get_live_market_service()
            stocks = live_service.get_stock_list()

            trending_stocks = [
                stock for stock in stocks
                if abs(stock['day_change_percent']) > 0.1 and stock['volume'] > 100000
            ]

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
        try:
            live_service = get_live_market_service()
            stocks = live_service.get_stock_list()
            
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

    @action(detail=False, methods=['get'])
    def by_symbol(self, request):
        try:
            symbol = request.query_params.get('symbol', '').upper()
            if not symbol:
                return Response({
                    'status': 'error',
                    'message': 'Symbol parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)

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
    
    @action(detail=False, methods=['get'])
    def market_data(self, request, pk=None):
        try:
            stock = self.get_object()
            symbol = stock.symbol

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
        try:
            query = request.query_params.get('q', '')
            if not query:
                return Response({
                    'status': 'error',
                    'message': 'Search query is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
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
        try:
            stock = self.get_object()
            symbol = stock.symbol

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
        portfolio = self.get_object()
        
        try:
            amount = Decimal(str(request.data.get('amount', 0)))
            
            result = TradingService.add_cash( 
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
        
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        portfolio = self.get_object()
        
        result = TradingService.get_portfolio_summary(
            user=request.user,
            portfolio_id=str(portfolio.id)
        )
        
        if result['success']:
            return Response(result['portfolio'], status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get']) 
    def portfolio(self, request):
        print(f"Portfolio request - User: {request.user}")
        print(f"Portfolio request - Auth: {request.auth}")
        print(f"Portfolio request - Headers: {request.headers}")
        print(f"Portfolio request - Is authenticated: {request.user.is_authenticated}")
        
        try:
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
    queryset = Stock.objects.filter(is_active=True)
    serializer_class = StockSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        try:
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
        try:
            stock = self.get_object()
            symbol = stock.symbol

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


class PredictionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PricePrediction.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PredictionSummarySerializer
        return PricePredictionSerializer
    
    @action(detail=False, methods=['get'])
    def predict(self, request):
        try:
            symbol = request.query_params.get('symbol', '').upper()
            if not symbol:
                return Response({
                    'status': 'error',
                    'message': 'Symbol parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            prediction_service = PredictionService()
            result = prediction_service.make_prediction(symbol)
            
            if result['status'] == 'success':
                return Response({
                    'status': 'success',
                    'data': result['data'],
                    'cached': result['cached']
                })
            else:
                return Response({
                    'status': 'error',
                    'message': result['message']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        try:
            symbol = request.query_params.get('symbol', '').upper()
            limit = int(request.query_params.get('limit', 10))
            
            if not symbol:
                return Response({
                    'status': 'error',
                    'message': 'Symbol parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            prediction_service = PredictionService()
            history = prediction_service.get_prediction_history(symbol, limit)
            
            return Response({
                'status': 'success',
                'data': history,
                'count': len(history)
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def performance(self, request):
        try:
            symbol = request.query_params.get('symbol', '').upper()
            
            if not symbol:
                return Response({
                    'status': 'error',
                    'message': 'Symbol parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            prediction_service = PredictionService()
            performance = prediction_service.get_model_performance(symbol)
            
            return Response(performance)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def available(self, request):
        try:
            limit = int(request.query_params.get('limit', 20))
            
            prediction_service = PredictionService()
            predictions = prediction_service.get_available_predictions(limit)
            
            return Response({
                'status': 'success',
                'data': predictions,
                'count': len(predictions)
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def update_actual_price(self, request):
        try:
            symbol = request.data.get('symbol', '').upper()
            actual_price = request.data.get('actual_price')
            
            if not symbol or actual_price is None:
                return Response({
                    'status': 'error',
                    'message': 'Symbol and actual_price are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            prediction_service = PredictionService()
            result = prediction_service.update_prediction_with_actual_price(symbol, float(actual_price))
            
            return Response(result)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def invalidate_cache(self, request):
        try:
            symbol = request.data.get('symbol', '').upper()
            
            if not symbol:
                return Response({
                    'status': 'error',
                    'message': 'Symbol parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            prediction_service = PredictionService()
            success = prediction_service.invalidate_prediction_cache(symbol)
            
            return Response({
                'status': 'success' if success else 'error',
                'message': f'Cache invalidated for {symbol}' if success else 'Failed to invalidate cache'
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def cache_stats(self, request):
        try:
            prediction_service = PredictionService()
            stats = prediction_service.get_cache_stats()
            
            return Response({
                'status': 'success',
                'data': stats
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def cleanup_cache(self, request):
        try:
            prediction_service = PredictionService()
            cleaned_count = prediction_service.cleanup_expired_cache()
            
            return Response({
                'status': 'success',
                'message': f'Cleaned up {cleaned_count} expired cache entries',
                'cleaned_count': cleaned_count
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PredictionModelViewSet(viewsets.ModelViewSet):
    queryset = PredictionModel.objects.all()
    serializer_class = PredictionModelSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['stock', 'model_type', 'status']
    search_fields = ['stock__symbol', 'stock__name']
    ordering_fields = ['created_at', 'updated_at', 'last_prediction_at']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def active_models(self, request):
        try:
            active_models = PredictionModel.objects.filter(
                status='trained'
            ).select_related('stock')
            
            serializer = self.get_serializer(active_models, many=True)
            
            return Response({
                'status': 'success',
                'data': serializer.data,
                'count': len(serializer.data)
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def by_symbol(self, request):
        try:
            symbol = request.query_params.get('symbol', '').upper()
            
            if not symbol:
                return Response({
                    'status': 'error',
                    'message': 'Symbol parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                stock = Stock.objects.get(symbol=symbol)
                models = PredictionModel.objects.filter(stock=stock)
                serializer = self.get_serializer(models, many=True)
                
                return Response({
                    'status': 'success',
                    'data': serializer.data,
                    'count': len(serializer.data)
                })
                
            except Stock.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': f'Stock {symbol} not found'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DataPreprocessingViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def data_summary(self, request):
        try:
            symbol = request.query_params.get('symbol', '').upper()
            
            if not symbol:
                return Response({
                    'status': 'error',
                    'message': 'Symbol parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data_service = DataPreprocessingService()
            summary = data_service.get_data_summary(symbol)
            
            return Response(summary)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def prepare_training_data(self, request):
        try:
            symbol = request.query_params.get('symbol', '').upper()
            days = int(request.query_params.get('days', 365))
            include_indicators = request.query_params.get('include_indicators', 'true').lower() == 'true'
            
            if not symbol:
                return Response({
                    'status': 'error',
                    'message': 'Symbol parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data_service = DataPreprocessingService()
            result = data_service.prepare_training_data(symbol, days, include_indicators)
            
            if result:
                return Response({
                    'status': 'success',
                    'metadata': result['metadata']
                })
            else:
                return Response({
                    'status': 'error',
                    'message': f'Unable to prepare training data for {symbol}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 