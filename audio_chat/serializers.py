"""
Serializers for the audio_chat app
"""
from rest_framework import serializers
from .models import ChatSession, ChatMessage


class ChatSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for ChatSession model
    """
    class Meta:
        model = ChatSession
        fields = ['id', 'level_description', 'child_age', 'initial_message', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_child_age(self, value):
        """
        Validate that child age is between 4 and 10
        """
        if value < 4 or value > 10:
            raise serializers.ValidationError("Child age must be between 4 and 10 years old")
        return value


class ChatSessionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new chat session
    """
    class Meta:
        model = ChatSession
        fields = ['level_description', 'child_age', 'initial_message']

    def validate_child_age(self, value):
        """
        Validate that child age is between 4 and 10
        """
        if value < 4 or value > 10:
            raise serializers.ValidationError("Child age must be between 4 and 10 years old")
        return value


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for ChatMessage model
    """
    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'sender', 'message_type', 'text_content',
                  'audio_file', 'image_file', 'created_at']
        read_only_fields = ['id', 'created_at']


class ScreenshotUploadSerializer(serializers.Serializer):
    """
    Serializer for screenshot upload
    """
    session_id = serializers.UUIDField(required=True)
    image = serializers.ImageField(required=True)
    question = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_image(self, value):
        """
        Validate image file size and format
        """
        # Limit file size to 5MB
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Image file size must not exceed 5MB")

        # Check file extension
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        ext = value.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}"
            )

        return value


class ChatHistorySerializer(serializers.Serializer):
    """
    Serializer for retrieving chat history
    """
    session_id = serializers.UUIDField(required=True)
    limit = serializers.IntegerField(required=False, default=50, min_value=1, max_value=200)
