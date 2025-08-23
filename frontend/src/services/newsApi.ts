import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

export interface NewsArticle {
  id: number;
  title: string;
  description: string;
  url: string;
  source: string;
  publishedAt: string;
  cachedAt?: string;
}

export interface NewsResponse {
  status: string;
  data: {
    symbol: string;
    articles: NewsArticle[];
    count: number;
  };
}

export interface PortfolioNewsResponse {
  status: string;
  data: {
    news_by_symbol: { [symbol: string]: NewsArticle[] };
    symbols: string[];
    total_articles: number;
  };
}

export const newsAPI = {
  getNewsForSymbol: async (symbol: string, refresh = false): Promise<NewsResponse> => {
    const response = await api.get(`/news/${symbol}/`, {
      params: refresh ? { refresh: 'true' } : {}
    });
    return response.data;
  },

  getPortfolioNews: async (refresh = false): Promise<PortfolioNewsResponse> => {
    const response = await api.get('/portfolio/news/', {
      params: refresh ? { refresh: 'true' } : {}
    });
    return response.data;
  },

  cleanupNewsCache: async (days = 7) => {
    const response = await api.post('/news/cleanup/', { days });
    return response.data;
  }
};