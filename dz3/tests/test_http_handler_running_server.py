# pylint:disable=missing-function-docstring
# pylint:disable=unused-argument
# pylint:disable=implicit-str-concat
# pylint:disable=consider-using-from-import

"""
Module for API tests
"""

import datetime
import hashlib
import json

import pytest
import requests

from dz3.api_handler.api import ADMIN_LOGIN, ADMIN_SALT, SALT


# Requires API started at http://127.0.0.1:8080
def gen_good_auth(request_body):
    if request_body['login'] == ADMIN_LOGIN:
        code_for_hash = (datetime.datetime.now()
                         .strftime("%Y%m%d%H") + ADMIN_SALT) \
            .encode('utf-8')
        return hashlib.sha512(code_for_hash).hexdigest()
    code_for_hash = (request_body['account']
                     + request_body['login'] + SALT).encode('utf-8')
    return hashlib.sha512(code_for_hash).hexdigest()


@pytest.mark.parametrize(("request_body", "request_header"),
                         [('{"account": "horns&hoofs", '
                           '"login": "hf",\n"method": '
                           '"online_score", "token": "", '
                           '"arguments": {"phone": "79859859857", '
                           '"email": "shitmail@me.da", "first_name": '
                           '"invan", "last_name": "demidov", '
                           '"birthday": "01.01.1980", "gender": 1}}',
                           {'Content-Type': 'application/json', })],
                         ids=['valid_request'])
def test_http_handler_valid_request(request_body, request_header):
    request_body = json.loads(request_body)
    request_body['token'] = gen_good_auth(request_body)
    request_body = json.dumps(request_body)
    response = requests.post('http://127.0.0.1:8080/method/', data=request_body)
    assert response.status_code == 200


@pytest.mark.parametrize(("request_body", "request_header"),
                         [('{"account": "horns&hoofs", '
                           '"login": "hf",\n"method": "online_score", '
                           '"token": "", '
                           '"arguments": {"phone": "79859859857", '
                           '"email": "shitmail@me.da", "first_name": '
                           '"invan", "last_name": "demidov", '
                           '"birthday": "01.01.1980", "gender": 1}}',
                           {'Content-Type': 'application/json', })],
                         ids=['valid_request-wrong-path'])
def test_http_handler_wrong_path(request_body, request_header):
    request_body = json.loads(request_body)
    request_body['token'] = gen_good_auth(request_body)
    request_body = json.dumps(request_body)
    response = requests.post('http://127.0.0.1:8080/met/', data=request_body)
    assert response.status_code == 404


@pytest.mark.parametrize(("request_body", "request_header"),
                         [('{'"account"': "horns&hoofs", '
                           '"login": "hf",\n"method": "online_score", '
                           '"token": "", '
                           '"arguments": {"phone": "79175002040", '
                           '"email": "shitmail@me.da", "first_name": '
                           '"invan", "last_name": "demidov", '
                           '"birthday": "01.01.1980", "gender": 1}}',
                           {'Content-Type': 'application/json', })],
                         ids=['account_field_with_excessive_quotes'])
def test_http_handler_bad_request(request_body, request_header):
    response = requests.post('http://127.0.0.1:8080/method/', data=request_body)
    assert response.status_code == 400


@pytest.mark.parametrize(("request_body", "request_header"),
                         [('{"acount": "horns&hoofs", '
                           '"login": "hf",\n"method": "online_score", '
                           '"token": "", '
                           '"arguments": {"phone": "79175002040", '
                           '"email": "shitmail@me.da", "first_name": '
                           '"invan", "last_name": "demidov", '
                           '"birthday": "01.01.1980", "gender": 1}}',
                           {'Content-Type': 'application/json', })],
                         ids=['acount instead of account'])
def test_http_handler_internal_error(request_body, request_header):
    response = requests.post('http://127.0.0.1:8080/method/', data=request_body)
    assert response.status_code == 500
