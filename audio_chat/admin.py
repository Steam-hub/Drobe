from django.contrib import admin
from .models import ChatSession, ChatMessage


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'child_age', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'child_age', 'created_at')
    search_fields = ('id', 'level_description')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'sender', 'message_type', 'created_at')
    list_filter = ('sender', 'message_type', 'created_at')
    search_fields = ('id', 'text_content', 'session__id')
    readonly_fields = ('id', 'created_at')
