import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab
} from '@mui/material';
import { TrendingUp, Search, ShowChart } from '@mui/icons-material';
import MarketSearch from './MarketSearch';
import StockChart from './StockChart';
import TradingPanel from '../trading/TradingPanel';

interface Stock {
  symbol: string;
  name: string;
  current_price: number;
  day_change: number;
  day_change_percent: number;
  volume: number;
  last_updated: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`market-tabpanel-${index}`}
      aria-labelledby={`market-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function MarketPage() {
  const [tabValue, setTabValue] = useState(0);
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [realTimeStocks, setRealTimeStocks] = useState<Stock[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<string>('Connecting...');
  const [lastUpdate, setLastUpdate] = useState<string>('');

  useEffect(() => {
    fetchInitialData();
    
    const interval = setInterval(fetchInitialData, 15000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchInitialData = async () => {
    try {
      setConnectionStatus('Fetching market data...');
      
      const token = localStorage.getItem('authToken');
      if (!token) {
        setConnectionStatus('Authentication required');
        return;
      }
      
      const response = await fetch('http://localhost:8000/api/stocks/trending/', {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success' && data.data) {
          const stocks = data.data.map((stock: any) => ({
            symbol: stock.symbol,
            name: stock.name || `${stock.symbol} Stock`,
            current_price: parseFloat(stock.current_price) || 0,
            day_change: parseFloat(stock.day_change) || 0,
            day_change_percent: parseFloat(stock.day_change_percent) || 0,
            volume: parseInt(stock.volume) || 0,
            last_updated: new Date().toLocaleTimeString()
          }));
          
          setRealTimeStocks(stocks);
          setConnectionStatus('Connected to live market feed');
          setLastUpdate(new Date().toLocaleTimeString());
        } else {
          setConnectionStatus('No market data available');
        }
      } else {
        setConnectionStatus('Failed to fetch market data');
      }
    } catch (error) {
      console.error('Failed to fetch initial data:', error);
      setConnectionStatus('Failed to connect to market feed');
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleStockSelect = (stock: Stock) => {
    setSelectedStock(stock);
    setTabValue(1); 
  };

  const handleTradeExecuted = () => {
    console.log('Trade executed successfully');
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Market Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Live stock data, charts, and trading
        </Typography>
        <Typography variant="body2" color="primary" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box 
            component="span" 
            sx={{ 
              width: 8, 
              height: 8, 
              borderRadius: '50%', 
              bgcolor: connectionStatus.includes('Connected') ? 'success.main' : 'warning.main' 
            }} 
          />
          {connectionStatus}
          {lastUpdate && (
            <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
              Last update: {lastUpdate}
            </Typography>
          )}
        </Typography>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="market tabs">
          <Tab 
            icon={<Search />} 
            label="Market Search" 
            iconPosition="start"
          />
          <Tab 
            icon={<ShowChart />} 
            label="Stock Chart" 
            iconPosition="start"
          />
          <Tab 
            icon={<TrendingUp />} 
            label="Live Market Data" 
            iconPosition="start"
          />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
          <Box>
            <MarketSearch onStockSelect={handleStockSelect} />
          </Box>
          <Box>
            <Paper sx={{ p: 3, height: 'fit-content' }}>
              <Typography variant="h6" gutterBottom>
                Trading Panel
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Select a stock from the search to start trading
              </Typography>
            </Paper>
          </Box>
        </Box>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, gap: 3 }}>
          <Box>
            {selectedStock ? (
              <StockChart stock={selectedStock} />
            ) : (
              <Paper sx={{ p: 3, textAlign: 'center', height: 400 }}>
                <ShowChart sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  Select a Stock
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Choose a stock from the market search to view charts and trading options
                </Typography>
              </Paper>
            )}
          </Box>
          <Box>
            <TradingPanel 
              selectedStock={selectedStock} 
              onTradeExecuted={handleTradeExecuted}
            />
          </Box>
        </Box>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Box>
          <Typography variant="h6" gutterBottom>
            Live Market Data
          </Typography>
          {realTimeStocks.length > 0 ? (
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr' }, gap: 2 }}>
              {realTimeStocks.map((stock) => (
                <Paper key={stock.symbol} sx={{ p: 2, cursor: 'pointer' }} onClick={() => handleStockSelect(stock)}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="h6" component="div">
                      {stock.symbol}
                    </Typography>
                    <Typography variant="h5" component="div" color="primary">
                      ${stock.current_price.toFixed(2)}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {stock.name}
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography 
                      variant="body2" 
                      color={stock.day_change >= 0 ? 'success.main' : 'error.main'}
                    >
                      {stock.day_change >= 0 ? '+' : ''}{stock.day_change.toFixed(2)} ({stock.day_change_percent.toFixed(2)}%)
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Vol: {stock.volume.toLocaleString()}
                    </Typography>
                  </Box>
                  {stock.last_updated && (
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                      Updated: {stock.last_updated}
                    </Typography>
                  )}
                </Paper>
              ))}
            </Box>
          ) : (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <TrendingUp sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Waiting for Market Data
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {connectionStatus}
              </Typography>
            </Box>
          )}
        </Box>
      </TabPanel>
    </Box>
  );
}
