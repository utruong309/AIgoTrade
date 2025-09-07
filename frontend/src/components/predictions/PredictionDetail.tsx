import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Alert,
  CircularProgress,
  Button,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Psychology,
  Refresh,
  History,
  Assessment,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { PricePrediction, PredictionModel } from '../../types';
import predictionApi from '../../services/predictionApi';

interface PredictionDetailProps {
  symbol: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`prediction-tabpanel-${index}`}
      aria-labelledby={`prediction-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

const PredictionDetail: React.FC<PredictionDetailProps> = ({ symbol }) => {
  const [currentPrediction, setCurrentPrediction] = useState<any>(null);
  const [predictionHistory, setPredictionHistory] = useState<PricePrediction[]>([]);
  const [models, setModels] = useState<PredictionModel[]>([]);
  const [performance, setPerformance] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);

  const fetchData = async () => {
    try {
      setError(null);
      setLoading(true);

      const [prediction, history, modelsData, performanceData] = await Promise.all([
        predictionApi.getPrediction(symbol),
        predictionApi.getPredictionHistory(symbol, 20),
        predictionApi.getModelsBySymbol(symbol),
        predictionApi.getModelPerformance(symbol),
      ]);

      setCurrentPrediction(prediction);
      setPredictionHistory(history);
      setModels(modelsData);
      setPerformance(performanceData);
    } catch (err) {
      setError('Failed to fetch prediction data');
      console.error('Error fetching prediction data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [symbol]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

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

  const chartData = predictionHistory
    .slice()
    .reverse()
    .map((pred) => ({
      date: new Date(pred.prediction_timestamp).toLocaleDateString(),
      predicted: pred.predicted_price,
      actual: pred.actual_price || null,
      current: pred.current_price,
    }));

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        {error}
      </Alert>
    );
  }

  if (!currentPrediction) {
    return (
      <Alert severity="warning" sx={{ mb: 3 }}>
        No prediction data available for {symbol}
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            {currentPrediction.symbol} - {currentPrediction.name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Last updated: {new Date(currentPrediction.prediction_timestamp).toLocaleString()}
          </Typography>
        </Box>
        
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchData}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" flexDirection={{ xs: 'column', md: 'row' }} gap={3}>
            <Box flex={1}>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <Typography variant="h6">Current Price</Typography>
                <Typography variant="h4" fontWeight="bold">
                  {formatPrice(currentPrediction.current_price)}
                </Typography>
              </Box>
              
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <Typography variant="h6">Predicted Price</Typography>
                <Typography 
                  variant="h4" 
                  fontWeight="bold"
                  color={getTrendColor(currentPrediction.price_change)}
                >
                  {formatPrice(currentPrediction.predicted_price)}
                </Typography>
                {getTrendIcon(currentPrediction.price_change)}
              </Box>
            </Box>
            
            <Box flex={1}>
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Expected Change
                </Typography>
                <Typography 
                  variant="h5" 
                  fontWeight="bold"
                  color={getTrendColor(currentPrediction.price_change)}
                >
                  {formatPrice(Math.abs(currentPrediction.price_change))} ({formatPercent(currentPrediction.price_change_percent)})
                </Typography>
              </Box>
              
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Confidence Level
                </Typography>
                <Box display="flex" alignItems="center" gap={1}>
                  <Chip
                    icon={<Psychology />}
                    label={currentPrediction.confidence_level.toUpperCase()}
                    color={getConfidenceColor(currentPrediction.confidence_level) as any}
                    variant="outlined"
                  />
                  <Typography variant="body2">
                    {(currentPrediction.confidence_score * 100).toFixed(1)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={currentPrediction.confidence_score * 100}
                  sx={{ mt: 1, height: 6 }}
                />
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab icon={<History />} label="History" />
          <Tab icon={<Assessment />} label="Performance" />
          <Tab icon={<Psychology />} label="Models" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <Box display="flex" flexDirection={{ xs: 'column', md: 'row' }} gap={3}>
          <Box flex={2}>
            <Typography variant="h6" gutterBottom>
              Prediction vs Actual Prices
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <RechartsTooltip formatter={(value, name) => [formatPrice(value as number), name]} />
                <Line
                  type="monotone"
                  dataKey="predicted"
                  stroke="#8884d8"
                  strokeWidth={2}
                  name="Predicted"
                />
                <Line
                  type="monotone"
                  dataKey="actual"
                  stroke="#82ca9d"
                  strokeWidth={2}
                  name="Actual"
                />
                <Line
                  type="monotone"
                  dataKey="current"
                  stroke="#ffc658"
                  strokeWidth={2}
                  name="Current"
                />
              </LineChart>
            </ResponsiveContainer>
          </Box>
          
          <Box flex={1}>
            <Typography variant="h6" gutterBottom>
              Recent Predictions
            </Typography>
            <TableContainer component={Paper} sx={{ maxHeight: 300 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Predicted</TableCell>
                    <TableCell>Actual</TableCell>
                    <TableCell>Accuracy</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {predictionHistory.slice(0, 10).map((pred) => (
                    <TableRow key={pred.id}>
                      <TableCell>
                        {new Date(pred.prediction_date).toLocaleDateString()}
                      </TableCell>
                      <TableCell>{formatPrice(pred.predicted_price)}</TableCell>
                      <TableCell>
                        {pred.actual_price ? formatPrice(pred.actual_price) : '-'}
                      </TableCell>
                      <TableCell>
                        {pred.prediction_accuracy ? `${pred.prediction_accuracy.toFixed(1)}%` : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        </Box>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {performance?.status === 'success' ? (
          <Box display="flex" flexDirection={{ xs: 'column', md: 'row' }} gap={3}>
            <Box flex={1}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Model Performance Metrics
                  </Typography>
                  <Box display="flex" flexDirection="column" gap={2}>
                    <Box display="flex" justifyContent="space-between">
                      <Typography>Average Accuracy:</Typography>
                      <Typography fontWeight="bold">
                        {performance.data.average_accuracy.toFixed(1)}%
                      </Typography>
                    </Box>
                    <Box display="flex" justifyContent="space-between">
                      <Typography>Total Predictions:</Typography>
                      <Typography fontWeight="bold">
                        {performance.data.total_predictions}
                      </Typography>
                    </Box>
                    <Box display="flex" justifyContent="space-between">
                      <Typography>Max Accuracy:</Typography>
                      <Typography fontWeight="bold">
                        {performance.data.max_accuracy.toFixed(1)}%
                      </Typography>
                    </Box>
                    <Box display="flex" justifyContent="space-between">
                      <Typography>Min Accuracy:</Typography>
                      <Typography fontWeight="bold">
                        {performance.data.min_accuracy.toFixed(1)}%
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Box>
            
            <Box flex={1}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Accuracy Trend
                  </Typography>
                  <Box display="flex" flexDirection="column" gap={1}>
                    {performance.data.accuracy_trend?.map((accuracy: number, index: number) => (
                      <Box key={index} display="flex" alignItems="center" gap={1}>
                        <Typography variant="body2" sx={{ minWidth: 60 }}>
                          Day {index + 1}:
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={accuracy}
                          sx={{ flexGrow: 1, height: 8 }}
                        />
                        <Typography variant="body2" sx={{ minWidth: 50 }}>
                          {accuracy.toFixed(1)}%
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Box>
          </Box>
        ) : (
          <Alert severity="info">
            No performance data available yet. Performance metrics will be available after predictions are evaluated.
          </Alert>
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Box display="flex" flexWrap="wrap" gap={3}>
          {models.map((model) => (
            <Box key={model.id} flex={{ xs: '1 1 100%', md: '1 1 calc(50% - 12px)' }}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">
                      {model.model_type.toUpperCase()} Model
                    </Typography>
                    <Chip
                      label={model.status.toUpperCase()}
                      color={model.status === 'trained' ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>
                  
                  <Box display="flex" flexDirection="column" gap={1}>
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2">Training Data Points:</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {model.training_data_points}
                      </Typography>
                    </Box>
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2">Training Duration:</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {model.training_duration_days} days
                      </Typography>
                    </Box>
                    {model.train_rmse && (
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Training RMSE:</Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {model.train_rmse.toFixed(4)}
                        </Typography>
                      </Box>
                    )}
                    {model.val_rmse && (
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Validation RMSE:</Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {model.val_rmse.toFixed(4)}
                        </Typography>
                      </Box>
                    )}
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2">Last Prediction:</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {model.last_prediction_at 
                          ? new Date(model.last_prediction_at).toLocaleString()
                          : 'Never'
                        }
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Box>
          ))}
        </Box>
      </TabPanel>
    </Box>
  );
};

export default PredictionDetail;
