import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Card, 
  CardContent, 
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { Refresh } from '@mui/icons-material';
import { portfolioAPI } from '../../services/api';
import { Portfolio } from '../../types';
import NewsFeed from '../news/NewsFeed';

const PortfolioTable: React.FC = () => {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  useEffect(() => {
    fetchPortfolio();
    const interval = setInterval(fetchPortfolio, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      const response = await portfolioAPI.getPortfolio();
      if (response.data && response.data.status === 'success' && response.data.data) {
        setPortfolio(response.data.data);
        setLastUpdate(new Date().toLocaleTimeString());
      } else if (response.data) {
        setPortfolio(response.data);
        setLastUpdate(new Date().toLocaleTimeString());
      } else {
        setPortfolio(null);
      }
    } catch (error) {
      console.error('Failed to fetch portfolio:', error);
      setPortfolio(null);
    }
    setLoading(false);
  };

  const rows = portfolio?.holdings || [];

  if (loading && !portfolio) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6">Loading portfolio...</Typography>
      </Box>
    );
  }

  if (!portfolio) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          No portfolio data available
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Portfolio Summary Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr 1fr' }, gap: 2, mb: 3 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Total Value
            </Typography>
            <Typography variant="h4" component="div">
              ${(portfolio.total_value ? parseFloat(String(portfolio.total_value)) : 0).toFixed(2)}
            </Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Cash Balance
            </Typography>
            <Typography variant="h4" component="div">
              ${(portfolio.cash_balance ? parseFloat(String(portfolio.cash_balance)) : 0).toFixed(2)}
            </Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Total Gain/Loss
            </Typography>
            <Typography variant="h4" component="div" color={(portfolio.total_gain_loss ? parseFloat(String(portfolio.total_gain_loss)) : 0) >= 0 ? 'success.main' : 'error.main'}>
              ${(portfolio.total_gain_loss ? parseFloat(String(portfolio.total_gain_loss)) : 0).toFixed(2)}
            </Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Gain/Loss %
            </Typography>
            <Typography variant="h4" component="div" color={(portfolio.total_gain_loss_percent ? parseFloat(String(portfolio.total_gain_loss_percent)) : 0) >= 0 ? 'success.main' : 'error.main'}>
              {(portfolio.total_gain_loss_percent ? parseFloat(String(portfolio.total_gain_loss_percent)) : 0).toFixed(2)}%
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Last Update Info */}
      {lastUpdate && (
        <Box sx={{ mb: 2, textAlign: 'right' }}>
          <Typography variant="caption" color="text.secondary">
            Last updated: {lastUpdate} (Auto-refreshes every 15 seconds)
          </Typography>
          <Button
            startIcon={<Refresh />}
            onClick={fetchPortfolio}
            size="small"
            sx={{ ml: 2 }}
          >
            Refresh Now
          </Button>
        </Box>
      )}

      {/* Holdings Table */}
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <TableContainer sx={{ maxHeight: 400 }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Symbol</TableCell>
                <TableCell>Company</TableCell>
                <TableCell align="right">Shares</TableCell>
                <TableCell align="right">Avg Cost</TableCell>
                <TableCell align="right">Stock Price</TableCell>
                <TableCell align="right">Current Value</TableCell>
                <TableCell align="right">Gain/Loss</TableCell>
                <TableCell align="right">Gain/Loss %</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>{row.symbol}</TableCell>
                  <TableCell>{row.name}</TableCell>
                  <TableCell align="right">{row.quantity}</TableCell>
                  <TableCell align="right">${row.average_cost?.toFixed(2) || '0.00'}</TableCell>
                  <TableCell align="right">${row.current_price?.toFixed(2) || '0.00'}</TableCell>
                  <TableCell align="right">${row.market_value?.toFixed(2) || '0.00'}</TableCell>
                  <TableCell align="right" sx={{ color: (row.gain_loss || 0) >= 0 ? 'success.main' : 'error.main' }}>
                    ${row.gain_loss?.toFixed(2) || '0.00'}
                  </TableCell>
                  <TableCell align="right" sx={{ color: (row.gain_loss_percent || 0) >= 0 ? 'success.main' : 'error.main' }}>
                    {row.gain_loss_percent?.toFixed(2) || '0.00'}%
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* News Feed */}
      <Box sx={{ mt: 3 }}>
        <NewsFeed />
      </Box>
    </Box>
  );
};

export default PortfolioTable;