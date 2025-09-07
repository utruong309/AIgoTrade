import os
import sys
import django
import asyncio
import requests
import json
import time
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aigo_trade.settings')
django.setup()

from django.utils import timezone
from django.db import transaction
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator

from trading.models import Stock, MarketData, PredictionModel, PricePrediction
from trading.data_preprocessing import DataPreprocessingService
from trading.prediction_service import PredictionService
from trading.ml_tasks import train_lstm_model, make_prediction_task, update_predictions_batch
from trading.prediction_consumers import PredictionConsumer
from trading.cache_services.prediction_cache import prediction_cache_service


class PredictionPipelineTester:
    
    def __init__(self, base_url="http://localhost:8000/api"):
        self.base_url = base_url
        self.data_service = DataPreprocessingService()
        self.prediction_service = PredictionService()
        self.test_symbol = "AAPL"
        self.test_results = {}
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        status = "PASS" if success else "FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results[test_name] = {"success": success, "message": message}
    
    def test_data_preprocessing(self):
        print("\nTesting Data Preprocessing...")
        
        try:
            summary = self.data_service.get_data_summary(self.test_symbol)
            if summary.get('status') == 'available':
                self.log_test("Data Summary", True, f"Found {summary['total_records']} records")
            else:
                self.log_test("Data Summary", False, summary.get('message', 'No data available'))
                return False
            
            training_data = self.data_service.prepare_training_data(self.test_symbol, days=90)
            if training_data:
                self.log_test("Training Data Preparation", True, 
                            f"Prepared {len(training_data['data'])} records with {len(training_data['metadata']['feature_columns'])} features")
            else:
                self.log_test("Training Data Preparation", False, "Failed to prepare training data")
                return False
            
            prediction_data = self.data_service.prepare_prediction_data(self.test_symbol)
            if prediction_data:
                self.log_test("Prediction Data Preparation", True, 
                            f"Prepared {len(prediction_data['data'])} records for prediction")
            else:
                self.log_test("Prediction Data Preparation", False, "Failed to prepare prediction data")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Data Preprocessing", False, str(e))
            return False
    
    def test_model_training(self):
        print("\nTesting Model Training...")
        
        try:
            stock = Stock.objects.filter(symbol=self.test_symbol).first()
            if not stock:
                self.log_test("Stock Exists", False, f"Stock {self.test_symbol} not found")
                return False
            
            self.log_test("Stock Exists", True, f"Found {self.test_symbol}")
            
            task_result = train_lstm_model.delay(self.test_symbol, days=90, epochs=10)
            
            timeout = 300
            start_time = time.time()
            
            while not task_result.ready() and (time.time() - start_time) < timeout:
                time.sleep(5)
                print(f"Training in progress... ({task_result.status})")
            
            if task_result.ready():
                result = task_result.result
                if result.get('status') == 'success':
                    self.log_test("Model Training", True, 
                                f"Trained model with RMSE: {result['metrics']['val_rmse']:.4f}")
                    
                    model = PredictionModel.objects.filter(
                        stock=stock, 
                        model_type='lstm',
                        status='trained'
                    ).first()
                    
                    if model:
                        self.log_test("Model Database Storage", True, f"Model saved with ID: {model.id}")
                    else:
                        self.log_test("Model Database Storage", False, "Model not found in database")
                    
                    return True
                else:
                    self.log_test("Model Training", False, result.get('error', 'Training failed'))
                    return False
            else:
                self.log_test("Model Training", False, "Training timed out")
                return False
                
        except Exception as e:
            self.log_test("Model Training", False, str(e))
            return False
    
    def test_prediction_generation(self):
        print("\nTesting Prediction Generation...")
        
        try:
            result = self.prediction_service.make_prediction(self.test_symbol)
            
            if result['status'] == 'success':
                prediction_data = result['data']
                self.log_test("Prediction Generation", True, 
                            f"Predicted: ${prediction_data['predicted_price']:.2f}, "
                            f"Current: ${prediction_data['current_price']:.2f}, "
                            f"Confidence: {prediction_data['confidence_level']}")
                
                prediction = PricePrediction.objects.filter(
                    stock__symbol=self.test_symbol,
                    prediction_date__gte=timezone.now().date()
                ).first()
                
                if prediction:
                    self.log_test("Prediction Database Storage", True, f"Prediction saved with ID: {prediction.id}")
                else:
                    self.log_test("Prediction Database Storage", False, "Prediction not found in database")
                
                return True
            else:
                self.log_test("Prediction Generation", False, result.get('message', 'Prediction failed'))
                return False
                
        except Exception as e:
            self.log_test("Prediction Generation", False, str(e))
            return False
    
    def test_api_endpoints(self):
        print("\nTesting API Endpoints...")
        
        try:
            response = requests.get(f"{self.base_url}/predictions/predict/?symbol={self.test_symbol}")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    self.log_test("Prediction API", True, "API endpoint working")
                else:
                    self.log_test("Prediction API", False, data.get('message', 'API error'))
            else:
                self.log_test("Prediction API", False, f"HTTP {response.status_code}")
            
            response = requests.get(f"{self.base_url}/predictions/available/")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    count = len(data.get('data', []))
                    self.log_test("Available Predictions API", True, f"Found {count} predictions")
                else:
                    self.log_test("Available Predictions API", False, data.get('message', 'API error'))
            else:
                self.log_test("Available Predictions API", False, f"HTTP {response.status_code}")
            
            response = requests.get(f"{self.base_url}/prediction-models/active_models/")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    count = len(data.get('data', []))
                    self.log_test("Active Models API", True, f"Found {count} active models")
                else:
                    self.log_test("Active Models API", False, data.get('message', 'API error'))
            else:
                self.log_test("Active Models API", False, f"HTTP {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("API Endpoints", False, str(e))
            return False
    
    def test_caching(self):
        print("\nTesting Caching...")
        
        try:
            if prediction_cache_service.is_redis_available():
                self.log_test("Redis Connection", True, "Redis is available")
                
                test_data = {
                    'symbol': self.test_symbol,
                    'predicted_price': 150.0,
                    'current_price': 145.0,
                    'confidence_score': 0.8,
                    'confidence_level': 'high'
                }
                
                cache_success = prediction_cache_service.cache_prediction(self.test_symbol, test_data)
                if cache_success:
                    self.log_test("Cache Write", True, "Successfully cached prediction")
                    
                    cached_data = prediction_cache_service.get_cached_prediction(self.test_symbol)
                    if cached_data:
                        self.log_test("Cache Read", True, "Successfully retrieved cached prediction")
                    else:
                        self.log_test("Cache Read", False, "Failed to retrieve cached prediction")
                else:
                    self.log_test("Cache Write", False, "Failed to cache prediction")
                
            else:
                self.log_test("Redis Connection", False, "Redis is not available")
            
            return True
            
        except Exception as e:
            self.log_test("Caching", False, str(e))
            return False
    
    async def test_websocket(self):
        print("\nTesting WebSocket...")
        
        try:
            communicator = WebsocketCommunicator(PredictionConsumer.as_asgi(), "/ws/predictions/")
            connected, subprotocol = await communicator.connect()
            
            if connected:
                self.log_test("WebSocket Connection", True, "Successfully connected to WebSocket")
                
                await communicator.send_json_to({
                    "type": "subscribe_symbol",
                    "symbol": self.test_symbol
                })
                
                response = await communicator.receive_json_from()
                if response.get('type') == 'subscription_confirmed':
                    self.log_test("WebSocket Subscription", True, f"Subscribed to {self.test_symbol}")
                else:
                    self.log_test("WebSocket Subscription", False, "Subscription failed")
                
                await communicator.disconnect()
            else:
                self.log_test("WebSocket Connection", False, "Failed to connect to WebSocket")
            
            return True
            
        except Exception as e:
            self.log_test("WebSocket", False, str(e))
            return False
    
    def test_celery_tasks(self):
        print("\nTesting Celery Tasks...")
        
        try:
            task = make_prediction_task.delay(self.test_symbol)
            
            timeout = 60
            start_time = time.time()
            
            while not task.ready() and (time.time() - start_time) < timeout:
                time.sleep(2)
            
            if task.ready():
                result = task.result
                if result.get('status') == 'success':
                    self.log_test("Celery Prediction Task", True, "Task completed successfully")
                else:
                    self.log_test("Celery Prediction Task", False, result.get('message', 'Task failed'))
            else:
                self.log_test("Celery Prediction Task", False, "Task timed out")
            
            task = update_predictions_batch.delay([self.test_symbol])
            
            start_time = time.time()
            while not task.ready() and (time.time() - start_time) < timeout:
                time.sleep(2)
            
            if task.ready():
                result = task.result
                if result.get('status') == 'completed':
                    self.log_test("Celery Batch Task", True, f"Batch task completed: {result.get('successful', 0)} successful")
                else:
                    self.log_test("Celery Batch Task", False, result.get('error', 'Batch task failed'))
            else:
                self.log_test("Celery Batch Task", False, "Batch task timed out")
            
            return True
            
        except Exception as e:
            self.log_test("Celery Tasks", False, str(e))
            return False
    
    def test_performance(self):
        print("\nTesting Performance...")
        
        try:
            start_time = time.time()
            result = self.prediction_service.make_prediction(self.test_symbol, use_cache=True)
            cache_time = time.time() - start_time
            
            if result['status'] == 'success':
                self.log_test("Cached Prediction Speed", True, f"Completed in {cache_time:.3f}s")
            
            start_time = time.time()
            result = self.prediction_service.make_prediction(self.test_symbol, use_cache=False)
            no_cache_time = time.time() - start_time
            
            if result['status'] == 'success':
                self.log_test("Non-Cached Prediction Speed", True, f"Completed in {no_cache_time:.3f}s")
            
            if cache_time < no_cache_time:
                speedup = no_cache_time / cache_time
                self.log_test("Cache Performance", True, f"Cache provides {speedup:.1f}x speedup")
            else:
                self.log_test("Cache Performance", False, "Cache not providing speedup")
            
            return True
            
        except Exception as e:
            self.log_test("Performance", False, str(e))
            return False
    
    def generate_report(self):
        print("\nTest Report")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅" if result['success'] else "❌"
            print(f"{status} {test_name}: {result['message']}")
        
        if failed_tests == 0:
            print("\nAll tests passed! The prediction pipeline is working correctly.")
        else:
            print(f"\n{failed_tests} tests failed. Please review the issues above.")
    
    async def run_all_tests(self):
        print("Starting LSTM Prediction Pipeline Tests")
        print("=" * 50)
        
        self.test_data_preprocessing()
        self.test_model_training()
        self.test_prediction_generation()
        self.test_api_endpoints()
        self.test_caching()
        await self.test_websocket()
        self.test_celery_tasks()
        self.test_performance()
        
        self.generate_report()


async def main():
    tester = PredictionPipelineTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
