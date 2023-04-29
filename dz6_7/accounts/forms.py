# -*- coding: utf-8 -*-
# pylint:disable=too-few-public-methods
"""
All forms that are used in Django project
"""

from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from dz6_7.accounts.models import MyUser


class RegisterForm(forms.ModelForm):
    """
    Form for user registration and setup of user avatar
    """
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    class Meta:
        """
        Django meta class
        """
        model = MyUser
        fields = ('login', 'email', 'avatar')

    def clean_email(self):
        """
        Clean method for email field
        """
        email = self.cleaned_data.get('email')
        clean_email = MyUser.objects.filter(email=email)
        if clean_email.exists():
            raise forms.ValidationError("email is taken")
        return email

    def clean_password(self):
        """
        Clean method for password field
        """
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match')
        return password1


class UserAdminCreationForm(forms.ModelForm):
    """
    A form for user creation. Has all the required fields
    and a prepared password
    """
    password1 = forms.CharField(label='Password',
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation',
                                widget=forms.PasswordInput)

    class Meta:
        """
        Django meta class
        """
        model = MyUser
        fields = ('login', 'email', 'avatar')

    def clean_password(self):
        """
        Checks that entered passwords are identical
        """
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match')
        return password1

    def save(self, commit=True):
        """
        Save password in hash form
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserAdminChangeForm(forms.ModelForm):
    """
    Form fur user updates. Includes all required fields.
    Password replaced with admin`s password hash
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        """
        Django meta class
        """
        model = MyUser
        fields = ('login', 'email', 'password',
                  'avatar', 'is_active', 'is_admin')

    def clean_password(self):
        """
        Returns the initial value, to whatever the user provides
        Done here because field has no access to initial value
        """
        return self.initial["password"]


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user
    """

    class Meta:
        """
        Django meta class
        """
        model = MyUser
        fields = ('login', 'email', 'avatar')

    login = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))
