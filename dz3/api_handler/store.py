# pylint:disable=broad-except

"""
Module for storeing results of score api and caching them
"""

import sqlite3
import logging
import json
import time
from contextlib import closing


def get_store_connection():
    """
    Gets sqlite connection to store.db
    """
    return sqlite3.connect('store.db')


def get_cache_connection():
    """
    Gets sqlite connection to cache.db
    """
    return sqlite3.connect('cache.db')


class Store:
    """
    Main storage class for all DBs
    """

    def __init__(self):
        """
        initialize both connections beforehand
        """
        self.conn_store = get_store_connection()
        self.conn_cache = get_cache_connection()

    def create_store_tables(self, table_name, fields):
        """
        Creates tables in sore DB if none are found
        """
        query = f'CREATE TABLE {table_name}({fields})'
        self.conn_store.execute(query)

    def create_cache_tables(self, table_name, fields):
        """
        Creates tables in cache DB if none are found
        """
        query = f'CREATE TABLE {table_name}({fields})'
        self.conn_cache.execute(query)

    def check_or_create_tables(self):
        """
        Checks master table for inner ones and creates if need be
        """
        tables_store = list(self.conn_store.execute(
            'SELECT name FROM sqlite_master '
            'WHERE type="table";'))
        tables_cache = list(self.conn_store.execute(
            'SELECT name FROM sqlite_master '
            'WHERE type="table";'))
        if len(tables_store) == 0 or ('interests',) not in tables_store:
            self.create_store_tables('interests',
                                     'client_id, interest')
        if len(tables_store) == 0 or ('cache_score',) not in tables_store:
            self.create_store_tables('cache_score',
                                     'key_score, '
                                     'score, '
                                     'timeout')
        if len(tables_cache) == 0 or ('interests',) not in tables_store:
            self.create_cache_tables('interests',
                                     'client_id, interest')
        if len(tables_cache) == 0 or ('cache_score',) not in tables_store:
            self.create_cache_tables('cache_score',
                                     'key_score, '
                                     'score, '
                                     'timeout')

    def query(self, conn_class, query, params=()):
        """
        Main query class for all SQL-based stuff
        """
        self.check_or_create_tables()
        try:
            with closing(conn_class.cursor()) as cursor:
                cursor.execute(query, params)
                return self.dictfetchall(cursor)
        except Exception as exception:
            logging.warning("Query %s error: %s", query, exception)
            raise exception

    def get(self, cids):
        """
        Gets interests from DB if any there
        """
        format_strings = ','.join(['%s'] * len(cids))
        query_text = 'SELECT client_id, GROUP_CONCAT(' \
                     'interest ORDER BY interest SEPARATOR " " ) ' \
                     'AS interests FROM interests GROUP BY ' \
                     f'client_id HAVING client_id IN (f{format_strings})'

        query_result = self.query(conn_class=self.conn_store, query=query_text)
        return json.dumps(query_result)

    @staticmethod
    def dictfetchall(cursor):
        """
        Uses Fetchall method and translates it to dict
        """
        desc = cursor.description
        return [
            dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
            ]

    def cache_get(self, key):
        """
        Get method for cache DB
        """
        query_text = 'SELECT score, timeout ' \
                     'FROM cache_score WHERE key_score= ?'
        try:
            result = self.query(conn_class=self.conn_cache,
                                query=query_text,
                                params=[key])
        except Exception as exception:
            raise ConnectionError(
                f"Cannot access to cache database: {exception}",
                ) from exception
        if len(result) != 0:
            if int(result[0][2]) < time.time():
                query_text = 'DELETE FROM cache_score WHERE key_score= ? '
                self.query(conn_class=self.conn_cache,
                           query=query_text,
                           params=[key])
                return None
            return query_text[0][1]
        return None

    def cache_set(self, key, score, timeout=60 * 60):
        """
        Set method for cache DB
        """
        try:
            query_text = 'INSERT INTO ' \
                         'cache_score(key_score, score, timeout) ' \
                         'VALUES (?, ?, ?);'
            self.query(conn_class=self.conn_cache,
                       query=query_text,
                       params=(key, score, time.time() + timeout))
        except Exception as exception:
            logging.warning("Cannot save to cache database: %s", exception)
