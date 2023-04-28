from .forms import UserChangeForm, UserAdminCreationForm
from django.urls import reverse_lazy
from django.views import generic
from .models import HaskerUser
"""
Views used in django project
"""


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
    model = HaskerUser
    form_class = UserChangeForm
    template_name = "accounts/update.html"
    success_url = reverse_lazy('question_list')

    def get_object(self, queryset=None):
        return self.request.user
