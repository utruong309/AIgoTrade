import React, { useState } from 'react';
import {
  Box,
  Typography,
  Container,
  Tabs,
  Tab,
  Paper,
} from '@mui/material';
import {
  GridView,
  Assessment,
  Psychology,
} from '@mui/icons-material';
import PredictionGrid from '../components/predictions/PredictionGrid';
import PredictionDetail from '../components/predictions/PredictionDetail';

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
      id={`predictions-tabpanel-${index}`}
      aria-labelledby={`predictions-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const PredictionsPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleSymbolSelect = (symbol: string) => {
    setSelectedSymbol(symbol);
    setTabValue(1); //Switch to detail tab
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 3 }}>
        <Box mb={3}>
          <Typography variant="h3" component="h1" gutterBottom>
            AI Price Predictions
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Advanced LSTM neural network predictions for stock price movements
          </Typography>
        </Box>

        <Paper sx={{ mb: 3 }}>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange}
            variant="fullWidth"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab 
              icon={<GridView />} 
              label="All Predictions" 
              id="predictions-tab-0"
              aria-controls="predictions-tabpanel-0"
            />
            <Tab 
              icon={<Assessment />} 
              label="Stock Detail" 
              id="predictions-tab-1"
              aria-controls="predictions-tabpanel-1"
              disabled={!selectedSymbol}
            />
            <Tab 
              icon={<Psychology />} 
              label="Model Management" 
              id="predictions-tab-2"
              aria-controls="predictions-tabpanel-2"
            />
          </Tabs>
        </Paper>

        <TabPanel value={tabValue} index={0}>
          <PredictionGrid onSymbolSelect={handleSymbolSelect} />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {selectedSymbol ? (
            <PredictionDetail symbol={selectedSymbol} />
          ) : (
            <Box textAlign="center" py={4}>
              <Typography variant="h6" color="text.secondary">
                Select a stock from the predictions grid to view detailed analysis
              </Typography>
            </Box>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box textAlign="center" py={4}>
            <Typography variant="h6" color="text.secondary">
              Model Management features coming soon...
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Train new models, monitor performance, and manage prediction settings
            </Typography>
          </Box>
        </TabPanel>
      </Box>
    </Container>
  );
};

export default PredictionsPage;