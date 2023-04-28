# -*- coding: utf-8 -*-
# pylint:disable=too-few-public-methods

"""
Admin page of a django project
"""

from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import HaskerUser


class UserCreationForm(forms.ModelForm):
    """
    Form for creating a new user.
    Has all required fields and a dual password confirmation.
    """
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        """
        Django meta class
        """
        model = HaskerUser
        fields = ('email', 'login', 'avatar')

    def clean_password(self):
        """
        Check if passwords entered are a match
        """
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        """
        Save a password in a hashed format
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """
    Form for updateing user info.
    Hass all the fields required and a admin password in hash diplay
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        """
        Django meta class
        """
        model = HaskerUser
        fields = ('email', 'login', 'password',
                  'avatar', 'is_active', 'is_admin')

    def clean_password(self):
        """
        Returns the initial value, to whatever the user provides
        Done here because field has no access to initial value
        """
        return self.initial["password"]


class UserAdmin(BaseUserAdmin):
    """
    This form adds or changes user instances
    Fields are used in user Model display
    Overrides the definition on userAdmin
    """
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('login', 'email', 'avatar', 'is_admin')
    list_filter = ('is_admin',)
    fieldsets = (
        (None, {'fields': ('login', 'email', 'password')}),
        ('Personal info', {'fields': ('avatar',)}),
        ('Permissions', {'fields': ('is_admin',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('login', 'email', 'avatar', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


admin.site.register(HaskerUser, UserAdmin)
admin.site.unregister(Group)
