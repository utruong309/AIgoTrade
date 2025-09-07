import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Chip,
  Box,
  LinearProgress,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Psychology,
  Refresh,
  Info,
} from '@mui/icons-material';
import { PredictionSummary } from '../../types';

interface PredictionCardProps {
  prediction: PredictionSummary;
  onRefresh?: () => void;
  onSymbolSelect?: (symbol: string) => void;
  loading?: boolean;
}

const PredictionCard: React.FC<PredictionCardProps> = ({
  prediction,
  onRefresh,
  onSymbolSelect,
  loading = false,
}) => {
  const formatPrice = (price: number) => `$${price.toFixed(2)}`;
  const formatPercent = (percent: number) => `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;

  const getConfidenceColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'high':
        return 'success';
      case 'medium':
        return 'warning';
      case 'low':
        return 'error';
      default:
        return 'default';
    }
  };

  const getTrendIcon = (change: number) => {
    return change >= 0 ? (
      <TrendingUp color="success" />
    ) : (
      <TrendingDown color="error" />
    );
  };

  const getTrendColor = (change: number) => {
    return change >= 0 ? 'success.main' : 'error.main';
  };

  const handleCardClick = () => {
    if (onSymbolSelect) {
      onSymbolSelect(prediction.symbol);
    }
  };

  return (
    <Card 
      sx={{ 
        height: '100%', 
        position: 'relative',
        cursor: onSymbolSelect ? 'pointer' : 'default',
        '&:hover': onSymbolSelect ? {
          boxShadow: 4,
          transform: 'translateY(-2px)',
          transition: 'all 0.2s ease-in-out',
        } : {},
      }}
      onClick={handleCardClick}
    >
      {loading && (
        <LinearProgress
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            zIndex: 1,
          }}
        />
      )}
      
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box>
            <Typography variant="h6" component="div" fontWeight="bold">
              {prediction.symbol}
            </Typography>
            <Typography variant="body2" color="text.secondary" noWrap>
              {prediction.name}
            </Typography>
          </Box>
          
          {onRefresh && (
            <IconButton
              size="small"
              onClick={onRefresh}
              disabled={loading}
              sx={{ ml: 1 }}
            >
              <Refresh />
            </IconButton>
          )}
        </Box>

        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Current Price
            </Typography>
            <Typography variant="h6" fontWeight="bold">
              {formatPrice(prediction.current_price)}
            </Typography>
          </Box>
          
          <Box textAlign="right">
            <Typography variant="body2" color="text.secondary">
              Predicted Price
            </Typography>
            <Typography 
              variant="h6" 
              fontWeight="bold"
              color={getTrendColor(prediction.price_change)}
            >
              {formatPrice(prediction.predicted_price)}
            </Typography>
          </Box>
        </Box>

        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            {getTrendIcon(prediction.price_change)}
            <Typography
              variant="body1"
              fontWeight="bold"
              color={getTrendColor(prediction.price_change)}
            >
              {formatPrice(Math.abs(prediction.price_change))}
            </Typography>
            <Typography
              variant="body2"
              color={getTrendColor(prediction.price_change)}
            >
              ({formatPercent(prediction.price_change_percent)})
            </Typography>
          </Box>
          
          <Chip
            icon={<Psychology />}
            label={prediction.confidence_level.toUpperCase()}
            color={getConfidenceColor(prediction.confidence_level) as any}
            size="small"
            variant="outlined"
          />
        </Box>

        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="caption" color="text.secondary">
              Confidence: {(prediction.confidence_score * 100).toFixed(1)}%
            </Typography>
            <LinearProgress
              variant="determinate"
              value={prediction.confidence_score * 100}
              sx={{
                mt: 0.5,
                height: 4,
                borderRadius: 2,
                backgroundColor: 'grey.200',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: getConfidenceColor(prediction.confidence_level) === 'success' 
                    ? 'success.main' 
                    : getConfidenceColor(prediction.confidence_level) === 'warning'
                    ? 'warning.main'
                    : 'error.main',
                },
              }}
            />
          </Box>
          
          <Tooltip title={`Prediction for ${new Date(prediction.prediction_date).toLocaleDateString()}`}>
            <IconButton size="small">
              <Info fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>

        <Box mt={2} pt={1} borderTop="1px solid" borderColor="divider">
          <Typography variant="caption" color="text.secondary">
            Model: {prediction.model_type.toUpperCase()} • 
            Updated: {new Date(prediction.prediction_timestamp).toLocaleTimeString()}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default PredictionCard;
