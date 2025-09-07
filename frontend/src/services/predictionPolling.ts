import { useEffect, useRef, useState } from 'react';
import predictionApi from './predictionApi';

interface PredictionUpdate {
  symbol: string;
  predicted_price: number;
  current_price: number;
  price_change: number;
  price_change_percent: number;
  confidence_score: number;
  confidence_level: string;
  prediction_timestamp: string;
}

class PredictionPollingService {
  private intervalId: NodeJS.Timeout | null = null;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private isPolling = false;
  private pollInterval = 10000; // 10 seconds default


  startPolling(interval: number = 10000): void {
    if (this.isPolling) {
      this.stopPolling();
    }
    
    this.pollInterval = interval;
    this.isPolling = true;
    
    // Initial fetch
    this.fetchPredictions();
    
    // Set up interval
    this.intervalId = setInterval(() => {
      this.fetchPredictions();
    }, this.pollInterval);
    
    this.emit('polling_started', { interval: this.pollInterval });
  }

  stopPolling(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.isPolling = false;
    this.emit('polling_stopped', {});
  }

  private async fetchPredictions(): Promise<void> {
    try {
      const predictions = await predictionApi.getAvailablePredictions(50);
      this.emit('predictions_updated', predictions);
      this.emit('polling_success', { timestamp: new Date() });
    } catch (error) {
      console.error('Error fetching predictions:', error);
      this.emit('polling_error', error);
    }
  }

  private emit(event: string, data: any): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach(listener => {
        try {
          listener(data);
        } catch (error) {
          console.error('Error in event listener:', error);
        }
      });
    }
  }

  on(event: string, listener: (data: any) => void): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(listener);
  }

  off(event: string, listener: (data: any) => void): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.delete(listener);
    }
  }

  isActive(): boolean {
    return this.isPolling;
  }

  getPollInterval(): number {
    return this.pollInterval;
  }
}

// Global polling service instance
export const predictionPollingService = new PredictionPollingService();

// React hook for prediction polling
export const usePredictionPolling = (interval: number = 10000, autoStart: boolean = true) => {
  const [isActive, setIsActive] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollingRef = useRef<PredictionPollingService | null>(null);

  useEffect(() => {
    pollingRef.current = predictionPollingService;
    
    const handlePollingStarted = () => setIsActive(true);
    const handlePollingStopped = () => setIsActive(false);
    const handlePollingSuccess = () => {
      setLastUpdate(new Date());
      setError(null);
    };
    const handlePollingError = (err: any) => {
      setError(err.message || 'Polling error');
    };

    pollingRef.current.on('polling_started', handlePollingStarted);
    pollingRef.current.on('polling_stopped', handlePollingStopped);
    pollingRef.current.on('polling_success', handlePollingSuccess);
    pollingRef.current.on('polling_error', handlePollingError);

    // Start polling if autoStart is true
    if (autoStart && !pollingRef.current.isActive()) {
      pollingRef.current.startPolling(interval);
    }

    return () => {
      if (pollingRef.current) {
        pollingRef.current.off('polling_started', handlePollingStarted);
        pollingRef.current.off('polling_stopped', handlePollingStopped);
        pollingRef.current.off('polling_success', handlePollingSuccess);
        pollingRef.current.off('polling_error', handlePollingError);
      }
    };
  }, [interval, autoStart]);

  const startPolling = () => {
    if (pollingRef.current) {
      pollingRef.current.startPolling(interval);
    }
  };

  const stopPolling = () => {
    if (pollingRef.current) {
      pollingRef.current.stopPolling();
    }
  };

  return {
    isActive,
    lastUpdate,
    error,
    startPolling,
    stopPolling,
    pollingService: pollingRef.current,
  };
};

// Hook for listening to prediction updates
export const usePredictionUpdates = (symbol?: string) => {
  const [updates, setUpdates] = useState<PredictionUpdate[]>([]);
  const pollingRef = useRef<PredictionPollingService | null>(null);

  useEffect(() => {
    pollingRef.current = predictionPollingService;

    const handlePredictionsUpdated = (predictions: any[]) => {
      if (!symbol) {
        // Update all predictions
        setUpdates(prev => {
          const newUpdates = predictions.map(p => ({
            symbol: p.symbol,
            predicted_price: p.predicted_price,
            current_price: p.current_price,
            price_change: p.price_change,
            price_change_percent: p.price_change_percent,
            confidence_score: p.confidence_score,
            confidence_level: p.confidence_level,
            prediction_timestamp: p.prediction_timestamp,
          }));
          return [...newUpdates, ...prev].slice(0, 10); // Keep last 10 updates
        });
      } else {
        // Update only specific symbol
        const relevantPrediction = predictions.find(p => p.symbol === symbol);
        if (relevantPrediction) {
          const update = {
            symbol: relevantPrediction.symbol,
            predicted_price: relevantPrediction.predicted_price,
            current_price: relevantPrediction.current_price,
            price_change: relevantPrediction.price_change,
            price_change_percent: relevantPrediction.price_change_percent,
            confidence_score: relevantPrediction.confidence_score,
            confidence_level: relevantPrediction.confidence_level,
            prediction_timestamp: relevantPrediction.prediction_timestamp,
          };
          setUpdates(prev => [update, ...prev].slice(0, 10));
        }
      }
    };

    pollingRef.current.on('predictions_updated', handlePredictionsUpdated);

    return () => {
      if (pollingRef.current) {
        pollingRef.current.off('predictions_updated', handlePredictionsUpdated);
      }
    };
  }, [symbol]);

  return updates;
};

export default predictionPollingService;
