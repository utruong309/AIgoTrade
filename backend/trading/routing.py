from django.urls import re_path
from . import consumers
from . import prediction_consumers

websocket_urlpatterns = [
    re_path(r'ws/market/$', consumers.MarketDataConsumer.as_asgi()),
    re_path(r'ws/test/$', consumers.TestConsumer.as_asgi()),
    re_path(r'ws/predictions/$', prediction_consumers.PredictionConsumer.as_asgi()),
    re_path(r'ws/model-training/$', prediction_consumers.ModelTrainingConsumer.as_asgi()),
]
