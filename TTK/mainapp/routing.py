from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # Добавляем <session_id> в URL сокета!
    path('ws/stream/<int:session_id>/', consumers.StreamListener.as_asgi()), 
]