from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/market/$', consumers.MarketDataConsumer.as_asgi()),
    re_path(r'ws/test/$', consumers.TestConsumer.as_asgi()),
]
