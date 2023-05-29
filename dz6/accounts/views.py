# -*- coding: utf-8 -*-
# pylint:disable=too-many-ancestors
"""
Views used in django project
"""
from django.urls import reverse_lazy
from django.views import generic

from dz6.accounts.admin import UserChangeForm
from dz6.accounts.forms import UserAdminCreationForm
from dz6.accounts.models import MyUser


class SignUp(generic.CreateView):
    """
    Sign up form
    """
    form_class = UserAdminCreationForm
    success_url = reverse_lazy('login')
    template_name = 'accounts/signup.html'


class UserProfileUpdateView(generic.UpdateView):
    """
    Update ciew
    """
    model = MyUser
    form_class = UserChangeForm
    template_name = "accounts/update.html"
    success_url = reverse_lazy('question_list')

    def get_object(self, queryset=None):
        return self.request.user
