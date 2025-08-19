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
  CardContent
} from '@mui/material';
import { portfolioAPI } from '../../services/api';
import { Portfolio, Holding } from '../../types';

const PortfolioTable: React.FC = () => {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    try {
      const response = await portfolioAPI.getPortfolio();
      setPortfolio(response.data);
    } catch (error) {
      console.error('Failed to fetch portfolio:', error);
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
      valueFormatter: (value: number) => `$${value.toFixed(2)}`
    },
    {
      field: 'current_value',
      headerName: 'Current Value',
      width: 140,
      type: 'number',
      valueFormatter: (value: number) => `$${value.toFixed(2)}`
    },
    {
      field: 'unrealized_gain_loss',
      headerName: 'Gain/Loss',
      width: 120,
      type: 'number',
      valueFormatter: (value: number) => `$${value.toFixed(2)}`,
      cellClassName: (params) => 
        params.value >= 0 ? 'profit' : 'loss'
    },
    {
      field: 'unrealized_gain_loss_percent',
      headerName: 'Gain/Loss %',
      width: 120,
      type: 'number',
      valueFormatter: (value: number) => `${value.toFixed(2)}%`,
      cellClassName: (params) => 
        params.value >= 0 ? 'profit' : 'loss'
    }
  ];

  const rows = portfolio?.holdings.map((holding) => ({
    id: holding.id,
    symbol: holding.stock.symbol,
    name: holding.stock.name,
    quantity: holding.quantity,
    average_cost: holding.average_cost,
    current_value: holding.current_value,
    unrealized_gain_loss: holding.unrealized_gain_loss,
    unrealized_gain_loss_percent: holding.unrealized_gain_loss_percent
  })) || [];

  if (loading) return <Typography>Loading...</Typography>;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Portfolio Dashboard
      </Typography>
      
      {/* Portfolio Summary Cards */}
      <Box sx={{ 
        display: 'flex', 
        flexWrap: 'wrap', 
        gap: 3, 
        mb: 4 
      }}>
        <Card sx={{ minWidth: 200, flex: 1 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total Value
            </Typography>
            <Typography variant="h5">
              ${portfolio?.total_value.toFixed(2)}
            </Typography>
          </CardContent>
        </Card>
        
        <Card sx={{ minWidth: 200, flex: 1 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Cash Balance
            </Typography>
            <Typography variant="h5">
              ${portfolio?.cash_balance.toFixed(2)}
            </Typography>
          </CardContent>
        </Card>
        
        <Card sx={{ minWidth: 200, flex: 1 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total Return
            </Typography>
            <Typography 
              variant="h5" 
              color={portfolio && portfolio.total_return >= 0 ? 'success.main' : 'error.main'}
            >
              ${portfolio?.total_return.toFixed(2)}
            </Typography>
          </CardContent>
        </Card>
        
        <Card sx={{ minWidth: 200, flex: 1 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Return %
            </Typography>
            <Typography 
              variant="h5"
              color={portfolio && portfolio.total_return_percent >= 0 ? 'success.main' : 'error.main'}
            >
              {portfolio?.total_return_percent.toFixed(2)}%
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Holdings Table */}
      <Paper sx={{ height: 400, width: '100%' }}>
        <DataGrid
          rows={rows}
          columns={columns}
          pagination
          pageSizeOptions={[5, 10, 25]}
          initialState={{
            pagination: { paginationModel: { pageSize: 10 } }
          }}
          sx={{
            '& .profit': {
              color: 'success.main',
              fontWeight: 'bold'
            },
            '& .loss': {
              color: 'error.main',
              fontWeight: 'bold'
            }
          }}
        />
      </Paper>
    </Box>
  );
};

export default PortfolioTable;