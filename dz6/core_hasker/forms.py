# -*- coding: utf-8 -*-
# pylint:disable=too-few-public-methods
# pylint:disable=no-member
"""
Django forms module
"""
from django import forms

from .models import Question, Answer


class QuestionCreateForm(forms.ModelForm):
    """
    Form for create question and tags
    """

    class Meta:
        """
        Django meta class
        """
        model = Question
        fields = ['title', 'question_text', 'question_tags']

        labels = {
            'title': 'Title:',
            'question_text': 'Question detail:',
            }

    question_tags = forms.CharField(
        label='Tags:',
        widget=forms.TextInput(attrs={'Placeholder': 'tag1 tag2 tag3'}))

    def clean(self):
        """
        Clean data for user question form
        """
        tags = self.cleaned_data['question_tags']
        if len(tags.split()) > 3:
            raise forms.ValidationError('You cannot assign more than 3 tags')
        return self.cleaned_data


class AnswerCreateForm(forms.ModelForm):
    """
    Answer form for user creation
    """

    class Meta:
        """
        Django meta class
        """
        model = Answer
        fields = ['answer_text']

        labels = {'answer_text': '', }

    def __init__(self, author, current_question, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.author = author
        self.question = current_question

    def clean(self):
        """
        Clean data for user creation form
        """
        if Answer.object.filter(question=self.question, author=self.author):
            raise forms.ValidationError(
                'You were already asked')
        return self.cleaned_data
