"""
Views for the audio_chat app
"""
import logging
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, render
from asgiref.sync import async_to_sync

from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionSerializer,
    ChatSessionCreateSerializer,
    ChatMessageSerializer,
    ScreenshotUploadSerializer,
    ChatHistorySerializer
)
from .services.gemini_live_service import GeminiLiveService

logger = logging.getLogger(__name__)


class ChatSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat sessions
    No authentication required as per requirements
    """
    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return ChatSessionCreateSerializer
        return ChatSessionSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new chat session with level description and child age
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create the session
        session = serializer.save()

        # Return the full session data
        response_serializer = ChatSessionSerializer(session)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        """
        List all active chat sessions
        """
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific chat session
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """
        End a chat session by marking it as inactive
        """
        session = self.get_object()
        session.is_active = False
        session.save()
        return Response({'message': 'Session ended successfully'}, status=status.HTTP_200_OK)


class ScreenshotUploadView(APIView):
    """
    API endpoint to upload screenshot for visual assistance
    No authentication required
    """

    def post(self, request):
        """
        Upload a screenshot and get AI assistance based on the image
        """
        serializer = ScreenshotUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        session_id = serializer.validated_data['session_id']
        image = serializer.validated_data['image']
        question = serializer.validated_data.get('question', '')

        # Get the session
        try:
            session = ChatSession.objects.get(id=session_id, is_active=True)
        except ChatSession.DoesNotExist:
            return Response(
                {'error': 'Session not found or inactive'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Save the screenshot message
        message = ChatMessage.objects.create(
            session=session,
            sender='child',
            message_type='image',
            image_file=image,
            text_content=question if question else 'Screenshot uploaded'
        )

        # Process the image with Gemini
        try:
            gemini_live_service = GeminiLiveService(
                session_id=str(session.id),
                level_description=session.level_description,
                child_age=session.child_age
            )

            # Read image data
            image.seek(0)
            image_data = image.read()

            # Get AI response
            result = async_to_sync(gemini_live_service.process_image_input)(
                image_data=image_data,
                question=question if question else None
            )

            if result['success']:
                # Save AI response
                response_message = ChatMessage.objects.create(
                    session=session,
                    sender='assistant',
                    message_type='text',
                    text_content=result['text']
                )

                return Response({
                    'message': 'Screenshot processed successfully',
                    'session_id': str(session.id),
                    'ai_response': result['text'],
                    'message_id': str(response_message.id)
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Failed to process screenshot',
                    'details': result.get('error', 'Unknown error')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Error processing screenshot: {str(e)}")
            return Response({
                'error': 'An error occurred while processing the screenshot',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatHistoryView(APIView):
    """
    API endpoint to retrieve chat history for a session
    No authentication required
    """

    def get(self, request):
        """
        Get chat history for a specific session
        Query params: session_id (required), limit (optional, default 50)
        """
        session_id = request.query_params.get('session_id')
        limit = int(request.query_params.get('limit', 50))

        if not session_id:
            return Response(
                {'error': 'session_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate limit
        if limit < 1 or limit > 200:
            limit = 50

        # Get the session
        try:
            session = ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get messages for the session
        messages = ChatMessage.objects.filter(session=session).order_by('created_at')[:limit]
        serializer = ChatMessageSerializer(messages, many=True)

        return Response({
            'session_id': str(session.id),
            'level_description': session.level_description,
            'child_age': session.child_age,
            'message_count': messages.count(),
            'messages': serializer.data
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
def health_check(request):
    """
    Simple health check endpoint
    """
    return Response({
        'status': 'healthy',
        'service': 'Audio Chat API'
    }, status=status.HTTP_200_OK)


def voice_agent_test(request):
    """
    Render the voice agent test interface
    """
    return render(request, 'voice_agent_test.html')
