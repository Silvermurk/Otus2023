from django.urls import path

from . import views
"""
Url manager of a django project
"""

urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('<slug:login>/', views.UserProfileUpdateView.as_view(), name='user_profile')
]
