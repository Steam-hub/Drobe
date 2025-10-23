from rest_framework import serializers
from .models import Curriculum, Label, Topic


class TopicSerializer(serializers.ModelSerializer):
    """
    Serializer for Topic model
    """
    class Meta:
        model = Topic
        fields = [
            'id',
            'title',
            'description',
            'image',
            'content_link',
            'order',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LabelSerializer(serializers.ModelSerializer):
    """
    Serializer for Label model with nested topics
    """
    topics = TopicSerializer(many=True, read_only=True)

    class Meta:
        model = Label
        fields = [
            'id',
            'title',
            'order',
            'topics',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CurriculumSerializer(serializers.ModelSerializer):
    """
    Serializer for Curriculum model with nested labels and topics
    """
    labels = LabelSerializer(many=True, read_only=True)

    class Meta:
        model = Curriculum
        fields = [
            'id',
            'title',
            'description',
            'image',
            'country',
            'is_active',
            'labels',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CurriculumListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for curriculum list view (without nested data)
    """
    class Meta:
        model = Curriculum
        fields = [
            'id',
            'title',
            'description',
            'image',
            'country',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TopicCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating topics with language-specific fields
    """
    class Meta:
        model = Topic
        fields = [
            'id',
            'label',
            'title_en',
            'title_ar',
            'description_en',
            'description_ar',
            'image',
            'content_link',
            'order',
            'is_active'
        ]
        read_only_fields = ['id']


class LabelCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating labels with language-specific fields
    """
    class Meta:
        model = Label
        fields = [
            'id',
            'curriculum',
            'title_en',
            'title_ar',
            'order'
        ]
        read_only_fields = ['id']


class CurriculumCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating curriculum with language-specific fields
    """
    class Meta:
        model = Curriculum
        fields = [
            'id',
            'title_en',
            'title_ar',
            'description_en',
            'description_ar',
            'image',
            'country',
            'is_active'
        ]
        read_only_fields = ['id']
