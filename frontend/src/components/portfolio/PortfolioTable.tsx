import React, { useState, useEffect } from 'react';
import {
  DataGrid,
  GridColDef
} from '@mui/x-data-grid';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  Button
} from '@mui/material';
import { Refresh } from '@mui/icons-material';
import { portfolioAPI } from '../../services/api';
import { Portfolio } from '../../types';

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

  const columns: GridColDef[] = [
    { field: 'symbol', headerName: 'Symbol', width: 100 },
    { field: 'name', headerName: 'Company', width: 200 },
    { 
      field: 'quantity', 
      headerName: 'Shares', 
      width: 100,
      type: 'number'
    },
    {
      field: 'average_cost',
      headerName: 'Avg Cost',
      width: 120,
      type: 'number',
      valueFormatter: (params: any) => {
        if (params.value === null || params.value === undefined) return '$0.00';
        return `$${Number(params.value).toFixed(2)}`;
      }
    },
    {
      field: 'current_value',
      headerName: 'Current Value',
      width: 140,
      type: 'number',
      valueFormatter: (params: any) => {
        if (params.value === null || params.value === undefined) return '$0.00';
        return `$${Number(params.value).toFixed(2)}`;
      }
    },
    {
      field: 'unrealized_gain_loss',
      headerName: 'Gain/Loss',
      width: 120,
      type: 'number',
      valueFormatter: (params: any) => {
        if (params.value === null || params.value === undefined) return '$0.00';
        return `$${Number(params.value).toFixed(2)}`;
      },
      cellClassName: (params: any) => 
        (params.value || 0) >= 0 ? 'profit' : 'loss'
    },
    {
      field: 'unrealized_gain_loss_percent',
      headerName: 'Gain/Loss %',
      width: 120,
      type: 'number',
      valueFormatter: (params: any) => {
        if (params.value === null || params.value === undefined) return '0.00%';
        return `${Number(params.value).toFixed(2)}%`;
      },
      cellClassName: (params: any) => 
        (params.value || 0) >= 0 ? 'profit' : 'loss'
    }
  ];

  const rows = portfolio?.holdings?.map((holding) => ({
    id: holding.id,
    symbol: holding.symbol || 'N/A',
    name: holding.name || 'Unknown',
    quantity: holding.quantity,
    average_cost: holding.average_cost,
    current_value: holding.market_value,
    unrealized_gain_loss: holding.gain_loss,
    unrealized_gain_loss_percent: holding.gain_loss_percent
  })) || [];

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
            <Typography 
              variant="h4" 
              component="div"
              color={(portfolio.total_gain_loss ? parseFloat(String(portfolio.total_gain_loss)) : 0) >= 0 ? 'success.main' : 'error.main'}
            >
              ${(portfolio.total_gain_loss ? parseFloat(String(portfolio.total_gain_loss)) : 0).toFixed(2)}
            </Typography>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Gain/Loss %
            </Typography>
            <Typography 
              variant="h4" 
              component="div"
              color={(portfolio.total_gain_loss_percent ? parseFloat(String(portfolio.total_gain_loss_percent)) : 0) >= 0 ? 'success.main' : 'error.main'}
            >
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
      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={rows}
          columns={columns}
          initialState={{
            pagination: {
              paginationModel: { page: 0, pageSize: 10 },
            },
          }}

          loading={loading}
          slots={{
            noRowsOverlay: () => (
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="h6" color="text.secondary">
                  No holdings in your portfolio
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Start trading to build your portfolio
                </Typography>
              </Box>
            )
          }}
        />
      </Paper>
    </Box>
  );
};

export default PortfolioTable;