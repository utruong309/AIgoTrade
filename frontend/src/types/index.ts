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
    day_change_percent: number;
}
  
export interface Holding {
    id: string;
    stock: Stock;
    quantity: number;
    average_cost: number;
    total_cost: number;
    current_value: number;
    unrealized_gain_loss: number;
    unrealized_gain_loss_percent: number;
}
  
export interface Portfolio {
    id: string;
    name: string;
    total_value: number;
    cash_balance: number;
    invested_amount: number;
    total_return: number;
    total_return_percent: number;
    holdings: Holding[];
}