import axios from 'axios';
import { AuthResponse, Portfolio } from '../types';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

export const authAPI = {
  register: (userData: any) => api.post<AuthResponse>('/auth/register/', userData),
  login: (email: string, password: string) => 
    api.post<AuthResponse>('/auth/login/', { email, password }),
  logout: () => api.post('/auth/logout/'),
  getProfile: () => api.get('/auth/profile/'),
};


// send GET to portfolios/portfolio

export const portfolioAPI = {
  getPortfolio: () => api.get<Portfolio>('/portfolios/portfolio/'), 
  getOrders: () => api.get('/portfolios/orders/'),
};

export default api;