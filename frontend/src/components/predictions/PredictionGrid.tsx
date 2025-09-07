import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Alert,
  CircularProgress,
  Button,
  TextField,
  InputAdornment,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Search,
  Refresh,
  Psychology,
  TrendingUp,
  TrendingDown,
  Wifi,
  WifiOff,
} from '@mui/icons-material';
import PredictionCard from './PredictionCard';
import { PredictionSummary } from '../../types';
import predictionApi from '../../services/predictionApi';
import { usePredictionPolling, usePredictionUpdates } from '../../services/predictionPolling';

interface PredictionGridProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
  onSymbolSelect?: (symbol: string) => void;
  usePolling?: boolean;
}

const PredictionGrid: React.FC<PredictionGridProps> = ({
  autoRefresh = true,
  refreshInterval = 15000,
  onSymbolSelect,
  usePolling = true,
}) => {
  const [predictions, setPredictions] = useState<PredictionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [confidenceFilter, setConfidenceFilter] = useState<string>('all');
  const [trendFilter, setTrendFilter] = useState<string>('all');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [usePollingUpdates, setUsePollingUpdates] = useState(usePolling);

  const { isActive: pollingActive } = usePredictionPolling(refreshInterval, usePolling);
  const pollingUpdates = usePredictionUpdates();

  const fetchPredictions = async () => {
    try {
      setError(null);
      const data = await predictionApi.getAvailablePredictions(50);
      setPredictions(data);
      setLastUpdated(new Date());
    } catch (err) {
      setError('Failed to fetch predictions');
      console.error('Error fetching predictions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, []);

  useEffect(() => {
    if (usePollingUpdates && pollingUpdates.length > 0) {
      const latestUpdate = pollingUpdates[0];
      
      setPredictions(prev => {
        const updated = [...prev];
        const index = updated.findIndex(p => p.symbol === latestUpdate.symbol);
        
        if (index !== -1) {
          updated[index] = {
            ...updated[index],
            predicted_price: latestUpdate.predicted_price,
            current_price: latestUpdate.current_price,
            price_change: latestUpdate.price_change,
            price_change_percent: latestUpdate.price_change_percent,
            confidence_score: latestUpdate.confidence_score,
            confidence_level: latestUpdate.confidence_level,
            prediction_timestamp: latestUpdate.prediction_timestamp,
          };
        }
        
        return updated;
      });
      
      setLastUpdated(new Date());
    }
  }, [pollingUpdates, usePollingUpdates]);

  useEffect(() => {
    if (autoRefresh && !usePollingUpdates) {
      const interval = setInterval(fetchPredictions, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, usePollingUpdates]);

  const filteredPredictions = predictions.filter((prediction) => {
    const matchesSearch = prediction.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         prediction.name.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesConfidence = confidenceFilter === 'all' || 
                             prediction.confidence_level === confidenceFilter;
    
    const matchesTrend = trendFilter === 'all' ||
                        (trendFilter === 'up' && prediction.price_change >= 0) ||
                        (trendFilter === 'down' && prediction.price_change < 0);
    
    return matchesSearch && matchesConfidence && matchesTrend;
  });

  const handleRefresh = () => {
    setLoading(true);
    fetchPredictions();
  };

  const getStats = () => {
    const total = predictions.length;
    const bullish = predictions.filter(p => p.price_change >= 0).length;
    const bearish = total - bullish;
    const highConfidence = predictions.filter(p => p.confidence_level === 'high').length;
    
    return { total, bullish, bearish, highConfidence };
  };

  const stats = getStats();

  if (loading && predictions.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            AI Price Predictions
          </Typography>
          <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="body2" color="text.secondary">
              {lastUpdated && `Last updated: ${lastUpdated.toLocaleTimeString()}`}
            </Typography>
            {usePollingUpdates && (
              <Box display="flex" alignItems="center" gap={1}>
                {pollingActive ? (
                  <Wifi color="success" fontSize="small" />
                ) : (
                  <WifiOff color="error" fontSize="small" />
                )}
                <Typography variant="caption" color={pollingActive ? 'success.main' : 'error.main'}>
                  {pollingActive ? 'Auto Updates' : 'Manual'}
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
        
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={handleRefresh}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      <Box display="flex" flexWrap="wrap" gap={2} mb={3}>
        <Box flex={{ xs: '1 1 100%', sm: '1 1 calc(50% - 8px)', md: '1 1 calc(25% - 12px)' }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1}>
                <Psychology color="primary" />
                <Box>
                  <Typography variant="h6">{stats.total}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Predictions
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>
        
        <Box flex={{ xs: '1 1 100%', sm: '1 1 calc(50% - 8px)', md: '1 1 calc(25% - 12px)' }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1}>
                <TrendingUp color="success" />
                <Box>
                  <Typography variant="h6">{stats.bullish}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Bullish Predictions
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>
        
        <Box flex={{ xs: '1 1 100%', sm: '1 1 calc(50% - 8px)', md: '1 1 calc(25% - 12px)' }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1}>
                <TrendingDown color="error" />
                <Box>
                  <Typography variant="h6">{stats.bearish}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Bearish Predictions
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>
        
        <Box flex={{ xs: '1 1 100%', sm: '1 1 calc(50% - 8px)', md: '1 1 calc(25% - 12px)' }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1}>
                <Chip label="HIGH" color="success" size="small" />
                <Box>
                  <Typography variant="h6">{stats.highConfidence}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    High Confidence
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>

      <Box display="flex" gap={2} mb={3} flexWrap="wrap" alignItems="center">
        <TextField
          placeholder="Search stocks..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            ),
          }}
          sx={{ minWidth: 200 }}
        />
        
        <FormControl sx={{ minWidth: 120 }}>
          <InputLabel>Confidence</InputLabel>
          <Select
            value={confidenceFilter}
            label="Confidence"
            onChange={(e) => setConfidenceFilter(e.target.value)}
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="high">High</MenuItem>
            <MenuItem value="medium">Medium</MenuItem>
            <MenuItem value="low">Low</MenuItem>
          </Select>
        </FormControl>
        
        <FormControl sx={{ minWidth: 120 }}>
          <InputLabel>Trend</InputLabel>
          <Select
            value={trendFilter}
            label="Trend"
            onChange={(e) => setTrendFilter(e.target.value)}
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="up">Bullish</MenuItem>
            <MenuItem value="down">Bearish</MenuItem>
          </Select>
        </FormControl>
        
        <FormControlLabel
          control={
            <Switch
              checked={usePollingUpdates}
              onChange={(e) => setUsePollingUpdates(e.target.checked)}
              color="primary"
            />
          }
          label="Auto Updates"
        />
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {filteredPredictions.length === 0 ? (
        <Box textAlign="center" py={4}>
          <Typography variant="h6" color="text.secondary">
            No predictions found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Try adjusting your filters or check back later
          </Typography>
        </Box>
      ) : (
        <Box display="flex" flexWrap="wrap" gap={3}>
          {filteredPredictions.map((prediction) => (
            <Box key={prediction.symbol} flex={{ xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(33.333% - 16px)', lg: '1 1 calc(25% - 18px)' }}>
              <PredictionCard
                prediction={prediction}
                onRefresh={handleRefresh}
                onSymbolSelect={onSymbolSelect}
                loading={loading}
              />
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
};

export default PredictionGrid;
