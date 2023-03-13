# -*- coding: utf-8 -*-
# pylint:disable=duplicate-code
"""
Tests for log_analyzer
"""

import copy
import json
import os

from dz1.log_analyzer.fs_utils import (load_external_config,
                                       check_for_logs,
                                       check_for_reports)
from dz1.log_analyzer.report_creator import create_report


def test_load_external_config():
    """
    Method to test loading of external configs
    :return: None
    """
    class Namespace:
        """
        Argparser-analogue class to mock it`s iterable namespace
        """
        def __init__(self, **kwargs):
            for name in kwargs.items():
                setattr(self, name[0], name[1])

        def __eq__(self, other):
            if not isinstance(other, Namespace):
                return NotImplemented
            return vars(self) == vars(other)

        def __contains__(self, key):
            return key in self.__dict__

    config = {
        "REPORT_SIZE": 1000,
        "REPORT_DIR": "./output",
        "LOG_DIR": "./input"
        }

    expected = copy.copy(config)
    print(f'!!!{os.listdir(os.getcwd())}!!!')
    with open(f'{os.getcwd()}/dz1/log_analyzer/config.json',
              encoding='utf-8') as file:
        expected.update(json.load(file))

    load_external_config(
        Namespace(config='config.json'),
        config)

    assert config == expected, f'Failed to load external config \n ' \
                               f'{config} != {expected}'


def test_bad_input_dir():
    """
    Method to test config with bad input directory
    """
    config = {
        "REPORT_SIZE": 1000,
        "REPORT_DIR": "./output",
        "LOG_DIR": "./bad_input"
        }
    assert check_for_logs(config) is None, 'Log reader raised ' \
                                           'exception on bad dir'


def test_bad_output_dir():
    """
    Method to test config with bad output directory
    """
    config = {
        "REPORT_SIZE": 1000,
        "REPORT_DIR": "./bad_output",
        "LOG_DIR": "./input"
        }
    assert check_for_reports(config) is None, 'Report reader raised ' \
                                              'exception on bad dir'


def test_report_creator():
    """
    Test for report creator on two-line log example
    """
    config = {
        "REPORT_SIZE": 1000,
        "REPORT_DIR": "./bad_output",
        "LOG_DIR": "./input"
        }
    result = create_report(config, 'nginx-access-ui.log-20100101')
    expected = [{'url': '/api/v2/banner/25019354',
                 'count': 1,
                 'time_sum': 0.39,
                 'time_max': 0.39,
                 'count_perc': 50.0,
                 'time_perc': 74.5697896749522,
                 'time_med': 0.39},
                {'url': '/api/1/photogenic_banners/list/?server_name=WIN7RB4',
                 'count': 1,
                 'time_sum': 0.133,
                 'time_max': 0.133,
                 'count_perc': 50.0,
                 'time_perc': 25.430210325047803,
                 'time_med': 0.133}]

    assert result == expected, 'report creator does not work properly'
