import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginForm from './components/auth/LoginForm';
import RegisterForm from './components/auth/RegisterForm';
import PortfolioTable from './components/portfolio/PortfolioTable';
import MarketPage from './components/market/MarketPage';
import PredictionsPage from './pages/PredictionsPage';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Button, 
  Box,
  Tabs,
  Tab,
  Container
} from '@mui/material';
import { Dashboard, ShowChart, Psychology, AccountCircle } from '@mui/icons-material';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
  },
});

const AuthTabs: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Box sx={{ width: '100%' }}>
        <Tabs value={tabValue} onChange={handleTabChange} centered>
          <Tab label="Login" />
          <Tab label="Register" />
        </Tabs>
        <Box sx={{ mt: 2 }}>
          {tabValue === 0 && <LoginForm />}
          {tabValue === 1 && <RegisterForm />}
        </Box>
      </Box>
    </Container>
  );
};

const AppContent: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const [currentTab, setCurrentTab] = useState(0);

  if (!isAuthenticated) {
    return <AuthTabs />;
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const renderContent = () => {
    switch (currentTab) {
      case 0:
        return <PortfolioTable />;
      case 1:
        return <MarketPage />;
      case 2:
        return <PredictionsPage />;
      default:
        return <PortfolioTable />;
    }
  };

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            AIgoTrade
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Button 
              color="inherit" 
              startIcon={<AccountCircle />}
              onClick={() => {/* TODO: Add profile menu */}}
            >
              {user?.first_name || user?.username}
            </Button>
            <Button color="inherit" onClick={logout}>
              Logout
            </Button>
          </Box>
        </Toolbar>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Container maxWidth="xl">
            <Tabs 
              value={currentTab} 
              onChange={handleTabChange} 
              aria-label="main navigation"
              sx={{ minHeight: 48 }}
            >
              <Tab 
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Dashboard />
                    Portfolio
                  </Box>
                }
                iconPosition="start"
              />
              <Tab 
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ShowChart />
                    Market
                  </Box>
                }
                iconPosition="start"
              />
              <Tab 
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Psychology />
                    Predictions
                  </Box>
                }
                iconPosition="start"
              />
            </Tabs>
          </Container>
        </Box>
      </AppBar>
      
      <Box sx={{ py: 3 }}>
        {renderContent()}
      </Box>
    </Box>
  );
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;