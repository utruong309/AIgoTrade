from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

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
    path('api-auth/', include('rest_framework.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)