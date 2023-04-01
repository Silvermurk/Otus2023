import datetime
import hashlib

import pytest

from dz3.api_handler import store, scoring
from dz3.api_handler.api import (ADMIN_LOGIN, ADMIN_SALT, SALT, FORBIDDEN,
                                 method_handler, INVALID_REQUEST)


def gen_good_auth(request_body):
    if request_body['login'] == ADMIN_LOGIN:
        code_for_hash = (datetime.datetime.now()
                         .strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')
        return hashlib.sha512(code_for_hash).hexdigest()
    else:
        code_for_hash = (request_body['account']
                         + request_body['login'] + SALT).encode('utf-8')
        return hashlib.sha512(code_for_hash).hexdigest()


class TestResponseRequest:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.context = {}
        self.headers = {}
        self.store = store.Store('debug')

    def get_response(self, request):
        return method_handler({"body": request, "headers": self.headers},
                              self.context,
                              self.store)

    @pytest.mark.parametrize("bad_auth_request", [
        {"account": "horns&hoofs", "login": "h&f",
         "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f",
         "method": "online_score", "token": "sdd", "arguments": {}},
        {"account": "horns&hoofs", "login": "admin",
         "method": "online_score", "token": "", "arguments": {}},
        ], ids=["no-token-user", "fake-token-user", "no-token-admin"])
    def test_bad_auth(self, bad_auth_request):
        param_input, expected_output = bad_auth_request, FORBIDDEN
        _, result_code = self.get_response(param_input)
        assert result_code == expected_output

    @pytest.mark.parametrize("invalid_request", [
        {"account": "horns&hoofs", "login": "h&f",
         "method": "online_score", "token": "sdd", "arguments": {}},
        {"account": "horns&hoofs", "login": "admin",
         "method": "bad_online_score", "token": "", "arguments": {}},
        ], ids=["empty_arguments", "invalid method"])
    def test_invalid_request(self, invalid_request):
        param_input = invalid_request
        param_input['token'] = gen_good_auth(param_input)
        error_msg, result_code = self.get_response(param_input)
        expected_output = INVALID_REQUEST
        print(error_msg)
        assert expected_output == result_code


class TestOnlineScoreMethod:
    @pytest.fixture(scope='function', autouse=True)
    def setup(self):
        self.context = {}
        self.headers = {}
        self.good_store = store.Store('sql')
        self.bad_store = store.Store('???')

    def get_response_good_store(self, request):
        return method_handler({"body": request, "headers": self.headers},
                              self.context, self.good_store)

    @pytest.mark.parametrize(("query", "expected_output"), [
        ({"account": "hf", "login": "???",
          "method": "online_score", "token": "???", "arguments":
              {"phone": "79859859857", "email": "shitmail@me.da",
               "first_name": "Satan", "last_name": "FromHell",
               "birthday": "01.01.1980", "gender": 1}}, 5),
        ({"account": "hf", "login": "???",
          "method": "online_score", "token": "???", "arguments":
              {
                  "phone": "79859859857", "email": "shitmail@me.da",
                  "first_name": "Jesus", "last_name": "",
                  "birthday": "01.01.1980", "gender": 1
                  }}, 4.5),
        ({"account": "hf", "login": "admin", "method":
            "online_score", "token": "???", "arguments":
              {
                  "phone": "79859859857", "email": "shitmail@me.da",
                  "first_name": "Vasya", "last_name": "",
                  "birthday": "01.01.1980", "gender": 1
                  }}, 43),
        ],
                             ids=["user-all_fields",
                                  "user_no_last_name",
                                  "admin_no_last_name"])
    def test_correct_score_calculation(self, query, expected_output):
        """
        Theoretically we can check everything, but... Too lazy for example
        """
        param_input, expected_output = query, expected_output
        param_input['token'] = gen_good_auth(param_input)
        result, _ = self.get_response_good_store(param_input)
        assert float(result['score']) == float(expected_output)

    @pytest.mark.parametrize(("query", "field_to_remove"), [
        ({"account": "hf", "login": "test",
          "method": "online_score", "token": "???", "arguments":
              {"phone": "79859859857", "email": "shitmail@me.da",
               "first_name": "Ivan", "last_name": "Demisov",
               "birthday": "01.01.1980", "gender": 1}}, "email"),
        ], ids=["user-all_fields_remove_last_name"])
    def test_check_cache_when_change_parameters(self, query, field_to_remove):
        """
        At the start we calculate score and assume it is in cache.
        Then remove field that should reduce overall score.
        But assert it should not change - because data was cached.
        """

        params_initial, field_to_remove = query, field_to_remove
        params_initial['token'] = gen_good_auth(params_initial)
        result_initial, _ = self.get_response_good_store(params_initial)
        params_new = params_initial
        params_new[field_to_remove] = ""
        result_new, _ = self.get_response_good_store(params_new)
        assert float(result_initial['score']) == float(result_new['score'])

    @pytest.mark.parametrize("query", [
        {"account": "hf", "login": "horse&hoofs",
         "method": "online_score", "token": "???", "arguments":
             {"phone": "79859859857", "email": "shitmail@me.da",
              "first_name": "Ivan", "last_name": "Demidov",
              "birthday": "01.01.1980", "gender": 1}}],
                             ids=["user-all_fields_disable_store"])
    def test_check_online_score_restore_connection(self, query):
        params_initial = query
        params_initial['token'] = gen_good_auth(params_initial)
        if self.good_store.conn_cache.conn:
            self.good_store.conn_cache.conn.close()
        result_new = scoring.get_score(
            store=self.good_store,
            phone=params_initial['arguments'].get('phone', None),
            email=params_initial['arguments'].get('email', None),
            birthday=params_initial['arguments'].get('birthday', None),
            gender=params_initial['arguments'].get('gender', None),
            first_name=params_initial['arguments'].get('first_name', None),
            last_name=params_initial['arguments'].get('last_name', None))
        aa = 1
        assert self.good_store.conn_cache.conn is not None

    @pytest.mark.parametrize("query", [
        {"account": "hf", "login": "123", "method": "online_score", "token": "123", "arguments":
            {"phone": "71234567890", "email": "a@b.ru", "first_name": "Stan", "last_name": "Stupnikov",
             "birthday": "01.01.1991", "gender": 1}}], ids=["user-all_fields_disable_store"])
    def test_online_score__works_when_store_is_unavailable(self, query):
        params_initial = query
        params_initial['token'] = gen_good_auth(params_initial)
        result_new = scoring.get_score(
            store=self.bad_store,
            phone=params_initial['arguments'].get('phone', None),
            email=params_initial['arguments'].get('email', None),
            birthday=params_initial['arguments'].get('birthday', None),
            gender=params_initial['arguments'].get('gender', None),
            first_name=params_initial['arguments'].get('first_name', None),
            last_name=params_initial['arguments'].get('last_name', None))

        assert result_new > 0

    @pytest.mark.parametrize("bad_request", [
        {"account": "hf", "login": "123",
         "method": "online_score", "token": "123", "arguments":
             {"phone": "71234567890", "email": "",
              "first_name": "Stan", "last_name": "",
              "birthday": "01.01.1991", "gender": ""}},
        ], ids=["missed_email_last_name_gender"])
    def test_missed_required_arguments(self, bad_request):
        '''
        at the beginnig we calculate score and think that it should be in cache. Then remove the field that should
        reduce score but expect that score won't change because it will be retrieved from cache
        You should NOT change first name, last name or birthday (only email, phone and gender are available)
        '''

        param_input = bad_request
        param_input['token'] = gen_good_auth(param_input)
        error_msg, result_code = self.get_response_good_store(param_input)
        expected_output = INVALID_REQUEST
        assert expected_output == result_code


class TestGetInterestMethod:
    @pytest.fixture(scope='function', autouse=True)
    def setup(self):
        self.context = {}
        self.headers = {}
        self.good_store = store.Store('sql')
        self.bad_store = store.Store('???')

    def get_response_good_store(self, request):
        return method_handler({"body": request, "headers": self.headers}, self.context, self.good_store)

    @pytest.mark.parametrize(("query", "expected_output"), [
        ({"account": "horns&hoofs", "login": "ff",
          "method": "clients_interests", "token": "",
          "arguments": {"client_ids": [1, 2], "date": "20.07.2017"}},
         [{'client_id': 1, 'interests': 'cars pets sport'},
          {'client_id': 2, 'interests': 'hi-tech music tv'}]),
        ({"account": "horns&hoofs", "login": "ff",
          "method": "clients_interests", "token": "",
          "arguments": {"client_ids": [1], "date": ""}},
         [{'client_id': 1, 'interests': 'cars pets sport'}]),
        ({"account": "horns&hoofs", "login": "ff",
          "method": "clients_interests", "token": "",
          "arguments": {"client_ids": [6], "date": "20.07.2017"}}, [])
        ],
                             ids=["existing_ids_with_date",
                                  "existing_ids_without_date",
                                  "no_existing_id_with_date"])
    def test_correct_query(self, query, expected_output):
        '''
        compare calculated output with the real rows in SQL db
        '''
        param_input, expected_output = query, expected_output
        param_input['token'] = gen_good_auth(param_input)
        result, _ = self.get_response_good_store(param_input)
        assert result == expected_output

    @pytest.mark.parametrize(("cids"), [([1, 2])], ids=['good_cids_bad_store'])
    def test_try_get_interests_from_bad_store(self, cids):
        '''
        Try to retrieve the data from non-existent store
        '''
        with pytest.raises(Exception):
            scoring.get_interests(store=self.bad_store, cid=cids)