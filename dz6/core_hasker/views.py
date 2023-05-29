# -*- coding: utf-8 -*-
# pylint:disable=no-member
# pylint:disable=too-many-ancestors
# pylint:disable=too-many-branches
# pylint:disable=arguments-differ
"""
Views general file for Django
"""

import operator
from functools import reduce

from django.db.models import Q
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, View

from dz6.core_hasker.forms import AnswerCreateForm, QuestionCreateForm
from dz6.core_hasker.models import Question, QuestionVote, Answer, AnswerVote


def error_404(request):
    """
    Returns 404 error page
    """
    data = {}
    return render(request, '404.html', data)


class QuestionListView(ListView):
    """
    Question list view for web
    """
    context_object_name = 'question_list'
    model = Question
    paginate_by = 20

    def get_queryset(self):
        """
        Gets the queryset for questions based on total points
        """
        return Question.objects.all().order_by('-created_at', '-total_points')

    def get_template_names(self):
        """
        Returns template names
        """
        return 'core_hasker/question_list.html'


class QuestionSearchListView(QuestionListView):
    """
    Display a Question List page filtered by the search query.
    """
    paginate_by = 20

    def get_queryset(self):
        """
        Get queryset for search
        """
        result = super().get_queryset()

        query = self.request.GET.get('q')
        if query:
            query_list = query.split()
            if query.startswith('tag:'):
                result = result.filter(
                    reduce(operator.and_,
                           (Q(question_tags__icontains=q[4:])
                            for q in query_list))
                    )
            else:
                result = result.filter(
                    reduce(operator.and_,
                           (Q(title__icontains=q) for q in query_list)) |
                    reduce(operator.and_,
                           (Q(question_text__icontains=q) for q in query_list))
                    )

        return result.order_by('-created_at')

    def get_template_names(self):
        """
        Gets template for question list
        """
        return 'core_hasker/question_list.html'


class QuestionDetailView(DetailView):
    """
    Detailed view for question
    """
    model = Question
    context_object_name = 'question_detail'
    template_name = 'core_hasker/question_detail.html'

    def get_context_data(self, **kwargs):
        """
        Gets context data for question details
        """
        context = super().get_context_data(**kwargs)
        selected_question = get_object_or_404(
            Question, slug=self.kwargs['slug'])
        context['form'] = AnswerCreateForm(self, self.request.user,
                                           instance=selected_question)
        return context


class QuestionCreateView(CreateView):
    """
    View for create question page
    """
    form_class = QuestionCreateForm
    template_name = 'core_hasker/new_question.html'
    context_object_name = 'new_question_form'

    def form_valid(self, form):
        """
        Check if question is valid
        """
        new_question = form.save(commit=False)
        new_question.author = self.request.user
        new_question.created_at = timezone.now()
        new_question.save()
        return HttpResponseRedirect(
            reverse('question_detail', kwargs={'slug': new_question.slug}))


class QuestionVoteView(View):
    """
    View for question vote page
    """
    model = Question
    vote_model = QuestionVote

    def post(self, request, object_id):
        """
        Post method for adding question
        """
        vote_target = get_object_or_404(self.model, pk=object_id)
        if vote_target.author == request.user:
            raise ValidationError(
                'Sorry, voting for your own question is not possible.')

        upvote = request.POST.get('upvote', None) is not None
        vote, created = self.vote_model.objects.get_or_create(
            defaults={'value': upvote},
            user=request.user,
            question=vote_target)
        if created:
            if upvote:
                vote_target.positive_votes += 1
            else:
                vote_target.negative_votes += 1

        else:
            if vote.value == upvote:
                vote.delete()

                if upvote:
                    vote_target.positive_votes -= 1

                else:
                    vote_target.negative_votes -= 1

            else:
                vote.value = upvote
                vote.save()
                if upvote:
                    vote_target.positive_votes += 1
                    vote_target.negative_votes -= 1

                else:
                    vote_target.negative_votes += 1
                    vote_target.positive_votes -= 1

        vote_target.save()

        next_url = request.POST.get('next', '')
        if next_url:
            return redirect(next_url)

        return HttpResponseRedirect(
            reverse('question_detail', kwargs={'slug': vote_target.slug}))


class AnswerVoteView(View):
    """
    View for answers page
    """
    model = Answer
    vote_model = AnswerVote

    def post(self, request, object_id):
        """
        Post method for answer page
        """
        vote_target = get_object_or_404(self.model, pk=object_id)
        if vote_target.author == request.user:
            raise ValidationError(
                'Sorry, voting for your own answer is not possible.')

        upvote = request.POST.get('upvote', None) is not None
        vote, created = self.vote_model.objects.get_or_create(
            defaults={'value': upvote},
            user=request.user,
            answer=vote_target)
        if created:
            if upvote:
                vote_target.positive_votes += 1
            else:
                vote_target.negative_votes += 1

        else:
            if vote.value == upvote:
                vote.delete()
                if upvote:
                    vote_target.positive_votes -= 1
                else:
                    vote_target.negative_votes -= 1

            else:
                vote.value = upvote
                vote.save()
                if upvote:
                    vote_target.positive_votes += 1
                    vote_target.negative_votes -= 1
                else:
                    vote_target.negative_votes += 1
                    vote_target.positive_votes -= 1

            vote_target.save()

        next_url = request.POST.get('next', '')
        if next_url:
            return redirect(next_url)
        return HttpResponseRedirect(
            reverse('question_detail',
                    kwargs={'slug': vote_target.question.slug}))


class AnswerCreateView(CreateView):
    """
    View for creating anserts
    """
    form_class = AnswerCreateForm
    template_name = 'core_hasker/question_detail.html'

    def get_form(self):
        """
        Get form for answer creation
        """
        current_question = get_object_or_404(Question,
                                             slug=self.kwargs['slug'])
        form = AnswerCreateForm(self.request.user, current_question,
                                self.request.POST)
        return form

    def get_context_data(self, **kwargs):
        """
        Gets context data for view creation
        """
        context = super().get_context_data(**kwargs)
        current_question = get_object_or_404(Question,
                                             slug=self.kwargs['slug'])
        answer_form = self.get_form()
        context['question_detail'] = current_question
        context['form'] = answer_form
        return context

    def form_valid(self, form):
        """
        Check if data input is valid
        """
        current_question = get_object_or_404(Question,
                                             slug=self.kwargs['slug'])
        instance = form.save(commit=False)
        instance.question = current_question
        instance.author = self.request.user
        instance.save()
        return HttpResponseRedirect(
            reverse('question_detail', kwargs={'slug': current_question.slug}))
