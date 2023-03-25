#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint:disable=broad-except
# pylint:disable=no-member
# pylint:disable=invalid-name

"""
Main class for HTTPServer api
"""
import argparse
import datetime
import hashlib
import json
import logging
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler

import Otus2023.dz3.api_handler.store as store_api
from dz3.api_handler.scoring import get_score, get_interests
from dz3.fields.fields import (DeclarativeFieldsMetaclass,
                               EMPTY_VALUES, ClientIDsField, DateField,
                               CharField, EmailField, BirthDayField,
                               PhoneField, GenderField, ArgumentsField)

# Looks ugly, but it was in  homework example
# so left untouched for compatibility
SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
    }
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
    }


class BasicClassRequest(metaclass=DeclarativeFieldsMetaclass):
    """
    Class accepts dict with argument values for fields,
    sets values to fields and stores names fields that are not null.
    Then validates all values passed by init
    function and returns dict with all errors that were discovered
    """

    def __init__(self, **kwargs):
        """
        Gets args and labels and produces error list after validation of both
        """
        non_empty_fields = []
        for (cls_fld_name, cls_fld_value) in self.all_fields:
            if cls_fld_name in kwargs:
                cls_fld_value.label = kwargs[cls_fld_name]
                if kwargs[cls_fld_name] not in list(EMPTY_VALUES):
                    non_empty_fields.append(cls_fld_name)
        self.non_empty_fields = non_empty_fields
        self.error_dict = None

    def validate(self):
        """
        validates fields based on empty / not empty
        and required / optional bias
        """
        error_dict = []
        for (cls_fld_name, cls_fld_value) in self.all_fields:
            if cls_fld_value.label in list(EMPTY_VALUES) \
                    and not cls_fld_value.nullable:
                error_dict.append((cls_fld_name, "This field cannot be empty"))
            if cls_fld_value.required \
                    and not hasattr(cls_fld_value, 'label'):
                error_dict.append((cls_fld_name, "This field is required"))
            if hasattr(cls_fld_value, 'label'):
                try:
                    cls_fld_value.validate(cls_fld_value.label)
                except Exception as exception:
                    error_dict.append((cls_fld_name, str(exception)))

        return error_dict

    def create_error_dict(self):
        """
        Creates dict for errors gathered from validation
        """
        error_dict = self.validate()
        if error_dict not in list(EMPTY_VALUES):
            self.error_dict = error_dict
            return True
        return False


class ClientsInterestsRequest(BasicClassRequest):
    """
    Class initiates and validates arguments passed by client interests
    get_interests - returns interests dict
    """

    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    @staticmethod
    def get_interests(interest_list):
        """
        Gets client interests from database
        """
        response_dict = {}
        for client in interest_list:
            response_dict[client] = get_interests(store=None, cid=client)
        return response_dict

    def get_result(self, ctx, store, **request):
        """
        Handles errors during interest retrivial
        """
        if self.create_error_dict():
            return self.error_dict, INVALID_REQUEST
        try:
            interest = get_interests(store, request['client_ids'])
            ctx['nclients'] = len(request['client_ids'])
            return interest, OK
        except Exception as exception:
            return "Error occurred during get_interests request " \
                   f"Exception: {exception}", \
                   INVALID_REQUEST


class OnlineScoreRequest(BasicClassRequest):
    """
    Class initiates and validates values passed by online_score request
    Does field validation for all base fields
    """
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self):
        has_combo = False
        basic_error_dict = super().validate()
        required_combos = [['email', 'phone'],
                           ['first_name', 'last_name'],
                           ['gender', 'birthday']]
        for combo in required_combos:
            if set(combo).issubset(self.non_empty_fields):
                has_combo = True
        if not has_combo:
            basic_error_dict.append((
                'multiple fields', 'One pair is required to be not null: '
                                   'email-phone, first_name-last_name, '
                                   'gender-birthday'))
            return basic_error_dict
        return None

    def get_result(self, ctx, store, is_admin, **request):
        """
        Returns resulting score and errors if any
        """
        if self.create_error_dict():
            return self.error_dict, INVALID_REQUEST
        ctx["has"] = self.non_empty_fields
        score_value = 42 if is_admin else get_score(store=store, **request)
        return {"score": score_value}, OK


class MethodRequest(BasicClassRequest):
    """
    Class validates all arguments that were received from POST request.
    is_admin validates admin login or basic one
    """

    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        """
        Basic admin check
        """
        for (cls_fld_name, cls_fld_value) in self.all_fields:
            if cls_fld_name == 'login':
                return cls_fld_value.label == ADMIN_LOGIN
        return None


def check_auth(request):
    """
    Checks if auth is valid or note based on hash
    """
    if request['login'] == ADMIN_LOGIN:
        code_for_hash = (
                datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT) \
            .encode('utf-8')
        digest = hashlib.sha512(code_for_hash).hexdigest()
    else:
        code_for_hash = (request['account'] + request['login'] + SALT) \
            .encode('utf-8')
        digest = hashlib.sha512(code_for_hash).hexdigest()
    if digest == request['token']:
        return True
    return False


def method_handler(request, ctx, store):
    """
    Method passes and validates requests
    """
    main_request = MethodRequest(**request['body'])
    if main_request.create_error_dict():
        return main_request.error_dict, INVALID_REQUEST

    # token processor, returns forbidden on bad auth
    if not check_auth(request['body']):
        return "Forbidden", FORBIDDEN

    # OnlineScore processor
    if request['body']['method'] == 'online_score':
        return OnlineScoreRequest(**request['body']['arguments']) \
            .get_result(ctx, store,
                        main_request.is_admin,
                        **request['body']['arguments'])

    # ClientInterests processor
    if request['body']['method'] == 'clients_interests':
        return ClientsInterestsRequest(**request['body']['arguments']) \
            .get_result(ctx, store,
                        **request['body']['arguments'])

    # Unknown method
    if request['body']['method'] not in ['online_score',
                                         'clients_interests']:
        return "Unknown method. Only 'online_score' and 'clients_interests' " \
               "are available", INVALID_REQUEST

    # Unknown cases
    return "Unknown error is in request", INVALID_REQUEST


class MainHTTPHandler(BaseHTTPRequestHandler):
    """
    Main HTTP handler class with builtin router
    """
    router = {
        "method": method_handler
        }
    store = store_api.Store()

    @staticmethod
    def get_request_id(headers):
        """
        Static method to get request ID
        """
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    # Server method, can to nothing to fix snake_case
    def do_POST(self):
        """
        Method does POST request
        """
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        data_string = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except Exception as exception:
            logging.exception("Bad request exception: %s", exception)
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s", self.path,
                         data_string.decode('utf-8'),
                         context["request_id"])
            if path in self.router:
                try:
                    response, code = \
                        self.router[path]({"body": request,
                                           "headers": self.headers},
                                          context,
                                          self.store)
                except Exception as exception:
                    logging.exception("Unexpected error: %s", exception)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            response = {"response": response, "code": code}
        else:
            response = {"error": response or ERRORS.get(code, "Unknown Error"),
                        "code": code}
        context.update(response)
        logging.info(context)
        output = json.dumps(response)
        self.wfile.write(output.encode('utf-8'))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Online Score APP (OSA)',
        description='Validates fields from post request',
        epilog='Some help text')
    parser.add_argument('-c', '--port', default=8080)
    parser.add_argument('-l', '--log', default='common.log')
    log_name = None if not parser.parse_args().log else parser.parse_args().log
    logging.basicConfig(filename=parser.parse_args().log,
                        level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')

    server = HTTPServer(("localhost", parser.parse_args().port),
                        MainHTTPHandler)
    logging.info("Starting server at %s", parser.parse_args().port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
