from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'stocks', views.StockViewSet)
router.register(r'portfolios', views.PortfolioViewSet, basename='portfolio') 
router.register(r'holdings', views.HoldingViewSet, basename='holding')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'market', views.MarketDataViewSet, basename='market')

urlpatterns = [
    path('', include(router.urls)),
    path('test/', views.test_websocket, name='test_websocket'),
    path('test-auth/', views.test_auth, name='test_auth'),
]