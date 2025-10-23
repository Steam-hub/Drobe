"""
URL routing for audio_chat app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChatSessionViewSet,
    ScreenshotUploadView,
    ChatHistoryView,
    health_check,
    voice_agent_test
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'sessions', ChatSessionViewSet, basename='chat-session')

app_name = 'audio_chat'

urlpatterns = [
    # Health check
    path('health/', health_check, name='health-check'),

    # Test interface
    path('test/', voice_agent_test, name='voice-agent-test'),

    # ViewSet routes (includes list, create, retrieve, update, destroy)
    path('', include(router.urls)),

    # Custom endpoints
    path('screenshot/', ScreenshotUploadView.as_view(), name='screenshot-upload'),
    path('history/', ChatHistoryView.as_view(), name='chat-history'),
]
