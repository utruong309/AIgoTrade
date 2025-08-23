import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Button,
  Divider,
  Chip
} from '@mui/material';
import { Refresh, TrendingUp } from '@mui/icons-material';
import { newsAPI, NewsArticle, PortfolioNewsResponse } from '../../services/newsApi';
import NewsCard from './NewsCard';

interface NewsFeedProps {
  maxArticles?: number;
  showRefreshButton?: boolean;
}

const NewsFeed: React.FC<NewsFeedProps> = ({ 
  maxArticles = 10, 
  showRefreshButton = true 
}) => {
  const [news, setNews] = useState<PortfolioNewsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const fetchNews = async (forceRefresh = false) => {
    try {
      if (forceRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      const response = await newsAPI.getPortfolioNews(forceRefresh);
      setNews(response);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (err: any) {
      console.error('Failed to fetch news:', err);
      setError(err.response?.data?.message || 'Failed to fetch news');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchNews();
  }, []);

  // Flatten and sort all articles by publish date
  const getAllArticles = (): Array<NewsArticle & { symbol: string }> => {
    if (!news?.data.news_by_symbol) return [];

    const allArticles: Array<NewsArticle & { symbol: string }> = [];
    
    Object.entries(news.data.news_by_symbol).forEach(([symbol, articles]) => {
      articles.forEach(article => {
        allArticles.push({ ...article, symbol });
      });
    });

    // Sort by publish date (newest first)
    return allArticles
      .sort((a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime())
      .slice(0, maxArticles);
  };

  const allArticles = getAllArticles();

  if (loading) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Loading latest financial news...
        </Typography>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="outlined" onClick={() => fetchNews()} startIcon={<Refresh />}>
          Try Again
        </Button>
      </Paper>
    );
  }

  if (!news?.data.symbols.length) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <TrendingUp color="disabled" sx={{ fontSize: 48, mb: 2 }} />
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No Portfolio Holdings
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Add some stocks to your portfolio to see relevant financial news
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TrendingUp color="primary" />
            Latest Financial News
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {news.data.total_articles} articles from your portfolio holdings
          </Typography>
        </Box>
        
        {showRefreshButton && (
          <Button
            variant="outlined"
            size="small"
            startIcon={refreshing ? <CircularProgress size={16} /> : <Refresh />}
            onClick={() => fetchNews(true)}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        )}
      </Box>

      {/* Portfolio Symbols */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Following:
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {news.data.symbols.map(symbol => (
            <Chip
              key={symbol}
              label={symbol}
              size="small"
              variant="outlined"
              color="primary"
            />
          ))}
        </Box>
      </Box>

      <Divider sx={{ mb: 3 }} />

      {/* News Articles */}
      {allArticles.length > 0 ? (
        <Box>
          {allArticles.map((article, index) => (
            <NewsCard
              key={`${article.symbol}-${article.id}-${index}`}
              article={article}
              symbol={article.symbol}
            />
          ))}
          
          {/* Last Update Info */}
          {lastUpdate && (
            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Last updated: {lastUpdate}
              </Typography>
            </Box>
          )}
        </Box>
      ) : (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Recent News
          </Typography>
          <Typography variant="body2" color="text.secondary">
            No financial news found for your portfolio holdings
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default NewsFeed;