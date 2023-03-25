# -*- coding: utf-8 -*-
# pylint:disable=too-few-public-methods

"""
Class for declarative fields
"""

import datetime
import re
from abc import ABCMeta, abstractmethod

# Null values for validator,will trigger the nullable check if in any field.
EMPTY_VALUES = (None, '', [], (), {})


class Field(metaclass=ABCMeta):
    """
    Basic class for all validated fields
    """

    def __init__(self, label=None, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self.label = label

    @abstractmethod
    def validate(self, label):
        """
        Not implemented raise in case method not overridden
        """
        raise NotImplementedError


class CharField(Field):
    """
    String-type field
    """

    def validate(self, label):
        if label not in list(EMPTY_VALUES):
            if not isinstance(label, str):
                raise ValueError("CharField accepts only string type")


class ArgumentsField(Field):
    """
    Dict-type fields, accepts arguments
    """

    def validate(self, label):
        if label not in list(EMPTY_VALUES):
            if not isinstance(label, dict):
                raise ValueError("ArgumentsField accepts only dict type")


class EmailField(CharField):
    """
    E-mail validation field, based on regex
    """

    def validate(self, label):
        super().validate(label)
        if label not in list(EMPTY_VALUES):
            email_regex = \
                re.compile(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$")
            if not email_regex.match(label):
                raise ValueError("E-mail address is not valid")


class PhoneField(Field):
    """
    Phone validation field, 11 digits, starting with 7
    """

    def validate(self, label):
        if label not in list(EMPTY_VALUES):
            if not (len(str(label)) == 11
                    and str(label).startswith('7') and str(label).isdigit()):
                raise ValueError("Phone number is 11 digit long "
                                 "and starts with 7")


class DateField(Field):
    """
    Date validation field, format DD.MM.YYY
    """

    def validate(self, label):
        if label not in list(EMPTY_VALUES):
            try:
                datetime.datetime.strptime(str(label), '%d.%m.%Y')
            except ValueError as expression:
                raise ValueError("Incorrect date format, "
                                 "should be DD-MM-YYYY") from expression


class BirthDayField(DateField):
    """
    Birthday validation field, formatted as DD.MM.YYY and bust be within 70
    years from today
    """

    def validate(self, label):
        super().validate(label)
        if label not in list(EMPTY_VALUES):
            current_date = datetime.datetime.now()
            converted_birthday = datetime.datetime.strptime(str(label),
                                                            '%d.%m.%Y')
            if (current_date.year - converted_birthday.year) > 70:
                raise ValueError("Birthday year cannot be higher than 70 "
                                 f"years from {datetime.datetime.now().date}")


class GenderField(Field):
    """
    Gender validation field.
    Can be empty
    Accepts 0,1,2
    """

    def validate(self, label):
        if label not in list(EMPTY_VALUES):
            if label not in [0, 1, 2]:
                raise ValueError("Incorrect value for gender field, "
                                 "allowed 0, 1, 2")


class ClientIDsField(Field):
    """
    Client IDs validation field
    Should be a list
    """

    def validate(self, label):
        if label not in list(EMPTY_VALUES):
            if not isinstance(label, list):
                raise ValueError("Client Ids should be a list")


class DeclarativeFieldsMetaclass(type):
    """
    Metaclass to collect and check all basic fields
    """

    def __new__(mcs, name, bases, attrs):
        # Collect fields from current class.
        all_fields = []
        for key, value in list(attrs.items()):
            if isinstance(value, Field):
                all_fields.append((key, value))
        new_class = super(DeclarativeFieldsMetaclass, mcs).__new__(
            mcs, name, bases, attrs)
        new_class.all_fields = all_fields
        return new_class
