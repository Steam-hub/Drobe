from modeltranslation.translator import register, TranslationOptions
from .models import Curriculum, Label, Topic


@register(Curriculum)
class CurriculumTranslationOptions(TranslationOptions):
    """
    Translation options for Curriculum model
    This will create title_en, title_ar, description_en, description_ar fields
    """
    fields = ('title', 'description')
    required_languages = {'en': ('title', 'description'), 'ar': ('title', 'description')}


@register(Label)
class LabelTranslationOptions(TranslationOptions):
    """
    Translation options for Label model
    This will create title_en, title_ar fields
    """
    fields = ('title',)
    required_languages = {'en': ('title',), 'ar': ('title',)}


@register(Topic)
class TopicTranslationOptions(TranslationOptions):
    """
    Translation options for Topic model
    This will create title_en, title_ar, description_en, description_ar fields
    """
    fields = ('title', 'description')
    required_languages = {'en': ('title', 'description'), 'ar': ('title', 'description')}
