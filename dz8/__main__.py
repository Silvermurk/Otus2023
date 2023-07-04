# pylint:disable=deprecated-module
# pylint:disable=no-member
# pylint:disable=broad-exception-caught
# pylint:disable=redefined-outer-name
# pylint:disable=pointless-string-statement

"""
Main module for memcload
"""
import glob
import gzip
import logging
import multiprocessing as mp
import os
import sys
import time

from collections import Counter
from functools import partial
from optparse import OptionParser
from pathlib import Path
from typing import List

import memcache

from . import appsinstalled_pb2
from .types import AppsInstalled, ProcessingStatus

NORMAL_ERR_RATE = 0.01
MEMCACHE_RETRY_NUMBER = 3
MEMCACHE_RETRY_TIMEOUT_SECONDS = 1
MEMCACHE_SOCKET_TIMEOUT_SECONDS = 3


def dot_rename(path):
    """
    Dot split os path to remove dots in path sirectorys
    """
    head, function = os.path.split(path)
    os.rename(path, os.path.join(head, "." + function))


def insert_appsinstalled(
        memcache_client: memcache.Client,
        appsinstalled: AppsInstalled,
        dry_run: bool = False,
        ) -> bool:
    """
    Memcache main method to insert data
    """
    user_apps = appsinstalled_pb2.UserApps()
    user_apps.lat = appsinstalled.lat
    user_apps.lon = appsinstalled.lon
    key = (appsinstalled.dev_type.value, appsinstalled.dev_id)
    user_apps.apps.extend(appsinstalled.apps)
    packed = user_apps.SerializeToString()

    if dry_run:
        logging.debug("%s -> %s", key, str(user_apps).replace("\n", " "))
        return True

    for _ in range(MEMCACHE_RETRY_NUMBER):
        try:
            # Use a tuple as key to write to specific Memcached server
            # https://github.com/linsomniac/python-memcached/blob/bad41222379102e3f18f6f2f7be3ee608de6fbff/memcache.py#L698
            memcache_client.set_multi(
                {key: packed},
                socket_timeout=MEMCACHE_SOCKET_TIMEOUT_SECONDS,
                )
        except Exception as exception:
            logging.exception("Cannot write to Memcache: %s", exception)
            return False
        else:
            return True
    time.sleep(MEMCACHE_RETRY_TIMEOUT_SECONDS)

    logging.error("Cannot write to Memcache. Server is down")
    return False


def process_line(
        raw_line: bytes, memcache_client: memcache.Client, dry: bool
        ) -> ProcessingStatus:
    """
    Process single line by memcache
    """

    line = raw_line.decode("utf-8").strip()
    if not line:
        return ProcessingStatus.SKIP

    try:
        appsinstalled = AppsInstalled.from_raw(line)
    except ValueError as exception:
        logging.error("Cannot parse line: %s", exception)
        return ProcessingStatus.ERROR

    all_ok: bool = insert_appsinstalled(memcache_client, appsinstalled, dry)
    if not all_ok:
        return ProcessingStatus.ERROR

    return ProcessingStatus.OK


def process_file(_function: str,
                 memcache_addresses: List[str],
                 dry: bool) -> str:
    """
    Process single file by memcache
    """
    worker = mp.current_process()
    logging.info("[%s] Processing %s", worker.name, _function)

    memcache_client = memcache.Client(
        memcache_addresses,
        socket_timeout=3,
        dead_retry=MEMCACHE_RETRY_TIMEOUT_SECONDS,
        )
    with gzip.open(_function) as filedir:
        job = partial(process_line, memcache_client=memcache_client, dry=dry)
        statuses = Counter(map(job, filedir))

    all_ok = statuses[ProcessingStatus.OK]
    errors = statuses[ProcessingStatus.ERROR]
    processed = all_ok + errors

    err_rate = float(errors) / processed if processed else 1.0

    if err_rate < NORMAL_ERR_RATE:
        logging.info(
            "%s [%s] Acceptable error rate: %s.\n"
            "Successfull load", worker.name, _function, err_rate
            )
    else:
        logging.error(
            "[%s] [%s] High error rate: "
            "{%s} > {%s}. Failed load",
            worker.name, _function, err_rate, NORMAL_ERR_RATE
            )
    return _function


def main(options):
    """
    Entry point
    """
    memcache_addresses: List[str] = [
        options.idfa,
        options.gaid,
        options.adid,
        options.dvid,
        ]

    job = partial(
        process_file, memcache_addresses=memcache_addresses, dry=options.dry
        )

    files = sorted(
        glob.glob(options.pattern), key=lambda file: Path(file).name
        )

    with mp.Pool() as pool:
        for processed_file in pool.imap(job, files):
            worker = mp.current_process()
            logging.info("[%s] Renaming {%s}", worker.name, processed_file)
            dot_rename(processed_file)


if __name__ == "__main__":
    """
    Starts here
    """
    op = OptionParser()

    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("--dry", action="store_true", default=False)
    op.add_option("--loglevel", action="store", default="INFO")
    op.add_option(
        "--pattern", action="store", default="/data/appsinstalled/*.tsv.gz"
        )
    op.add_option("--idfa", action="store", default="127.0.0.1:33013")
    op.add_option("--gaid", action="store", default="127.0.0.1:33014")
    op.add_option("--adid", action="store", default="127.0.0.1:33015")
    op.add_option("--dvid", action="store", default="127.0.0.1:33016")

    (opts, args) = op.parse_args()

    logging.basicConfig(
        filename=opts.log,
        level=getattr(logging, opts.loglevel, logging.INFO),
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
        )

    logging.info("Memc loader started with options: %s", opts)

    try:
        main(opts)
    except Exception as exception:
        logging.exception("Unexpected error: %s", exception)
        sys.exit(1)
