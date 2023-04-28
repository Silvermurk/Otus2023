# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main manage class for django project
"""

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hasker.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            'Please install django, django-widget-tweaks and django_extensions,'
            'also activate Venv throu ./scripts/venv/activate'
            ) from exc
    execute_from_command_line(sys.argv)
