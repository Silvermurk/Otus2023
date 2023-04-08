# -*- coding: utf-8 -*-
"""
Simple HTTP server
Uses multiple threads, number specified in arguments
Accepts GET and HEAD HTTP methods
Only serves files from root folder

Allowed types:
.html | .js | .css |.jpeg | .jpg | .png | .gif | .swf
"""
import argparse
import logging
import sys

from pathlib import Path

from dz4.http_server import httpd


parser = argparse.ArgumentParser(
        prog='Http get / set server',
        description='Serves files from root folder',
        epilog='Some help text')
parser.add_argument('-p', '--port', default=8080)
parser.add_argument('-l', '--log', default='common.log')
parser.add_argument('-w', '--workers', default=4)
parser.add_argument('-r', '--root', default='./')
parser.add_argument('-a', '--address', default='localhost')


if parser.parse_args().workers < 0:
    logging.error('Number of workers must be more than 0')
    sys.exit()

if not Path(parser.parse_args().root).is_dir():
    logging.error('Document root must be a directory')
    sys.exit()

if parser.parse_args().port < 1:
    logging.error('Port must be grater than 1')
    sys.exit()


if __name__ == '__main__':
    httpd.serve_forever(parser.parse_args().address,
                        parser.parse_args().port,
                        Path(parser.parse_args().root).resolve(),
                        parser.parse_args().workers)
