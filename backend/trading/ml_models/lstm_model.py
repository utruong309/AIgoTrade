import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import logging
import os
from typing import Tuple, List, Dict, Optional
import pickle

logger = logging.getLogger(__name__)


class StockDataset(Dataset):
    """PyTorch Dataset for stock price data"""
    
    def __init__(self, data: np.ndarray, sequence_length: int = 60):
        """
        Initialize the dataset
        
        Args:
            data: Normalized stock data (OHLCV features)
            sequence_length: Number of time steps to use for prediction
        """
        self.data = data
        self.sequence_length = sequence_length
        
    def __len__(self):
        return len(self.data) - self.sequence_length
    
    def __getitem__(self, idx):
        """
        Get a sequence of data and the target value
        
        Returns:
            tuple: (sequence, target) where sequence is input features
                   and target is the next day's close price
        """
        sequence = self.data[idx:idx + self.sequence_length]
        target = self.data[idx + self.sequence_length, 3]  # Close price is at index 3
        
        return torch.FloatTensor(sequence), torch.FloatTensor([target])


class LSTMModel(nn.Module):
    """LSTM Neural Network for Stock Price Prediction"""
    
    def __init__(self, input_size: int = 5, hidden_size: int = 50, 
                 num_layers: int = 2, dropout: float = 0.2):
        """
        Initialize the LSTM model
        
        Args:
            input_size: Number of input features (OHLCV = 5)
            hidden_size: Number of LSTM units
            num_layers: Number of LSTM layers
            dropout: Dropout rate
        """
        super(LSTMModel, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True
        )
        
        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size, 25)
        self.fc2 = nn.Linear(25, 1)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # Activation
        self.relu = nn.ReLU()
        
    def forward(self, x):
        """
        Forward pass through the network
        
        Args:
            x: Input tensor of shape (batch_size, sequence_length, input_size)
            
        Returns:
            Predicted price tensor of shape (batch_size, 1)
        """
        # Initialize hidden state
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        
        # LSTM forward pass
        out, _ = self.lstm(x, (h0, c0))
        
        # Take the last output
        out = out[:, -1, :]
        
        # Fully connected layers
        out = self.dropout(out)
        out = self.relu(self.fc1(out))
        out = self.dropout(out)
        out = self.fc2(out)
        
        return out


class StockPricePredictor:
    """Main class for training and using the LSTM model"""
    
    def __init__(self, model_path: str = "models/", sequence_length: int = 60):
        """
        Initialize the predictor
        
        Args:
            model_path: Path to save/load models
            sequence_length: Number of time steps for prediction
        """
        self.model_path = model_path
        self.sequence_length = sequence_length
        self.scaler = MinMaxScaler()
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Create model directory if it doesn't exist
        os.makedirs(model_path, exist_ok=True)
        
    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare and normalize the data for training
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            tuple: (normalized_data, scaler_params)
        """
        # Select OHLCV columns
        features = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
        data = df[features].values
        
        # Normalize the data
        normalized_data = self.scaler.fit_transform(data)
        
        return normalized_data, self.scaler.scale_
    
    def create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM training
        
        Args:
            data: Normalized data
            
        Returns:
            tuple: (X, y) where X is input sequences and y is targets
        """
        X, y = [], []
        
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            y.append(data[i + self.sequence_length, 3])  # Close price
        
        return np.array(X), np.array(y)
    
    def train_model(self, df: pd.DataFrame, epochs: int = 100, 
                   batch_size: int = 32, learning_rate: float = 0.001) -> Dict:
        """
        Train the LSTM model
        
        Args:
            df: Training data DataFrame
            epochs: Number of training epochs
            batch_size: Batch size for training
            learning_rate: Learning rate for optimizer
            
        Returns:
            dict: Training metrics and history
        """
        logger.info(f"Starting model training with {len(df)} data points")
        
        # Prepare data
        normalized_data, scaler_params = self.prepare_data(df)
        
        # Create sequences
        X, y = self.create_sequences(normalized_data)
        
        # Split data into train and validation sets
        split_idx = int(0.8 * len(X))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Create datasets
        train_dataset = StockDataset(X_train, self.sequence_length)
        val_dataset = StockDataset(X_val, self.sequence_length)
        
        # Create data loaders
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        # Initialize model
        self.model = LSTMModel().to(self.device)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        
        # Training history
        train_losses = []
        val_losses = []
        
        logger.info(f"Training on device: {self.device}")
        
        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0
            
            for batch_X, batch_y in train_loader:
                batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            # Validation phase
            self.model.eval()
            val_loss = 0.0
            
            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                    outputs = self.model(batch_X)
                    loss = criterion(outputs, batch_y)
                    val_loss += loss.item()
            
            train_loss /= len(train_loader)
            val_loss /= len(val_loader)
            
            train_losses.append(train_loss)
            val_losses.append(val_loss)
            
            if epoch % 10 == 0:
                logger.info(f'Epoch [{epoch}/{epochs}], Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}')
        
        # Save model and scaler
        self.save_model()
        
        # Calculate final metrics
        train_predictions = self.predict_sequences(X_train)
        val_predictions = self.predict_sequences(X_val)
        
        train_rmse = np.sqrt(mean_squared_error(y_train, train_predictions))
        val_rmse = np.sqrt(mean_squared_error(y_val, val_predictions))
        train_mae = mean_absolute_error(y_train, train_predictions)
        val_mae = mean_absolute_error(y_val, val_predictions)
        
        metrics = {
            'train_losses': train_losses,
            'val_losses': val_losses,
            'train_rmse': train_rmse,
            'val_rmse': val_rmse,
            'train_mae': train_mae,
            'val_mae': val_mae,
            'scaler_params': scaler_params.tolist(),
            'sequence_length': self.sequence_length
        }
        
        logger.info(f"Training completed. Train RMSE: {train_rmse:.4f}, Val RMSE: {val_rmse:.4f}")
        
        return metrics
    
    def predict_sequences(self, X: np.ndarray) -> np.ndarray:
        """Predict for a batch of sequences"""
        self.model.eval()
        predictions = []
        
        with torch.no_grad():
            for i in range(0, len(X), 32):  # Process in batches
                batch = torch.FloatTensor(X[i:i+32]).to(self.device)
                batch_pred = self.model(batch)
                predictions.extend(batch_pred.cpu().numpy().flatten())
        
        return np.array(predictions)
    
    def predict_next_price(self, recent_data: pd.DataFrame) -> Dict:
        """
        Predict the next day's closing price
        
        Args:
            recent_data: Recent OHLCV data
            
        Returns:
            dict: Prediction results
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # Prepare the last sequence
        features = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
        data = recent_data[features].tail(self.sequence_length).values
        
        # Normalize using the fitted scaler
        normalized_data = self.scaler.transform(data)
        
        # Create input tensor
        input_tensor = torch.FloatTensor(normalized_data).unsqueeze(0).to(self.device)
        
        # Make prediction
        self.model.eval()
        with torch.no_grad():
            prediction = self.model(input_tensor)
        
        # Denormalize the prediction
        predicted_price = self.scaler.inverse_transform(
            np.zeros((1, 5))
        )[0, 3] * prediction.cpu().numpy()[0, 0]
        
        # Get current price for comparison
        current_price = recent_data['close_price'].iloc[-1]
        
        return {
            'predicted_price': float(predicted_price),
            'current_price': float(current_price),
            'price_change': float(predicted_price - current_price),
            'price_change_percent': float((predicted_price - current_price) / current_price * 100),
            'confidence': self._calculate_confidence(recent_data)
        }
    
    def _calculate_confidence(self, recent_data: pd.DataFrame) -> float:
        """
        Calculate prediction confidence based on recent volatility
        
        Args:
            recent_data: Recent price data
            
        Returns:
            float: Confidence score (0-1)
        """
        # Calculate recent volatility
        returns = recent_data['close_price'].pct_change().dropna()
        volatility = returns.std()
        
        # Lower volatility = higher confidence
        confidence = max(0.1, min(0.9, 1 - volatility * 10))
        
        return confidence
    
    def save_model(self):
        """Save the trained model and scaler"""
        if self.model is None:
            raise ValueError("No model to save")
        
        # Save PyTorch model
        model_file = os.path.join(self.model_path, 'lstm_model.pth')
        torch.save(self.model.state_dict(), model_file)
        
        # Save scaler
        scaler_file = os.path.join(self.model_path, 'scaler.pkl')
        with open(scaler_file, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        # Save metadata
        metadata = {
            'sequence_length': self.sequence_length,
            'model_architecture': {
                'input_size': 5,
                'hidden_size': 50,
                'num_layers': 2,
                'dropout': 0.2
            }
        }
        
        metadata_file = os.path.join(self.model_path, 'metadata.pkl')
        with open(metadata_file, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info(f"Model saved to {self.model_path}")
    
    def load_model(self, symbol: str):
        """
        Load a trained model for a specific symbol
        
        Args:
            symbol: Stock symbol
        """
        model_dir = os.path.join(self.model_path, symbol.lower())
        
        if not os.path.exists(model_dir):
            raise FileNotFoundError(f"No model found for {symbol}")
        
        # Load metadata
        metadata_file = os.path.join(model_dir, 'metadata.pkl')
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        
        self.sequence_length = metadata['sequence_length']
        
        # Initialize model with saved architecture
        arch = metadata['model_architecture']
        self.model = LSTMModel(
            input_size=arch['input_size'],
            hidden_size=arch['hidden_size'],
            num_layers=arch['num_layers'],
            dropout=arch['dropout']
        ).to(self.device)
        
        # Load model weights
        model_file = os.path.join(model_dir, 'lstm_model.pth')
        self.model.load_state_dict(torch.load(model_file, map_location=self.device))
        
        # Load scaler
        scaler_file = os.path.join(model_dir, 'scaler.pkl')
        with open(scaler_file, 'rb') as f:
            self.scaler = pickle.load(f)
        
        logger.info(f"Model loaded for {symbol}")
    
    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        if self.model is None:
            return {'status': 'No model loaded'}
        
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        return {
            'status': 'Model loaded',
            'device': str(self.device),
            'sequence_length': self.sequence_length,
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'model_architecture': {
                'input_size': 5,
                'hidden_size': 50,
                'num_layers': 2,
                'dropout': 0.2
            }
        }
