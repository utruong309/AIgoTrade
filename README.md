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
