# -*- coding: utf-8 -*-
import os
import logging as log
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse

import aiohttp

from bs4 import BeautifulSoup

from dz11.config import YNEWS_POST_URL_TEMPLATE, YNEWS_MAIN_URL, FETCH_TIMEOUT, SENTINEL
from dz11.fetcher import Fetcher


async def fetch_post_links(session: aiohttp.ClientSession,
                           post_id: int) -> list[str]:
    """
    Fetch the HTML content of a post and return the links to its comments
    """
    url = YNEWS_POST_URL_TEMPLATE.format(id=post_id)
    try:
        async with session.get(url, timeout=FETCH_TIMEOUT) as response:
            content = await response.text()
            soup = BeautifulSoup(content, "html.parser")
            links = soup.select("a[href*=item?id=]")
            return [link["href"] for link in links]
    except aiohttp.ClientError:
        log.debug("Failed to fetch post {}".format(post_id))
        return []


async def crawl_post_links(session: aiohttp.ClientSession,
                           fetcher: Fetcher,
                           post_id: int):
    """
    Fetch the links to the comments of a post and save them to files
    """
    links = await fetch_post_links(session, post_id)
    for i, link in enumerate(links):
        await fetcher.load_and_save(YNEWS_MAIN_URL + link, post_id, i + 1)


async def crawl_top_posts(session: aiohttp.ClientSession,
                          fetcher: Fetcher,
                          num_posts: int):
    """
    Fetch the top N posts and the links to their comments and save them to files
    """
    async with session.get(YNEWS_MAIN_URL, timeout=FETCH_TIMEOUT) as response:
        content = await response.text()
        soup = BeautifulSoup(content, "html.parser")
        links = soup.select("a.storylink")

        for i, link in enumerate(links[:num_posts]):
            post_id = int(urlparse(link["href"]).query.split("=")[1])
            await fetcher.load_and_save(link["href"], post_id, 0)
            await crawl_post_links(session, fetcher, post_id)


async def crawl(fetcher: Fetcher, num_posts: int):
    """
    Start the crawler and wait for it to finish
    """
    async with aiohttp.ClientSession() as session:
        fetcher.session = session
        await crawl_top_posts(session, fetcher, num_posts)

    await fetcher.write_to_file(os.path.join(fetcher.store_dir, SENTINEL), b"")


def setup_logging(logfile: str):
    """
    Configure the logger to write to a file and stdout
    """
    log.basicConfig(
        level=log.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[
            RotatingFileHandler(logfile, maxBytes=10 * 1024 * 1024, backupCount=5),
            log.StreamHandler()
            ]
        )
