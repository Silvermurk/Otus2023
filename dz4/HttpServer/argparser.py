# -*- coding: utf-8 -*-
from argparse import ArgumentParser


def parse_args():
    """
    Parses command line arguments
    """
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("-r", "--root", help="Document root.", required=True)
    parser.add_argument(
        "-w",
        "--workers",
        help="Number of workers [Default: 4].",
        default=4,
        type=int)
    parser.add_argument(
        "-a",
        "--address",
        help="Server address [Default: 127.0.0.1]",
        default="127.0.0.1")
    parser.add_argument(
        "-p",
        "--port",
        help="Listen port [Default: 8080]",
        default=8080,
        type=int)
    return parser.parse_args()