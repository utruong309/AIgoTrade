import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  ToggleButton,
  ToggleButtonGroup,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { marketAPI } from '../../services/api';

interface Stock {
  symbol: string;
  name: string;
  current_price: number;
  day_change: number;
  day_change_percent: number;
  volume: number;
}

interface StockChartProps {
  stock: Stock;
}

interface MarketDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export default function StockChart({ stock }: StockChartProps) {
  const [chartType, setChartType] = useState<'line' | 'area' | 'bar'>('line');
  const [timePeriod, setTimePeriod] = useState<'1day' | '1week' | '1month'>('1month');
  const [marketData, setMarketData] = useState<MarketDataPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStockData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await marketAPI.getStockDetail(stock.symbol);
      
      if (response.data.status === 'success' && response.data.stock?.market_data) {
        setMarketData(response.data.stock.market_data);
      } else {

        setMarketData([
          {
            date: new Date().toISOString().split('T')[0],
            open: stock.current_price * 0.99,
            high: stock.current_price * 1.02,
            low: stock.current_price * 0.98,
            close: stock.current_price,
            volume: stock.volume
          }
        ]);
      }
    } catch (err: any) {
      console.error('Error fetching stock data:', err);

      setMarketData([
        {
          date: new Date().toISOString().split('T')[0],
          open: stock.current_price * 0.99,
          high: stock.current_price * 1.02,
          low: stock.current_price * 0.98,
          close: stock.current_price,
          volume: stock.volume
        }
      ]);
    } finally {
      setLoading(false);
    }
  }, [stock.symbol, timePeriod]);

  useEffect(() => {
    fetchStockData();
  }, [fetchStockData]);

  const handleChartTypeChange = (
    event: React.MouseEvent<HTMLElement>,
    newChartType: 'line' | 'area' | 'bar' | null,
  ) => {
    if (newChartType !== null) {
      setChartType(newChartType);
    }
  };

  const handleTimePeriodChange = (
    event: React.MouseEvent<HTMLElement>,
    newTimePeriod: '1day' | '1week' | '1month' | null,
  ) => {
    if (newTimePeriod !== null) {
      setTimePeriod(newTimePeriod);
    }
  };

  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`;
  };

  const formatChange = (change: number) => {
    return change >= 0 ? `+$${change.toFixed(2)}` : `-$${Math.abs(change).toFixed(2)}`;
  };

  const formatChangePercent = (changePercent: number) => {
    return changePercent >= 0 ? `+${changePercent.toFixed(2)}%` : `${changePercent.toFixed(2)}%`;
  };

  const getChangeColor = (change: number) => {
    return change >= 0 ? 'success.main' : 'error.main';
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Stock Info Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2, alignItems: 'center' }}>
            <Box>
              <Typography variant="h4" component="h2" gutterBottom>
                {stock.symbol}
              </Typography>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {stock.name}
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="h3" component="div" gutterBottom>
                {formatPrice(stock.current_price)}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 1 }}>
                <Typography
                  variant="h6"
                  color={getChangeColor(stock.day_change)}
                  fontWeight="bold"
                >
                  {formatChange(stock.day_change)} ({formatChangePercent(stock.day_change_percent)})
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Volume: {stock.volume.toLocaleString()}
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Chart Controls */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Chart Type:
          </Typography>
          <ToggleButtonGroup
            value={chartType}
            exclusive
            onChange={handleChartTypeChange}
            size="small"
          >
            <ToggleButton value="line">Line</ToggleButton>
            <ToggleButton value="area">Area</ToggleButton>
            <ToggleButton value="bar">Bar</ToggleButton>
          </ToggleButtonGroup>

          <Typography variant="body2" color="text.secondary" sx={{ ml: 2 }}>
            Time Period:
          </Typography>
          <ToggleButtonGroup
            value={timePeriod}
            exclusive
            onChange={handleTimePeriodChange}
            size="small"
          >
            <ToggleButton value="1day">1 Day</ToggleButton>
            <ToggleButton value="1week">1 Week</ToggleButton>
            <ToggleButton value="1month">1 Month</ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </Paper>

      {/* Chart */}
      <Paper sx={{ p: 2, height: 500 }}>
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'line' ? (
            <LineChart data={marketData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis domain={['dataMin - 1', 'dataMax + 1']} />
              <Tooltip 
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
                labelFormatter={(label: any) => `Date: ${label}`}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="close" 
                stroke="#8884d8" 
                strokeWidth={2}
                dot={false}
                name="Close Price"
              />
            </LineChart>
          ) : chartType === 'area' ? (
            <AreaChart data={marketData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis domain={['dataMin - 1', 'dataMax + 1']} />
              <Tooltip 
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
                labelFormatter={(label) => `Date: ${label}`}
              />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="close" 
                stroke="#8884d8" 
                fill="#8884d8" 
                fillOpacity={0.3}
                name="Close Price"
              />
            </AreaChart>
          ) : (
            <BarChart data={marketData} barGap={0}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis domain={['dataMin - 1', 'dataMax + 1']} />
              <Tooltip 
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
                labelFormatter={(label) => `Date: ${label}`}
              />
              <Legend />
              <Bar 
                dataKey="close" 
                fill="#8884d8" 
                name="Close Price"
              />
            </BarChart>
          )}
        </ResponsiveContainer>
      </Paper>

      {/* Data Summary */}
      {marketData.length > 0 && (
        <Paper sx={{ p: 2, mt: 2 }}>
          <Typography variant="h6" gutterBottom>
            Data Summary
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr 1fr 1fr' }, gap: 2 }}>
            <Box>
              <Typography variant="body2" color="text.secondary">Data Points</Typography>
              <Typography variant="h6">{marketData.length}</Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">Date Range</Typography>
              <Typography variant="h6">
                {marketData[0]?.date} to {marketData[marketData.length - 1]?.date}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">Highest Price</Typography>
              <Typography variant="h6" color="success.main">
                {formatPrice(Math.max(...marketData.map(d => d.high)))}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">Lowest Price</Typography>
              <Typography variant="h6" color="error.main">
                {formatPrice(Math.min(...marketData.map(d => d.low)))}
              </Typography>
            </Box>
          </Box>
        </Paper>
      )}
    </Box>
  );
}
