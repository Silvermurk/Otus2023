# -*- coding: utf-8 -*-
"""
Url manager of a django project
"""
from django.urls import path

from dz6.accounts import views

urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('<slug:login>/', views.UserProfileUpdateView.as_view(), name='user_profile')
]
