from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from .news_service import NewsService
from .models import Portfolio

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_news_for_symbol(request, symbol):
    
    try:

        force_refresh = request.GET.get('refresh', 'false').lower() == 'true'
        
        news_service = NewsService()
        articles = news_service.fetch_news_for_symbol(
            symbol=symbol.upper(),
            force_refresh=force_refresh
        )
        
        return Response({
            'status': 'success',
            'data': {
                'symbol': symbol.upper(),
                'articles': articles,
                'count': len(articles)
            }
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Failed to fetch news: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_portfolio_news(request):
    
    try:
        
        try:
            portfolio = Portfolio.objects.get(user=request.user)
        except Portfolio.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Portfolio not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        
        holdings = portfolio.holdings.all()
        symbols = list(set(holding.stock.symbol for holding in holdings if holding.stock and holding.stock.symbol))
        
        if not symbols:
            return Response({
                'status': 'success',
                'data': {
                    'news_by_symbol': {},
                    'symbols': []
                }
            })
        
        
        news_service = NewsService()
        force_refresh = request.GET.get('refresh', 'false').lower() == 'true'
        
        news_by_symbol = {}
        for symbol in symbols:
            try:
                articles = news_service.fetch_news_for_symbol(
                    symbol=symbol,
                    force_refresh=force_refresh
                )
                news_by_symbol[symbol] = articles[:5]  
            except Exception as e:
                news_by_symbol[symbol] = []
        
        return Response({
            'status': 'success',
            'data': {
                'news_by_symbol': news_by_symbol,
                'symbols': symbols,
                'total_articles': sum(len(articles) for articles in news_by_symbol.values())
            }
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Failed to fetch portfolio news: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cleanup_news_cache(request):
    try:
        days = int(request.data.get('days', 7))
        news_service = NewsService()
        deleted_count = news_service.cleanup_old_cache(days=days)
        
        return Response({
            'status': 'success',
            'message': f'Cleaned up {deleted_count} old articles',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Failed to cleanup cache: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_newsapi_config(request):
    """Test endpoint to verify NewsAPI configuration"""
    try:
        api_key = getattr(settings, 'NEWS_API_KEY', None)
        news_service = NewsService()
        
        return Response({
            'status': 'success',
            'data': {
                'api_key_configured': bool(api_key),
                'api_key_length': len(api_key) if api_key else 0,
                'api_key_preview': api_key[:8] + '...' if api_key else None,
                'service_initialized': bool(news_service.api_key)
            }
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Config test failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)