from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Curriculum, Label, Topic
from .serializers import (
    CurriculumSerializer,
    CurriculumListSerializer,
    CurriculumCreateUpdateSerializer,
    LabelSerializer,
    LabelCreateUpdateSerializer,
    TopicSerializer,
    TopicCreateUpdateSerializer
)


class CurriculumViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Curriculum model
    Provides list, retrieve, create, update, and delete operations
    """
    queryset = Curriculum.objects.filter(is_active=True).prefetch_related(
        'labels',
        'labels__topics'
    )
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['country', 'is_active']
    search_fields = ['title', 'description', 'country']
    ordering_fields = ['created_at', 'title', 'country']
    ordering = ['country', 'title']

    def get_serializer_class(self):
        """
        Use appropriate serializer based on action
        """
        if self.action == 'retrieve':
            return CurriculumSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CurriculumCreateUpdateSerializer
        return CurriculumListSerializer

    @action(detail=True, methods=['get'])
    def labels(self, request, pk=None):
        """
        Get all labels for a specific curriculum
        """
        curriculum = self.get_object()
        labels = curriculum.labels.prefetch_related('topics').all()
        serializer = LabelSerializer(labels, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def countries(self, request):
        """
        Get list of all countries with curricula
        """
        countries = Curriculum.objects.filter(is_active=True).values_list('country', flat=True).distinct()
        return Response({'countries': list(countries)})


class LabelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Label model
    """
    queryset = Label.objects.all().select_related('curriculum').prefetch_related('topics')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['curriculum']
    search_fields = ['title', 'curriculum__title']
    ordering_fields = ['order', 'created_at', 'title']
    ordering = ['curriculum', 'order', 'title']

    def get_serializer_class(self):
        """
        Use create/update serializer for write operations
        """
        if self.action in ['create', 'update', 'partial_update']:
            return LabelCreateUpdateSerializer
        return LabelSerializer

    @action(detail=True, methods=['get'])
    def topics(self, request, pk=None):
        """
        Get all topics for a specific label
        """
        label = self.get_object()
        topics = label.topics.filter(is_active=True).order_by('order')
        serializer = TopicSerializer(topics, many=True)
        return Response(serializer.data)


class TopicViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Topic model
    """
    queryset = Topic.objects.filter(is_active=True).select_related('label', 'label__curriculum')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['label', 'label__curriculum', 'is_active']
    search_fields = ['title', 'description', 'label__title']
    ordering_fields = ['order', 'created_at', 'title']
    ordering = ['label', 'order', 'title']

    def get_serializer_class(self):
        """
        Use create/update serializer for write operations
        """
        if self.action in ['create', 'update', 'partial_update']:
            return TopicCreateUpdateSerializer
        return TopicSerializer

    @action(detail=False, methods=['get'])
    def by_curriculum(self, request):
        """
        Get all topics grouped by curriculum
        """
        curriculum_id = request.query_params.get('curriculum_id')
        if not curriculum_id:
            return Response({'error': 'curriculum_id parameter is required'}, status=400)

        topics = self.queryset.filter(label__curriculum_id=curriculum_id)
        serializer = self.get_serializer(topics, many=True)
        return Response(serializer.data)
