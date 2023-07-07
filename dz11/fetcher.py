# -*- coding: utf-8 -*-
import os
import logging as log
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse

import aiohttp

from bs4 import BeautifulSoup

from dz11.config import YNEWS_POST_URL_TEMPLATE, YNEWS_MAIN_URL, FETCH_TIMEOUT, SENTINEL
from dz11.fetcher import Fetcher


class Crawler:
    """
    Async web crawler for fetching top posts from news.ycombinator.com
    """

    def __init__(self, store_dir: str, num_posts: int, logfile: str):
        self.store_dir = store_dir
        self.num_posts = num_posts
        self.logfile = logfile
        self.fetcher = Fetcher(store_dir)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.fetcher.close()

    async def start(self):
        """
        Start the crawler and wait for it to finish
        """
        setup_logging(self.logfile)
        async with aiohttp.ClientSession() as session:
            self.fetcher.session = session
            try:
                await self.crawl_top_posts(session, self.fetcher, self.num_posts)
            except Exception as e:
                log.error(f"An error occurred while crawling: {e}")

        await self.fetcher.write_to_file(os.path.join(self.store_dir, SENTINEL), b"")

    async def crawl_post_links(self, session: aiohttp.ClientSession, post_id: int):
        """
        Fetch the links to the comments of a post and save them to files
        """
        links = await self.fetch_post_links(session, post_id)
        for i, link in enumerate(links):
            try:
                await self.fetcher.load_and_save(YNEWS_MAIN_URL + link, post_id, i + 1)
            except Exception as e:
                log.error(f"An error occurred while fetching post {post_id} link {i + 1}: {e}")

    async def crawl_top_posts(self, session: aiohttp.ClientSession, fetcher: Fetcher, num_posts: int):
        """
        Fetch the top N posts and the links to their comments and save them to files
        """
        async with session.get(YNEWS_MAIN_URL, timeout=FETCH_TIMEOUT) as response:
            content = await response.text()
            soup = BeautifulSoup(content, "html.parser")
            links = soup.select("a.storylink")

            for i, link in enumerate(links[:num_posts]):
                post_id = int(urlparse(link["href"]).query.split("=")[1])
                try:
                    await self.fetcher.load_and_save(link["href"], post_id, 0)
                    await self.crawl_post_links(session, post_id)
                except Exception as e:
                    log.error(f"An error occurred while fetching post {post_id}: {e}")

    @staticmethod
    async def fetch_post_links(session: aiohttp.ClientSession, post_id: int) -> list[str]:
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
        except aiohttp.ClientError as e:
            log.debug(f"Failed to fetch post {post_id}: {e}")
            return []


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