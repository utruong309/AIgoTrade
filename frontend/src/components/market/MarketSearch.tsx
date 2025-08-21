import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  InputAdornment,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Paper,
  Typography,
  CircularProgress,
  Chip
} from '@mui/material';
import { Search, TrendingUp, TrendingDown } from '@mui/icons-material';
import { marketAPI } from '../../services/api';

interface Stock {
  symbol: string;
  name: string;
  current_price: number;
  day_change: number;
  day_change_percent: number;
  volume: number;
  last_updated: string;
}

interface MarketSearchProps {
  onStockSelect: (stock: Stock) => void;
}

const MarketSearch: React.FC<MarketSearchProps> = ({ onStockSelect }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [filteredStocks, setFilteredStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStocks();
  }, []);

  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredStocks(stocks);
    } else {
      // Add a small delay to avoid too many API calls while typing
      const timeoutId = setTimeout(() => {
        searchStocks(searchTerm);
      }, 300);

      return () => clearTimeout(timeoutId);
    }
  }, [searchTerm]);

  const fetchStocks = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await marketAPI.getStocks();
      setStocks(response.data.data || []);
    } catch (err) {
      setError('Failed to fetch stocks');
      console.error('Error fetching stocks:', err);
    } finally {
      setLoading(false);
    }
  };

  const searchStocks = async (query: string) => {
    if (!query.trim()) {
      setFilteredStocks(stocks);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      console.log('Searching for:', query);
      const response = await marketAPI.searchStocks(query);
      console.log('Search response:', response.data);
      
      if (response.data.status === 'success') {
        setFilteredStocks(response.data.data || []);
        console.log('Search results:', response.data.data);
      } else {
        setFilteredStocks([]);
        console.log('Search failed:', response.data);
      }
    } catch (err) {
      setError('Failed to search stocks');
      console.error('Error searching stocks:', err);
      setFilteredStocks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleStockSelect = (stock: Stock) => {
    onStockSelect(stock);
  };

  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`;
  };

  const formatChange = (change: number) => {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}`;
  };

  const formatChangePercent = (percent: number) => {
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${percent.toFixed(2)}%`;
  };

  const getChangeColor = (change: number) => {
    return change >= 0 ? 'success.main' : 'error.main';
  };

  return (
    <Box sx={{ width: '100%', maxWidth: 600 }}>
      <Typography variant="h6" gutterBottom>
        Market Search
      </Typography>
      
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Search stocks by symbol or company name..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Search />
            </InputAdornment>
          ),
        }}
        sx={{ mb: 2 }}
      />

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <Paper sx={{ maxHeight: 400, overflow: 'auto' }}>
        <List>
          {filteredStocks.map((stock) => (
            <ListItem key={stock.symbol} disablePadding>
              <ListItemButton onClick={() => handleStockSelect(stock)}>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1" fontWeight="bold">
                        {stock.symbol}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {stock.name}
                      </Typography>
                    </Box>
                  }
                  secondary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
                      <Typography variant="body2">
                        {formatPrice(stock.current_price)}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        {stock.day_change >= 0 ? (
                          <TrendingUp fontSize="small" color="success" />
                        ) : (
                          <TrendingDown fontSize="small" color="error" />
                        )}
                        <Typography
                          variant="body2"
                          color={getChangeColor(stock.day_change)}
                          fontWeight="bold"
                        >
                          {formatChange(stock.day_change)} ({formatChangePercent(stock.day_change_percent)})
                        </Typography>
                      </Box>
                      <Chip
                        label={`Vol: ${stock.volume.toLocaleString()}`}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                  }
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Paper>

      {filteredStocks.length === 0 && !loading && searchTerm.trim() !== '' && (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', p: 2 }}>
          No stocks found matching "{searchTerm}"
        </Typography>
      )}
    </Box>
  );
};

export default MarketSearch;
