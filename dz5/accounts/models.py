from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
    )
from django.urls import reverse
"""
All user and admin pages of a django project
"""


class DjangoUserManager(BaseUserManager):
    def create_user(self, email, login, avatar, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        if not login:
            raise ValueError('Users must have login')

        user = self.model(
            email=self.normalize_email(email),
            login=login,
            avatar=avatar,
            )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, login, avatar, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            login=login,
            password=password,
            avatar=avatar,
            )
        user.is_admin = True
        user.save(using=self._db)
        return user


class HaskerUser(AbstractBaseUser):
    email = models.EmailField(
        verbose_name='e-mail address',
        max_length=255,
        unique=True,
        )
    login = models.CharField(max_length=64, unique=True, )
    avatar = models.ImageField(upload_to='static/avatars/')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = DjangoUserManager()

    USERNAME_FIELD = 'login'
    REQUIRED_FIELDS = ['avatar', 'email']

    def __str__(self):
        return self.login

    @staticmethod
    def has_permissions():
        """
        Checks if a user has any specific permissions
        We assume thai it is always true
        """
        return True

    @staticmethod
    def has_module_permissions():
        """
        Checks if a user has a permission to view app_label
        We assume it is always true
        """
        return True

    def get_absolute_url(self):
        """
        Returns absolute url for current user
        """
        return reverse('user_profile', kwargs={'slug': self.login})

    @property
    def is_staff(self):
        """
        Checks if a user is a member of official staff
        We assume all admins are staff
        """
        return self.is_admin
