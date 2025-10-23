from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CurriculumViewSet, LabelViewSet, TopicViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'curricula', CurriculumViewSet, basename='curriculum')
router.register(r'labels', LabelViewSet, basename='label')
router.register(r'topics', TopicViewSet, basename='topic')

urlpatterns = [
    path('', include(router.urls)),
]
