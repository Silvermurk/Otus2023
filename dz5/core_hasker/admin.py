"""
Admin page for django project
"""

from django.contrib import admin

from dz5.core_hasker.models import Question, Answer


class QuestionAdmin(admin.ModelAdmin):
    """
    Admin question form
    """
    list_display = ('title', 'author', 'created_at')
    prepopulated_fields = {'slug': ('title',)}


class AnswerAdmin(admin.ModelAdmin):
    """
    Admin answer form
    """


class SavedQuestionAdmin(admin.ModelAdmin):
    """
    Saved Qestion admin form
    """
    list_display = ('user', 'question',)


class QuestionTagAdmin(admin.ModelAdmin):
    """
    Tag admin form
    """
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
