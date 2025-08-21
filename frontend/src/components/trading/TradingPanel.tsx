import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Alert,
  Snackbar,
  CircularProgress,
  Divider,
  Chip
} from '@mui/material';
import { Add, Remove, TrendingUp, TrendingDown } from '@mui/icons-material';
import { portfolioAPI } from '../../services/api';

interface Stock {
  symbol: string;
  name: string;
  current_price: number;
  day_change: number;
  day_change_percent: number;
}

interface TradingPanelProps {
  selectedStock: Stock | null;
  onTradeExecuted: () => void;
}

interface TradeForm {
  quantity: string;
  price: string;
}

export default function TradingPanel({ selectedStock, onTradeExecuted }: TradingPanelProps) {
  const [tradeType, setTradeType] = useState<'buy' | 'sell'>('buy');
  const [formData, setFormData] = useState<TradeForm>({
    quantity: '',
    price: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showMessage, setShowMessage] = useState(false);

  useEffect(() => {
    if (selectedStock) {
      setFormData(prev => ({
        ...prev,
        price: selectedStock.current_price.toString()
      }));
    }
  }, [selectedStock]);

  const handleInputChange = (field: keyof TradeForm) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const calculateTotal = () => {
    const quantity = parseFloat(formData.quantity) || 0;
    const price = parseFloat(formData.price) || 0;
    return quantity * price;
  };

  const validateForm = () => {
    if (!selectedStock) {
      setMessage({ type: 'error', text: 'Please select a stock first' });
      setShowMessage(true);
      return false;
    }

    if (!formData.quantity || parseFloat(formData.quantity) <= 0) {
      setMessage({ type: 'error', text: 'Please enter a valid quantity' });
      setShowMessage(true);
      return false;
    }

    if (!formData.price || parseFloat(formData.price) <= 0) {
      setMessage({ type: 'error', text: 'Please enter a valid price' });
      setShowMessage(true);
      return false;
    }

    return true;
  };

  const executeTrade = async () => {
    if (!validateForm()) return;

    setLoading(true);
    try {
      const tradeData = {
        symbol: selectedStock!.symbol,
        quantity: parseFloat(formData.quantity),
        price: parseFloat(formData.price)
      };

      const response = tradeType === 'buy' 
        ? await portfolioAPI.buyStock(tradeData)
        : await portfolioAPI.sellStock(tradeData);

      if (response.data.status === 'success') {
        setMessage({ 
          type: 'success', 
          text: `${tradeType.toUpperCase()} order executed successfully!` 
        });
        setShowMessage(true);
        
        // Reset form
        setFormData({ quantity: '', price: selectedStock!.current_price.toString() });
        
        // Notify parent component
        onTradeExecuted();
      } else {
        setMessage({ 
          type: 'error', 
          text: response.data.message || 'Trade execution failed' 
        });
        setShowMessage(true);
      }
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.message || 'Trade execution failed' 
      });
      setShowMessage(true);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseMessage = () => {
    setShowMessage(false);
  };

  if (!selectedStock) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Select a Stock
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Choose a stock from the market to start trading
        </Typography>
      </Paper>
    );
  }

  const total = calculateTotal();
  const isPositiveChange = selectedStock.day_change >= 0;

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Trade {selectedStock.symbol}
      </Typography>
      
      <Typography variant="body2" color="text.secondary" gutterBottom>
        {selectedStock.name}
      </Typography>

      {/* Stock Price Display */}
      <Box sx={{ mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="h4" component="div">
            ${selectedStock.current_price.toFixed(2)}
          </Typography>
          <Chip
            icon={isPositiveChange ? <TrendingUp /> : <TrendingDown />}
            label={`${isPositiveChange ? '+' : ''}${selectedStock.day_change.toFixed(2)} (${selectedStock.day_change_percent.toFixed(2)}%)`}
            color={isPositiveChange ? 'success' : 'error'}
            variant="outlined"
          />
        </Box>
      </Box>

      {/* Trade Type Selection */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={1}>
          <Grid item xs={6}>
            <Button
              fullWidth
              variant={tradeType === 'buy' ? 'contained' : 'outlined'}
              color="success"
              startIcon={<Add />}
              onClick={() => setTradeType('buy')}
            >
              Buy
            </Button>
          </Grid>
          <Grid item xs={6}>
            <Button
              fullWidth
              variant={tradeType === 'sell' ? 'contained' : 'outlined'}
              color="error"
              startIcon={<Remove />}
              onClick={() => setTradeType('sell')}
            >
              Sell
            </Button>
          </Grid>
        </Grid>
      </Box>

      <Divider sx={{ my: 2 }} />

      {/* Trade Form */}
      <Box component="form" sx={{ mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <TextField
              fullWidth
              label="Quantity"
              type="number"
              value={formData.quantity}
              onChange={handleInputChange('quantity')}
              inputProps={{ min: 0, step: 1 }}
              disabled={loading}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              fullWidth
              label="Price per Share"
              type="number"
              value={formData.price}
              onChange={handleInputChange('price')}
              inputProps={{ min: 0, step: 0.01 }}
              disabled={loading}
            />
          </Grid>
        </Grid>

        {/* Total Calculation */}
        {total > 0 && (
          <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Total {tradeType === 'buy' ? 'Cost' : 'Proceeds'}:
            </Typography>
            <Typography variant="h6" color="primary">
              ${total.toFixed(2)}
            </Typography>
          </Box>
        )}
      </Box>

      {/* Execute Trade Button */}
      <Button
        fullWidth
        variant="contained"
        color={tradeType === 'buy' ? 'success' : 'error'}
        size="large"
        onClick={executeTrade}
        disabled={loading || !formData.quantity || !formData.price}
        startIcon={loading ? <CircularProgress size={20} /> : (tradeType === 'buy' ? <Add /> : <Remove />)}
      >
        {loading ? 'Executing...' : `${tradeType.toUpperCase()} ${selectedStock.symbol}`}
      </Button>

      {/* Message Snackbar */}
      <Snackbar
        open={showMessage}
        autoHideDuration={6000}
        onClose={handleCloseMessage}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseMessage}
          severity={message?.type || 'info'}
          sx={{ width: '100%' }}
        >
          {message?.text}
        </Alert>
      </Snackbar>
    </Paper>
  );
}
