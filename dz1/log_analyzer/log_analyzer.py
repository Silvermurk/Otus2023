#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint:disable=broad-except
# https://github.com/PyCQA/pylint/issues/214

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip
#                     '[$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for"
#                     '"$http_X_REQUEST_ID" "$http_X_RB_USER" $request_time';

"""
Main log analyzer module for translateing nginx logs into tabled html reports
using jquery.tablesorter.min.js
Runs fs-utils to work with files
Runs report_creator to generate reports based on config
"""

import argparse
import datetime
import signal
import sys

from dz1.log_analyzer.fs_utils import (load_external_config,
                                       check_for_logs,
                                       check_for_reports, create_and_copy_report)
from dz1.log_analyzer.log import logger
from dz1.log_analyzer.report_creator import create_report

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./output",
    "LOG_DIR": "./input"
    }

parser = argparse.ArgumentParser(
    prog='LogAnalyzer',
    description='Translates logs to html table',
    epilog='Some help text')
parser.add_argument('-c', '--config')


def signal_handler(signum, frame):
    """
    Method that stops code execution on signal input
    :param signum: Signal integer number
    :param frame: Signal origin system frame
    :return: None
    """
    logger.exception('Signal recived %s, frame %s', signum, frame)
    sys.exit(1)


def main():
    """
    Main programm method - translates logs from nginx to reports using a
    built in or an external config
    :return: None
    """
    signal.signal(signal.SIGINT, signal_handler)
    load_external_config(parser.parse_args(), config)

    latest_logs = check_for_logs(config)
    if not latest_logs:
        sys.exit('No logs to analyze')

    latest_reports = check_for_reports(config)
    if not latest_reports:
        sys.exit('Exception on loading reports dir')

    if max(latest_reports) == max(latest_logs):
        logger.info('Latest logs for %s are analyzed already', latest_reports)
        sys.exit('No new logs to analyze')

    first_k = []
    try:
        first_k = create_report(config, latest_logs[max(latest_logs)])
    except Exception as exception:
        logger.exception('Unknown error %s', exception)

    latest_date = datetime.datetime.strptime(
                   latest_logs[max(latest_logs)].split('.')[1][4:],
                   '%Y%m%d').date()
    filename = 'report-' + f'{latest_date.year}.' \
                           f'{latest_date.month:02d}.' \
                           f'{latest_date.day:02d}'

    create_and_copy_report(filename, config, first_k)


if __name__ == "__main__":
    main()
