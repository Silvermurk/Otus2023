# -*- coding: utf-8 -*-
# pylint:disable=too-many-return-statements
# pylint:disable=protected-access
# pylint:disable=consider-using-f-string
"""
Class for different utilities
"""
import re

from django.template.defaultfilters import slugify
from django.utils import timezone


def pretty_date(datetime_field):
    """
    Get a datetime and translate it to int or timestamp
    Return a pretty string
    """
    now = timezone.now()
    diff = now - datetime_field
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(int(round(second_diff, 0))) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(int(round(second_diff / 60, 0))) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(int(round(second_diff / 3600, 0))) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(int(round(day_diff, 0))) + " days ago"
    if day_diff < 31:
        return str(int(round(day_diff / 7, 0))) + " weeks ago"
    if day_diff < 365:
        return str(int(round(day_diff / 30, 0))) + " months ago"
    return str(int(round(day_diff / 365, 0))) + " years ago"


def unique_slugify(instance, value, slug_field_name='slug', queryset=None,
                   slug_separator='-'):
    """
    Calculates and stores a unique slug of 'value' for an instance.
    'slug_field_name' should be a string matching the name of the field to
    store the slug in (and the field to check against for uniqueness).
    'queryset' usually doesn't need to be explicitly provided - it'll default
    to using the '.all()' queryset from the model's default manager.
    """
    slug_field = instance._meta.get_field(slug_field_name)

    slug_len = slug_field.max_length

    slug = slugify(value)
    if slug_len:
        slug = slug[:slug_len]
    slug = _slug_strip(slug, slug_separator)
    original_slug = slug

    if queryset is None:
        queryset = instance.__class__._default_manager.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    _next = 2
    while not slug or queryset.filter(**{slug_field_name: slug}):
        slug = original_slug
        end = f'{slug_separator}{_next}'
        if slug_len and len(slug) + len(end) > slug_len:
            slug = slug[:slug_len - len(end)]
            slug = _slug_strip(slug, slug_separator)
        slug = f'{slug}{end}'
        _next += 1

    setattr(instance, slug_field.attname, slug)


def _slug_strip(value, separator='-'):
    """
    Cleans up a slug by removing slug separator characters that occur at the
    beginning or end of a slug.
    If an alternate separator is used, it will also replace any instances of
    the default '-' separator with the new separator.
    """
    separator = separator or ''
    if separator == '-' or not separator:
        re_sep = '-'
    else:
        re_sep = '(?:-|%s)' % re.escape(separator)
    if separator != re_sep:
        value = re.sub('%s+' % re_sep, separator, value)
    if separator:
        if separator != '-':
            re_sep = re.escape(separator)
        value = re.sub(r'^%s+|%s+$' % (re_sep, re_sep), '', value)
    return value
