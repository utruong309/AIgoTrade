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