# -*- coding: utf-8 -*-
# pylint:disable=broad-except

"""
Module designed to work with filesystem for log analyzer
"""

import json
import os
import shutil
from argparse import Namespace

from datetime import datetime

from dz1.log_analyzer.log import logger


def load_external_config(args: Namespace, config: dict) -> dict:
    """
    :param args: ArgumentParser-like Namespace that contains parsed external
    arguments
    :param config: Dictionary containing config data from main script
    :return: Merged config data from config and external file, if it is present
    """
    if 'config' in args:
        with open(os.getcwd() + f'/{args.config}',
                  encoding='utf-8') as file:
            config.update(json.load(file))
    return config


def check_for_logs(config: dict) -> dict or None:
    """
    Method for reading log files from directory, specified in config
    :param config: Dictionary containing config data from main script
    :return: Dictionary of files if any present, None if bad path or no logs
    """
    try:
        files = os.listdir(config['LOG_DIR'])
    except Exception as exception:
        logger.exception('Exception on listing log dir: %s', exception)
        return None

    log_files = dict()
    for file in files:
        if not file.startswith('nginx-access-ui'):
            continue
        file_date = datetime.strptime(file.split('.')[1][4:], '%Y%m%d').date()
        log_files[file_date] = file

    if len(log_files) == 0:
        logger.info('No files to analyze')
        return None
    return log_files


def check_for_reports(config: dict) -> dict or None:
    """
        Method for checking report files from directory, specified in config
        :param config: Dictionary containing config data from main script
        :return: Dictionary of files if any present, None if bad path or no logs
        """
    try:
        files = os.listdir(config['REPORT_DIR'])
    except Exception as exception:
        logger.exception('Exception on listing log dir: %s', exception)
        return None

    report_files = dict()
    for file in files:
        if not file.startswith('report-'):
            continue
        file_date = datetime.strptime(file.split('-')[1][:-5],
                                      '%Y.%m.%d').date()
        report_files[file_date] = file
    return report_files


def create_and_copy_report(filename: str,
                           config: dict,
                           first_k: list) -> None:
    """
    Method that takes sample report.html, modifies it with new data
    and saves to report folder with data when it was analyzed
    :param filename: Name based on pattern 'report-YYY-MM-DD.html'
    :param config: Dictionary containing config data from main script
    :param first_k: list of Lines of logs, that report_creator produced
    :return: None
    """
    shutil.copy(f'{os.getcwd()}/jquery/report.html',
                f'{os.getcwd()}/{config["REPORT_DIR"]}/{filename}.html')

    with open(f'{os.getcwd()}/{config["REPORT_DIR"]}/{filename}.html',
              'r',
              encoding='utf-8') as file:
        file_data = file.read()
    file_data = file_data.replace('$table_json', str(first_k))
    with open(f'{os.getcwd()}/{config["REPORT_DIR"]}/{filename}.html',
              'w') as file:
        file.write(file_data)
