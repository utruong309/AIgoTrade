import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// WebSocket connection for real-time market data
export class MarketDataWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  private onMessageCallback: ((data: any) => void) | null = null;

  connect(onMessage: (data: any) => void) {
    this.onMessageCallback = onMessage;
    
    try {
      this.ws = new WebSocket(`${WS_BASE_URL}/ws/market/`);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected to live market data feed');
        this.reconnectAttempts = 0;
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (this.onMessageCallback) {
            this.onMessageCallback(data);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      this.ws.onclose = () => {
        console.log('WebSocket connection closed');
        this.scheduleReconnect();
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * this.reconnectAttempts;
      console.log(`Reconnecting in ${delay}ms... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        if (this.onMessageCallback) {
          this.connect(this.onMessageCallback);
        }
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  subscribeToSymbol(symbol: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe_symbol',
        symbol: symbol
      }));
    }
  }

  unsubscribeFromSymbol(symbol: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe_symbol',
        symbol: symbol
      }));
    }
  }

  getStockList() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'get_stocks'
      }));
    }
  }

  searchStocks(query: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'search_stocks',
        query: query
      }));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const marketDataWS = new MarketDataWebSocket();

export const authAPI = {
  login: (credentials: { email: string; password: string }) =>
    apiClient.post('/auth/login/', credentials),
  
  register: (userData: any) =>
    apiClient.post('/auth/register/', userData),
  
  logout: () =>
    apiClient.post('/auth/logout/'),
  
  getProfile: () =>
    apiClient.get('/users/me/'),
};

export const portfolioAPI = {
  getPortfolio: () =>
    apiClient.get('/portfolios/portfolio/'),
  
  getOrders: () =>
    apiClient.get('/portfolios/orders/'),
  
  buyStock: (data: { symbol: string; quantity: number; price?: number }) =>
    apiClient.post('/portfolios/buy/', data),
  
  sellStock: (data: { symbol: string; quantity: number; price?: number }) =>
    apiClient.post('/portfolios/sell/', data),
  
  getHolding: (symbol: string) =>
    apiClient.get(`/portfolios/holding/?symbol=${symbol}`),
};

export const marketAPI = {
  getStocks: () =>
    apiClient.get('/stocks/'),
  
  getStockDetail: (symbol: string) =>
    apiClient.get(`/stocks/by_symbol/?symbol=${symbol}`),
  
  getStockMarketData: (id: string, period: string = '1day') =>
    apiClient.get(`/stocks/${id}/market_data/?period=${period}`),
  
  getTrendingStocks: () =>
    apiClient.get('/stocks/trending/'),
  
  getTopStocks: () =>
    apiClient.get('/stocks/top_stocks/'),
  
  searchStocks: (query: string) =>
    apiClient.get(`/stocks/search/?q=${query}`),
  
  getMarketData: () =>
    apiClient.get('/market-data/'),
  
  getMarketDataDetail: (id: string) =>
    apiClient.get(`/market-data/${id}/`),
};

export const testAPI = {
  testAuth: () =>
    apiClient.get('/test-auth/'),
};