# AIgoTrade - Algorithmic Trading Platform

[![Django](https://img.shields.io/badge/Django-5.2.5-green.svg)](https://djangoproject.com/)
[![React](https://img.shields.io/badge/React-19.1.1-blue.svg)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-5.3.4-green.svg)](https://celeryproject.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docker.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-4.9.5-blue.svg)](https://typescriptlang.org/)
[![Material-UI](https://img.shields.io/badge/Material--UI-7.3.1-blue.svg)](https://mui.com/)

Advanced algorithmic trading platform with real-time market data, portfolio management, and comprehensive trading analytics. Built with Django REST Framework backend and React frontend, containerized with Docker. 

https://github.com/user-attachments/assets/d5547e6a-d95b-405a-b06f-d1f38485893a

## Main Features

### 1. **Real-Time Trading System** 
- **Live Market Data**: Real-time stock prices, volume, and market indicators via Twelvedata API
- **Portfolio Management**: Track holdings, calculate P&L, and manage multiple portfolios
- **Order Execution**: Buy/sell stocks with real-time pricing and transaction history
- **Risk Management**: User-defined risk tolerance and investment experience levels

### 2. **Advanced Analytics** 
- **Portfolio Performance**: Real-time portfolio valuation and performance metrics
- **Market Analysis**: Trending stocks, top performers, and sector analysis
- **Historical Data**: Comprehensive transaction history and performance tracking
- **Gain/Loss Calculations**: Detailed P&L analysis with percentage changes

### 3. **Market Data & News** 
- **Real-Time Market Data**: Live stock prices, volume, and market indicators via Twelvedata API
- **Portfolio Performance Tracking**: Comprehensive P&L analysis and performance metrics
- **Market Analysis Tools**: Stock screening, trending analysis, and sector performance
- **News Integration**: Financial news aggregation via NewsAPI with Redis caching

### 4. **User Experience**
- **Custom User Model**: Extended user profiles with investment preferences
- **Responsive Design**: Modern Material-UI interface for all devices
- **Real-Time Data**: Live market data updates via API polling (15-second intervals)
- **Multi-Platform Support**: Web-based platform accessible anywhere

## Technologies Used

### **Backend**
- **Framework**: Django 5.2.5 with Django REST Framework 3.14.0
- **Database**: PostgreSQL 15 with psycopg2-binary
- **Authentication**: Custom User model with Token-based authentication
- **Task Queue**: Celery 5.3.4 with Redis 5.0.1 as broker
- **Real-Time Data**: Live market data service with Twelvedata API integration
- **API**: RESTful API with comprehensive filtering and search capabilities

### **Frontend**
- **Framework**: React 19.1.1 with TypeScript 4.9.5
- **UI Library**: Material-UI 7.3.1 with comprehensive component library
- **Charts**: Recharts 3.1.2 for data visualization
- **HTTP Client**: Axios 1.11.0 for API communication
- **State Management**: React hooks and context for state management

### **Infrastructure**
- **Containerization**: Docker with multi-service orchestration
- **Database**: PostgreSQL with persistent volume storage
- **Caching**: Redis for session management and task queuing
- **Web Server**: Nginx for frontend serving and API proxying
- **Process Manager**: Gunicorn for Django application server
- **Background Services**: Celery workers for market data updates

## How to Run the Code

### Prerequisites
- Docker and Docker Compose
- Git
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)

### 1. **Clone the Repository**
```bash
git clone <your-repository-url>
cd AIgoTrade
```

### 2. **Environment Setup**
Create `.env.docker` file in the root directory:
```env
SECRET_KEY=your-secret-key-here
DEBUG=False
DB_NAME=aigo_trade_db
DB_USER=aigo_trade_user
DB_PASSWORD=aigo_trade_password
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
NEWS_API_KEY=your-newsapi-key
TWELVEDATA_API_KEY=your-twelvedata-api-key
```

### 3. **Start with Docker (Recommended)**
```bash
# Build and start all services
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 4. **Database Setup**
```bash
# Run database migrations
docker exec -it aigotrade-backend-1 python manage.py migrate

# Create superuser
docker exec -it aigotrade-backend-1 python manage.py createsuperuser
```

### 5. **Access the Application**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api-auth/

## Local Development

### **Backend Development**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up local environment
cp .env.example .env
# Edit .env with local database settings

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### **Frontend Development**
```bash
cd frontend
npm install

# Start development server
npm start
```

### **Database Setup - Local**
```bash
# Install PostgreSQL locally or use Docker
# Update .env with local database credentials
DB_HOST=localhost
DB_PORT=5432
```
## Docker Services 

### **Service Architecture**
- **db**: PostgreSQL 15 database with persistent storage
- **redis**: Redis 7 for caching and task queuing
- **backend**: Django application with Gunicorn
- **celery**: Asynchronous task worker for background jobs
- **frontend**: React application served by Nginx

### **Docker Commands**
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild specific service
docker-compose build backend --no-cache

# View logs
docker-compose logs -f [service-name]

# Execute commands in container
docker exec -it aigotrade-backend-1 python manage.py shell
```
## Deployment

### **Production Considerations**
- Set `DEBUG=False` in production
- Use strong `SECRET_KEY`
- Configure production database credentials
- Set up proper CORS origins
- Enable HTTPS with SSL certificates
- Configure production Redis and Celery settings

### **Environment Variables**
- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (False for production)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DB_*`: Database connection parameters
- `REDIS_URL`: Redis connection string
- `NEWS_API_KEY`: NewsAPI service key (newsapi.org)
- `TWELVEDATA_API_KEY`: Market data API key