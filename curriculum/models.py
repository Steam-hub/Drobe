from django.db import models
import uuid


class Curriculum(models.Model):
    """
    Represents a curriculum for a specific country
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, help_text="Curriculum title")
    description = models.TextField(help_text="Curriculum description")
    image = models.ImageField(upload_to='curriculum/images/', blank=True, null=True, help_text="Curriculum image")
    country = models.CharField(max_length=100, help_text="Country for this curriculum")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['country', 'title']
        verbose_name = 'Curriculum'
        verbose_name_plural = 'Curricula'

    def __str__(self):
        return f"{self.title} - {self.country}"


class Label(models.Model):
    """
    Represents a label/category that groups multiple topics together within a curriculum
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='labels')
    title = models.CharField(max_length=255, help_text="Label title")
    order = models.IntegerField(default=0, help_text="Display order within curriculum")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['curriculum', 'order', 'title']
        verbose_name = 'Label'
        verbose_name_plural = 'Labels'

    def __str__(self):
        return f"{self.curriculum.title} - {self.title}"


class Topic(models.Model):
    """
    Represents a topic within a label, containing educational content
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=255, help_text="Topic title")
    description = models.TextField(help_text="Topic description")
    image = models.ImageField(upload_to='curriculum/topics/', blank=True, null=True, help_text="Topic image")
    content_link = models.URLField(max_length=500, help_text="Link to topic content")
    order = models.IntegerField(default=0, help_text="Display order within label")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['label', 'order', 'title']
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'

    def __str__(self):
        return f"{self.label.title} - {self.title}"
