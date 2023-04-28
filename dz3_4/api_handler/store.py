# pylint:disable=broad-except

"""
Module for storeing results of score api and caching them
"""

import sqlite3
import logging
import json
import time
from contextlib import closing

import psycopg2
import sql


def get_store_connection(db_type: str):
    """
    Gets sqlite connection to store.db
    """
    if db_type == 'sqlite':
        return sqlite3.connect('store.db')
    if db_type == 'debug':
        return None
    if db_type == 'sql':
        try:
            connection = None
            retry_max = 3
            retry_count = 0
            while not connection:
                connection = sql.SQL(psycopg2.connect(host='localhost',
                                                      user='user',
                                                      password='password',
                                                      database='db_store'))
                retry_count += 1
                if retry_count > retry_max:
                    logging.error('Store DB %s is unreachable', db_type)
            return connection
        except psycopg2.OperationalError:
            logging.error('Connection to %s failed critically', db_type)
            return None
    else:
        logging.error('Invalid database type %s', db_type)
        return None


def get_cache_connection(db_type: str):
    """
    Gets sqlite connection to cache.db
    """
    if db_type == 'sqlite':
        return sqlite3.connect('cache.db')
    if db_type == 'debug':
        return {"Good_connection": 1}
    if db_type == 'sql':
        try:
            connection = None
            retry_max = 3
            retry_count = 0
            while not connection:
                connection = sql.SQL(psycopg2.connect(host='localhost',
                                                      user='user',
                                                      password='password',
                                                      database='db_cache'))
                retry_count += 1
                if retry_count > retry_max:
                    logging.error('Cache DB %s is unreachable', db_type)
            return connection
        except psycopg2.OperationalError:
            logging.error('Connection to %s failed critically', db_type)
            return None
    else:
        logging.error('Invalid database type %s', db_type)
        return None


class Store:
    """
    Main storage class for all DBs
    """

    def __init__(self, db_type: str = 'sqlite'):
        """
        initialize both connections beforehand
        """
        self.db_type = db_type
        self.conn_store = get_store_connection(db_type)
        self.conn_cache = get_cache_connection(db_type)

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
        if self.db_type == 'sqlite':
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
        Gets interests from DB if any
        """
        format_strings = ','.join(['%s'] * len(cids))
        query_text = 'SELECT client_id, GROUP_CONCAT(' \
                     'interest ORDER BY interest SEPARATOR " " ) ' \
                     'AS interests FROM interests GROUP BY ' \
                     f'client_id HAVING client_id IN (f{format_strings})'

        query_result = self.query(conn_class=self.conn_store,
                                  query=query_text)
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
        result = {}
        try:
            result = self.query(conn_class=self.conn_cache,
                                query=query_text,
                                params=[key])
        except Exception as exception:
            logging.warning("Cannot access to cache database: %s", exception)
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
