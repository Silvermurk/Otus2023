# -*- coding: utf-8 -*-
# pylint:disable=no-member
# pylint:disable=too-few-public-methods
"""
Django models
"""

import re

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from .utils import unique_slugify, pretty_date


class Question(models.Model):
    """
    Class with fields for questions
    """
    title = models.CharField(max_length=140)
    slug = models.SlugField(max_length=255)
    question_tags = models.CharField(max_length=200)
    question_text = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    positive_votes = models.IntegerField(default=0)
    negative_votes = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)

    def __unicode__(self):
        return self.title

    @property
    def get_trending(self):
        """
        Return ordered data by points
        """
        return self.order_by('-total_points', '-created_at')[:2]

    def get_date(self):
        """
        Get date in pretty format
        """
        return pretty_date(self.created_at)

    def get_tag_list(self):
        """
        Returns tag list for question
        """
        return re.split(" ", self.question_tags)

    def save(self, *args, **kwargs):
        """
        Saves question and updates votes
        """
        slug = self.title
        unique_slugify(self, slug)
        self.total_points = self.positive_votes - self.negative_votes
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Returns absolute user URL
        """
        return reverse('question_detail', kwargs={'slug': self.slug})


class QuestionVote(models.Model):
    """
    Class for voteing on question
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    value = models.BooleanField(default=True)

    class Meta:
        """
        Django meta class
        """
        unique_together = ('user', 'question')


class Answer(models.Model):
    """
    Class for answer
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)
    positive_votes = models.IntegerField(default=0)
    negative_votes = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        """
        Save answer method
        """
        self.total_points = self.positive_votes - self.negative_votes
        super().save(*args, **kwargs)

    def __unicode__(self):
        """
        Translate question to unicode
        """
        return f"id: {self.id} " \
               f"question: {self.question} " \
               f"text: {self.answer_text}"


class AnswerVote(models.Model):
    """
    Answer method for votes
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    value = models.BooleanField(default=True)

    class Meta:
        """
        Django meta class
        """
        unique_together = ('user', 'answer')
