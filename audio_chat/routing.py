"""
WebSocket URL routing for audio_chat app
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/audio-chat/(?P<session_id>[0-9a-f-]+)/$', consumers.AudioChatConsumer.as_asgi()),
]
