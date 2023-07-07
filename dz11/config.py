"""
Config file for crawler
"""
# -*- coding: utf-8 -*-
YNEWS_MAIN_URL = "https://news.ycombinator.com/"
YNEWS_POST_URL_TEMPLATE = "https://news.ycombinator.com/item?id={id}"
FETCH_TIMEOUT = 10
MAX_RETRIES = 3
SEC_BETWEEN_RETRIES = 3
SENTINEL = "EXIT"
