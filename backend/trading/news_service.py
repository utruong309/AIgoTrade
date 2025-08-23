import requests
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from typing import List, Dict
import logging
from .models import NewsArticle

logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self):
        self.api_key = getattr(settings, 'NEWS_API_KEY', None)
        self.base_url = "https://newsapi.org/v2"
        
        # Debug logging to check API key
        if self.api_key:
            logger.info(f"NewsService initialized with API key: {self.api_key[:8]}...")
        else:
            logger.warning("NewsService initialized without API key")
        
    def fetch_news_for_symbol(self, symbol: str, force_refresh: bool = False) -> List[Dict]:
        
        if not force_refresh and NewsArticle.is_cache_valid(symbol):
            logger.info(f"Using cached news for {symbol}")
            return self._get_cached_news(symbol)
        
        logger.info(f"Fetching fresh news for {symbol}")
        try:
            articles = self._fetch_from_newsapi(symbol)
            if articles:
                self._cache_articles(symbol, articles)
                return self._get_cached_news(symbol)
            else:
                return self._get_cached_news(symbol)
                
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {str(e)}")
            return self._get_cached_news(symbol)
    
    def _fetch_from_newsapi(self, symbol: str) -> List[Dict]:
        """Fetch news from NewsAPI with improved error handling"""
        
        # Check if API key is configured
        if not self.api_key:
            logger.warning("NEWS_API_KEY not configured")
            return self._get_sample_data(symbol)

        logger.info(f"Fetching real news for {symbol} from NewsAPI")
        
        # NewsAPI endpoint
        url = f"{self.base_url}/everything"
        
        # Build search query - more specific for better results
        query = f'({symbol} AND stock) OR ("{symbol} earnings") OR ("{symbol} financial")'
        
        params = {
            'q': query,
            'apiKey': self.api_key,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 15,  # Reduced for better quality
            'from': (timezone.now() - timedelta(days=3)).strftime('%Y-%m-%d'),  # Last 3 days for more recent news
            'domains': 'reuters.com,bloomberg.com,cnbc.com,marketwatch.com,yahoo.com,wsj.com'  # Trusted financial sources
        }
        
        try:
            logger.info(f"Making NewsAPI request for {symbol}")
            response = requests.get(url, params=params, timeout=15)
            
            # Log the response status
            logger.info(f"NewsAPI response status: {response.status_code}")
            
            if response.status_code == 401:
                logger.error("NewsAPI authentication failed - check your API key")
                return self._get_sample_data(symbol)
            elif response.status_code == 429:
                logger.error("NewsAPI rate limit exceeded")
                return self._get_sample_data(symbol)
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'ok':
                articles = data.get('articles', [])
                logger.info(f"Retrieved {len(articles)} articles for {symbol}")
                
                # Filter out articles with missing data
                filtered_articles = []
                for article in articles:
                    if (article.get('title') and 
                        article.get('url') and 
                        article.get('title') != '[Removed]' and
                        article.get('description')):
                        filtered_articles.append(article)
                
                logger.info(f"Filtered to {len(filtered_articles)} quality articles for {symbol}")
                return filtered_articles
            else:
                error_msg = data.get('message', 'Unknown error')
                logger.error(f"NewsAPI error: {error_msg}")
                return self._get_sample_data(symbol)
                
        except requests.Timeout:
            logger.error("NewsAPI request timed out")
            return self._get_sample_data(symbol)
        except requests.RequestException as e:
            logger.error(f"Request error fetching news: {str(e)}")
            return self._get_sample_data(symbol)
        except Exception as e:
            logger.error(f"Unexpected error fetching news: {str(e)}")
            return self._get_sample_data(symbol)
    
    def _get_sample_data(self, symbol: str) -> List[Dict]:
        """Return sample data as fallback"""
        return [
            {
                'title': f'{symbol} Stock Performance Update',
                'description': f'Latest market analysis and performance metrics for {symbol} stock',
                'url': 'https://example.com/news',
                'source': {'name': 'Financial News'},
                'publishedAt': timezone.now().isoformat()
            },
            {
                'title': f'{symbol} Quarterly Earnings Preview',
                'description': f'Analysts expectations and key metrics to watch for {symbol} earnings',
                'url': 'https://example.com/earnings',
                'source': {'name': 'Market Analysis'},
                'publishedAt': (timezone.now() - timedelta(hours=2)).isoformat()
            }
        ]
    
    def _cache_articles(self, symbol: str, articles: List[Dict]):
        for article_data in articles:
            try:
                published_str = article_data.get('publishedAt')
                if published_str:
                    try:
                        published_at = datetime.fromisoformat(
                            published_str.replace('Z', '+00:00')
                        )
                    except ValueError:
                        published_at = timezone.now()
                else:
                    published_at = timezone.now()
                
                NewsArticle.objects.update_or_create(
                    symbol=symbol,
                    url=article_data.get('url', ''),
                    defaults={
                        'title': article_data.get('title', ''),
                        'description': article_data.get('description', ''),
                        'source': article_data.get('source', {}).get('name', 'Unknown'),
                        'published_at': published_at,
                    }
                )
                
            except Exception as e:
                logger.error(f"Error caching article: {str(e)}")
                continue
    
    def _get_cached_news(self, symbol: str) -> List[Dict]:
        try:
            articles = NewsArticle.objects.filter(symbol=symbol)[:20]
            
            return [
                {
                    'id': article.id,
                    'title': article.title,
                    'description': article.description,
                    'url': article.url,
                    'source': article.source,
                    'publishedAt': article.published_at.isoformat(),
                    'cachedAt': article.cached_at.isoformat(),
                }
                for article in articles
            ]
        except Exception as e:
            logger.error(f"Error getting cached news: {str(e)}")
            return []
    
    def fetch_news_for_portfolio(self, user_holdings: List[str]) -> Dict[str, List[Dict]]:
        news_by_symbol = {}
        
        for symbol in user_holdings:
            news_by_symbol[symbol] = self.fetch_news_for_symbol(symbol)
        
        return news_by_symbol
    
    def cleanup_old_cache(self, days: int = 7):
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            deleted_count = NewsArticle.objects.filter(
                cached_at__lt=cutoff_date
            ).delete()[0]
            
            logger.info(f"Cleaned up {deleted_count} old cached articles")
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up cache: {str(e)}")
            return 0