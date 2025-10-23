from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline, TranslationStackedInline
from .models import Curriculum, Label, Topic


class LabelInline(TranslationStackedInline):
    """Inline for adding labels directly from curriculum page"""
    model = Label
    extra = 1
    fields = ('title', 'order')
    show_change_link = True
    classes = ('collapse',)


class TopicInline(TranslationTabularInline):
    """Inline for adding topics directly from label page"""
    model = Topic
    extra = 1
    fields = ('title', 'description', 'image', 'content_link', 'order', 'is_active')
    show_change_link = True


@admin.register(Curriculum)
class CurriculumAdmin(TranslationAdmin):
    """Admin interface for Curriculum with translation support"""
    list_display = ('title', 'country', 'label_count', 'is_active', 'created_at')
    list_filter = ('country', 'is_active', 'created_at')
    list_editable = ('is_active',)
    search_fields = ('title', 'country', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at', 'label_count')
    inlines = [LabelInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'country', 'description')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('id', 'label_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def label_count(self, obj):
        """Display count of labels in this curriculum"""
        count = obj.labels.count()
        return format_html('<strong>{}</strong> labels', count)
    label_count.short_description = 'Labels'

    class Meta:
        verbose_name = 'Curriculum'
        verbose_name_plural = 'Curricula'


@admin.register(Label)
class LabelAdmin(TranslationAdmin):
    """Admin interface for Label with translation support"""
    list_display = ('title', 'curriculum', 'order', 'topic_count', 'created_at')
    list_filter = ('curriculum', 'created_at')
    list_editable = ('order',)
    search_fields = ('title', 'curriculum__title')
    readonly_fields = ('id', 'created_at', 'updated_at', 'topic_count')
    inlines = [TopicInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('curriculum', 'title', 'order')
        }),
        ('System Information', {
            'fields': ('id', 'topic_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def topic_count(self, obj):
        """Display count of topics in this label"""
        count = obj.topics.count()
        return format_html('<strong>{}</strong> topics', count)
    topic_count.short_description = 'Topics'


@admin.register(Topic)
class TopicAdmin(TranslationAdmin):
    """Admin interface for Topic with translation support"""
    list_display = ('title', 'label', 'get_curriculum', 'order', 'is_active', 'created_at')
    list_filter = ('label__curriculum', 'label', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'description', 'label__title', 'label__curriculum__title')
    readonly_fields = ('id', 'created_at', 'updated_at', 'image_preview')
    autocomplete_fields = []

    fieldsets = (
        ('Basic Information', {
            'fields': ('label', 'title', 'description', 'order')
        }),
        ('Media', {
            'fields': ('image', 'image_preview', 'content_link')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_curriculum(self, obj):
        """Display the curriculum this topic belongs to"""
        return obj.label.curriculum.title
    get_curriculum.short_description = 'Curriculum'
    get_curriculum.admin_order_field = 'label__curriculum__title'

    def image_preview(self, obj):
        """Display image preview in admin"""
        if obj.image:
            return format_html('<img src="{}" style="max-height: 200px; max-width: 300px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Image Preview'
