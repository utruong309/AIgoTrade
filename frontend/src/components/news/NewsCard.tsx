import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Link
} from '@mui/material';
import { OpenInNew, Schedule } from '@mui/icons-material';
import { NewsArticle } from '../../services/newsApi';

interface NewsCardProps {
  article: NewsArticle;
  symbol?: string;
}

const NewsCard: React.FC<NewsCardProps> = ({ article, symbol }) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${diffInHours}h ago`;
    } else {
      const diffInDays = Math.floor(diffInHours / 24);
      return `${diffInDays}d ago`;
    }
  };

  const handleArticleClick = () => {
    window.open(article.url, '_blank', 'noopener,noreferrer');
  };

  return (
    <Card 
      sx={{ 
        mb: 2, 
        cursor: 'pointer',
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: 3
        }
      }}
      onClick={handleArticleClick}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
          {symbol && (
            <Chip 
              label={symbol} 
              size="small" 
              color="primary" 
              sx={{ mb: 1 }}
            />
          )}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Schedule fontSize="small" color="disabled" />
            <Typography variant="caption" color="text.secondary">
              {formatDate(article.publishedAt)}
            </Typography>
          </Box>
        </Box>

        <Typography 
          variant="h6" 
          component="h3" 
          sx={{ 
            mb: 1,
            fontSize: '1rem',
            fontWeight: 600,
            lineHeight: 1.3,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden'
          }}
        >
          {article.title}
        </Typography>

        {article.description && (
          <Typography 
            variant="body2" 
            color="text.secondary"
            sx={{
              mb: 2,
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              lineHeight: 1.4
            }}
          >
            {article.description}
          </Typography>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="caption" color="primary" fontWeight={500}>
            {article.source}
          </Typography>
          
          <Link
            component="span"
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 0.5,
              color: 'primary.main',
              textDecoration: 'none',
              fontSize: '0.75rem',
              fontWeight: 500,
              '&:hover': {
                textDecoration: 'underline'
              }
            }}
          >
            Read More
            <OpenInNew fontSize="inherit" />
          </Link>
        </Box>
      </CardContent>
    </Card>
  );
};

export default NewsCard;