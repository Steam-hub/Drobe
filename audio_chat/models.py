from django.db import models
import uuid


class ChatSession(models.Model):
    """
    Represents a chat session between a child and the AI assistant
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    level_description = models.TextField(help_text="Description of the game level")
    child_age = models.IntegerField(default=7, help_text="Child's age (4-10)")
    initial_message = models.TextField(
        blank=True,
        null=True,
        help_text="Initial context message sent to AI before student speaks"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'

    def __str__(self):
        return f"Session {self.id} - Age {self.child_age}"


class ChatMessage(models.Model):
    """
    Represents individual messages in a chat session
    """
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('audio', 'Audio'),
        ('image', 'Image'),
    )

    SENDER_TYPES = (
        ('child', 'Child'),
        ('assistant', 'Assistant'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=20, choices=SENDER_TYPES)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)

    # Content fields
    text_content = models.TextField(blank=True, null=True)
    audio_file = models.FileField(upload_to='audio_messages/', blank=True, null=True)
    image_file = models.ImageField(upload_to='screenshots/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'

    def __str__(self):
        return f"{self.sender} - {self.message_type} - {self.created_at}"
