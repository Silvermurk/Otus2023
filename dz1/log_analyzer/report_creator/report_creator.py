# -*- coding: utf-8 -*-
# pylint:disable=anomalous-backslash-in-string

"""
Report creater module for log_analyzer
Gets log file on input and parses each line throu regular expression
If too many lines are broken (50+%) - logs en exception
Results in a list of lines that fit expression and have max(time_max)
"""

import gzip
import os
import re
import statistics

from dz1.log_analyzer.log import logger

line_format = re.compile(
    '(?P<remote_addr>(?:^|\b(?<!\.))'
    '(?:1?\d\d?|2[0-4]\d|25[0-5])(?:\.(?:1?\d\d?|2[0-4]\d|25[0-5])){3}'
    '(?=$|[^\w.]))\s'
    '(?P<useless_data>-|\S{0,30})\s{2}'
    '(?P<remote_usr>-|[a-z_][a-z0-9_]{0,30})\s'
    '(?P<date_time>\[(?P<date>[0-3][0-9]\/\w{3}\/[12]\d{3}):'
    '(?P<time>\d\d:\d\d:\d\d).*\])\s(?P<request>\"'
    '(?P<req_method>GET|POST|HEAD|PUT|DELETE|CONNECT|OPTIONS|TRACE|PATCH)\s'
    '(?P<req_uri>\S*)\s(?P<http_ver>HTTP/\d\.\d)\")\s'
    '(?P<status>\d{3})\s'
    '(?P<body_byte_sent>\d+)\s\"'
    '(?P<http_referer>[^\s]+)\"\s\"'
    '(?P<user_agent>[^\"]+)\"\s\"'
    '(?P<forward_for>[^\"]+)\"\s\"'
    '(?P<x_req_id>-|\d{0,16}-\d{0,16}-\d{0,16}-\d{0,16})\"\s\"'
    '(?P<x_rb_usr>\S{0,30})\"\s'
    '(?P<req_time>\d.\d{0,10})')


def create_report(config: dict, file: str) -> list:
    """
    Method gets config and log file path as input and results a list
    of requests with maximum time_max
    :param config: Dictionary containing config data from main script
    :param file: Path to log file to analyze
    :return: list of files matching expression with max(time_max)
    """
    file_path = os.getcwd() + f'/{config["LOG_DIR"]}/{file}'
    if file.endswith('.gz'):
        log_file = gzip.open(file_path, encoding='utf-8')
    else:
        log_file = open(file_path, encoding='utf-8')

    results = dict()
    total_time = int()
    bad_reqs = int()
    for line in log_file:
        if isinstance(line, bytes):
            line = line.decode('utf-8')

        data = re.search(line_format, line)
        if data:
            datadict = data.groupdict()
            req_uri = datadict['req_uri']
            req_time = float(datadict['req_time'])
            if req_uri not in results:
                results[req_uri] = dict()
                results[req_uri]['url'] = req_uri
                results[req_uri]['count'] = 1
                results[req_uri]['time_sum'] = req_time
                results[req_uri]['time_max'] = req_time
                results[req_uri]['median'] = []
                results[req_uri]['median'].append(req_time)
            else:
                results[req_uri]['count'] += 1
                results[req_uri]['time_sum'] += req_time
                results[req_uri]['time_max'] = \
                    max(results[req_uri]['time_max'],
                        req_time)
                results[req_uri]['median'].append(req_time)
            total_time += req_time
        else:
            if '"0" 400' not in line:
                bad_reqs += 1
                logger.exception('Bad line %s', line)
    result_tuples = sorted(results.items(), key=lambda x: x[1]['time_sum'],
                           reverse=True)
    if bad_reqs / len(result_tuples) * 100 > 50:
        logger.error('More than 50% of lines were not parsed')
        raise Exception('More than 50% of lines were not parsed')

    if len(result_tuples) > config['REPORT_SIZE']:
        first_k = dict(result_tuples[:config['REPORT_SIZE']])
    else:
        first_k = dict(result_tuples)
    for item in first_k:
        first_k[item]['count_perc'] = \
            first_k[item]['count'] / len(result_tuples) * 100
        first_k[item]['time_perc'] = \
            first_k[item]['time_sum'] / total_time * 100
        first_k[item]['time_med'] = \
            statistics.median(first_k[item]['median'])
        first_k[item].pop('median', None)

    return list(first_k.values())
