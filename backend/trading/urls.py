from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'stocks', views.StockViewSet)
router.register(r'portfolios', views.PortfolioViewSet, basename='portfolio') # base name is just internal name
router.register(r'holdings', views.HoldingViewSet, basename='holding')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]