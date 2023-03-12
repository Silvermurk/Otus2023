# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
"""
General logger
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

LOG_FILE_MAX_SIZE = 1024 * 1024 * 1024
LOG_FILE_MAX_BACKUP_COUNT = 1

logger = logging.getLogger('common')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname).1s %(message)s',
                              '%d.%m.%Y %H:%M:%S')

console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


file_handler = RotatingFileHandler(filename=f'{os.getcwd()}/log/autotest.log',
                                   maxBytes=LOG_FILE_MAX_SIZE,
                                   backupCount=LOG_FILE_MAX_BACKUP_COUNT,
                                   encoding='utf-8',
                                   mode='w')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
