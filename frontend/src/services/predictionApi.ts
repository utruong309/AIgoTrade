import axios from 'axios';
import { PricePrediction, PredictionModel, PredictionSummary, MLTask } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

export const predictionApi = {
  // Get prediction for a specific stock
  getPrediction: async (symbol: string): Promise<PredictionSummary> => {
    const response = await api.get(`/predictions/predict/?symbol=${symbol}`);
    return response.data.data;
  },

  // Get prediction history for a stock
  getPredictionHistory: async (symbol: string, limit: number = 10): Promise<PricePrediction[]> => {
    const response = await api.get(`/predictions/history/?symbol=${symbol}&limit=${limit}`);
    return response.data.data;
  },

  // Get all available predictions
  getAvailablePredictions: async (limit: number = 20): Promise<PredictionSummary[]> => {
    const response = await api.get(`/predictions/available/?limit=${limit}`);
    return response.data.data;
  },

  // Get model performance for a stock
  getModelPerformance: async (symbol: string) => {
    const response = await api.get(`/predictions/performance/?symbol=${symbol}`);
    return response.data;
  },

  // Get active prediction models
  getActiveModels: async (): Promise<PredictionModel[]> => {
    const response = await api.get('/prediction-models/active_models/');
    return response.data.data;
  },

  // Get prediction models for a specific symbol
  getModelsBySymbol: async (symbol: string): Promise<PredictionModel[]> => {
    const response = await api.get(`/prediction-models/by_symbol/?symbol=${symbol}`);
    return response.data.data;
  },

  // Get data summary for a stock
  getDataSummary: async (symbol: string) => {
    const response = await api.get(`/data-preprocessing/data_summary/?symbol=${symbol}`);
    return response.data;
  },

  // ML Task Management
  trainModel: async (symbol: string, days: number = 365, epochs: number = 100): Promise<MLTask> => {
    const response = await api.post('/ml-tasks/train_model/', {
      symbol,
      days,
      epochs,
    });
    return response.data;
  },

  trainModelsBatch: async (symbols: string[], days: number = 365, epochs: number = 100): Promise<MLTask> => {
    const response = await api.post('/ml-tasks/train_models_batch/', {
      symbols,
      days,
      epochs,
    });
    return response.data;
  },

  updatePredictionsBatch: async (symbols: string[], useCache: boolean = true): Promise<MLTask> => {
    const response = await api.post('/ml-tasks/update_predictions_batch/', {
      symbols,
      use_cache: useCache,
    });
    return response.data;
  },

  cleanupCaches: async (): Promise<MLTask> => {
    const response = await api.post('/ml-tasks/cleanup_caches/');
    return response.data;
  },

  getTaskStatus: async (taskId: string) => {
    const response = await api.get(`/ml-tasks/task_status/?task_id=${taskId}`);
    return response.data;
  },

  // Cache Management
  invalidateCache: async (symbol: string) => {
    const response = await api.post('/predictions/invalidate_cache/', {
      symbol,
    });
    return response.data;
  },

  getCacheStats: async () => {
    const response = await api.get('/predictions/cache_stats/');
    return response.data;
  },

  cleanupCache: async () => {
    const response = await api.post('/predictions/cleanup_cache/');
    return response.data;
  },
};

export default predictionApi;
