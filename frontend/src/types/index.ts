export interface User {
    id: string;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    risk_tolerance: string;
    investment_experience: string;
}
  
export interface AuthResponse {
    success: boolean;
    user: User;
    token: string;
    message?: string;
}
  
export interface Stock {
    id: string;
    symbol: string;
    name: string;
    current_price: number;
    day_change: number;
    day_change_percent: number;
    volume: number;
}
  
export interface Holding {
    id: string;
    symbol: string;
    name: string;
    quantity: number;
    average_cost: number;
    total_cost: number;
    current_price: number;
    market_value: number;
    cost_basis: number;
    gain_loss: number;
    gain_loss_percent: number;
    day_change: number;
    day_change_percent: number;
}
  
export interface Portfolio {
    portfolio_id: string;
    portfolio_name: string;
    total_value: number;
    cash_balance: number;
    total_cost: number;
    total_gain_loss: number;
    total_gain_loss_percent: number;
    holdings: Holding[];
    holdings_count: number;
    last_updated: string;
}

export interface PricePrediction {
    id: string;
    symbol: string;
    name: string;
    predicted_price: number;
    current_price: number;
    price_change: number;
    price_change_percent: number;
    confidence_score: number;
    confidence_level: 'low' | 'medium' | 'high';
    prediction_date: string;
    prediction_timestamp: string;
    model_type: string;
    is_future_prediction: boolean;
    actual_price?: number;
    prediction_accuracy?: number;
}

export interface PredictionModel {
    id: string;
    stock_symbol: string;
    stock_name: string;
    model_type: string;
    status: 'training' | 'trained' | 'failed' | 'outdated';
    sequence_length: number;
    training_data_points: number;
    train_rmse?: number;
    val_rmse?: number;
    train_mae?: number;
    val_mae?: number;
    is_active: boolean;
    training_duration_days: number;
    created_at: string;
    updated_at: string;
    last_prediction_at?: string;
}

export interface MLTask {
    task_id: string;
    status: string;
    symbol?: string;
    symbols?: string[];
    message: string;
    started_at?: string;
    completed_at?: string;
    error?: string;
}

export interface PredictionSummary {
    symbol: string;
    name: string;
    current_price: number;
    predicted_price: number;
    price_change: number;
    price_change_percent: number;
    confidence_score: number;
    confidence_level: string;
    prediction_date: string;
    prediction_timestamp: string;
    model_type: string;
    is_future_prediction: boolean;
}