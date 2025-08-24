from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework.authtoken import views as token_views
from trading import views

def home(request):
    return JsonResponse({
        'message': 'AIgoTrade API is running!',
        'status': 'success',
        'websocket_endpoints': [
            '/ws/test/',
            '/ws/stocks/{symbol}/'
        ]
    })

urlpatterns = [
    path('', home, name='home'),  
    path('admin/', admin.site.urls),
    path('api/', include('trading.urls')),
    path('api/auth/', include('trading.auth_urls')),
    path('api-auth/', include('rest_framework.urls')), 
    path('api/token/', views.CustomObtainAuthToken.as_view()), 
    path('api/news/<str:symbol>/', include('trading.urls')),
    path('api/portfolio/news/', include('trading.urls')),
    path('api/news/cleanup/', include('trading.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)