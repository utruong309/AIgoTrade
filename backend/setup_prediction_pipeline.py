import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def run_command(command, cwd=None):
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_service_running(service_name, port):
    try:
        response = requests.get(f"http://localhost:{port}", timeout=5)
        return True
    except:
        return False

def install_dependencies():
    print("Installing Python dependencies...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    if requirements_file.exists():
        success, stdout, stderr = run_command(f"pip install -r {requirements_file}")
        if success:
            print("Python dependencies installed successfully")
            return True
        else:
            print(f"Failed to install Python dependencies: {stderr}")
            return False
    else:
        print("requirements.txt not found")
        return False

def check_database():
    print("Checking database...")
    
    success, stdout, stderr = run_command("python manage.py migrate")
    if success:
        print("Database migrations completed")
    else:
        print(f"Database migration failed: {stderr}")
        return False
    
    success, stdout, stderr = run_command("python manage.py shell -c \"from trading.models import Stock; print(f'Stocks: {Stock.objects.count()}')\"")
    if success:
        print(f"Database check: {stdout.strip()}")
        return True
    else:
        print(f"Database check failed: {stderr}")
        return False

def check_redis():
    print("Checking Redis...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("Redis is running and accessible")
        return True
    except Exception as e:
        print(f"Redis connection failed: {e}")
        print("Make sure Redis is running: redis-server")
        return False

def check_celery():
    print("Checking Celery...")
    
    success, stdout, stderr = run_command("ps aux | grep celery")
    if "celery worker" in stdout:
        print("Celery worker is running")
        return True
    else:
        print("Celery worker not found")
        print("Start Celery worker: celery -A aigo_trade worker --loglevel=info")
        return False

def check_django_server():
    print("Checking Django server...")
    
    if check_service_running("Django", 8000):
        print("Django server is running on port 8000")
        return True
    else:
        print("Django server not running on port 8000")
        print("Start Django server: python manage.py runserver")
        return False

def check_frontend():
    print("Checking React frontend...")
    
    if check_service_running("React", 3000):
        print("React frontend is running on port 3000")
        return True
    else:
        print("React frontend not running on port 3000")
        print("Start React frontend: cd frontend && npm start")
        return False

def populate_sample_data():
    print("Checking sample data...")
    
    success, stdout, stderr = run_command("python manage.py shell -c \"from trading.models import Stock; print(f'Stocks: {Stock.objects.count()}')\"")
    if success and "Stocks: 0" in stdout:
        print("Populating sample data...")
        success, stdout, stderr = run_command("python manage.py populate_sample_data")
        if success:
            print("Sample data populated successfully")
        else:
            print(f"Failed to populate sample data: {stderr}")
            return False
    else:
        print("Sample data already exists")
    
    return True

def main():
    print("LSTM Prediction Pipeline Setup")
    print("=" * 40)
    
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    checks = [
        ("Dependencies", install_dependencies),
        ("Database", check_database),
        ("Redis", check_redis),
        ("Sample Data", populate_sample_data),
        ("Celery", check_celery),
        ("Django Server", check_django_server),
        ("React Frontend", check_frontend),
    ]
    
    results = {}
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        results[check_name] = check_func()
    
    print("\nSetup Summary:")
    print("=" * 20)
    
    all_passed = True
    for check_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\nAll checks passed! You can now run the prediction pipeline tests.")
        print("\nTo run tests:")
        print("python test_prediction_pipeline.py")
    else:
        print("\nSome checks failed. Please fix the issues above before running tests.")
        print("\nCommon solutions:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start Redis: redis-server")
        print("3. Start Celery: celery -A aigo_trade worker --loglevel=info")
        print("4. Start Django: python manage.py runserver")
        print("5. Start React: cd frontend && npm start")

if __name__ == "__main__":
    main()