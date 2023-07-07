# -*- coding: utf-8 -*-
"""
Provides fetching url, saving url content to file, counting of ready links
"""
import os
import logging as log
import aiohttp
import aiofiles
import asyncio

import async_timeout

from dz11.config import SEC_BETWEEN_RETRIES, MAX_RETRIES


class Fetcher:
    """
    Provides fetching url, saving url content to file, counting of ready links
    """

    def __init__(self, store_dir: str):
        """
        Initializes a Fetcher object with a store directory path, and sets up a client session and a lock.
        """
        self.__posts_saved = 0
        self.__comments_links_saved = 0
        self.store_dir = store_dir
        self.lock = asyncio.Lock()
        self.session = aiohttp.ClientSession()

    async def __aenter__(self):
        """
        Acquires the lock for the Fetcher object.
        """
        await self.lock.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """
        Releases the lock for the Fetcher object.
        """
        self.lock.release()

    async def close(self):
        """
        Clean up the client session when we're done using it
        """
        await self.session.close()

    @property
    async def posts_saved(self):
        """
        Returns the number of posts saved.
        """
        async with self:
            return self.__posts_saved

    async def inc_posts_saved(self):
        """
        Increments the number of posts saved.
        """
        async with self:
            self.__posts_saved += 1

    @property
    async def comments_links_saved(self):
        """
        Returns the number of comments links saved.
        """
        async with self:
            return self.__comments_links_saved

    async def inc_comments_links_saved(self):
        """
        Increments the number of comments links saved.
        """
        async with self:
            self.__comments_links_saved += 1

    async def load_and_save(self, url: str, post_id: int, link_id: int):
        """
        Fetches the content of a given URL, saves it to a file in the store directory, and increments the count of
        posts or comments links saved.
        """
        try:
            content = await self.fetch(url, need_bytes=True)
            filepath = self.get_path(link_id, post_id)
            await self.write_to_file(filepath, content)

            if link_id > 0:
                await self.inc_comments_links_saved()
            else:
                await self.inc_posts_saved()

            log.debug("Fetched and saved link %s for post %s: %s", link_id, post_id, url)
        except aiohttp.ClientError as error:
            log.exception("Failed to load and save %s due to %s", url, error)

    async def fetch(self,
                    url: str,
                    need_bytes: bool = True,
                    retry: int = 0) -> (bytes, str):
        """
        Fetches the content of a given URL using aiohttp and returns it as bytes or text.
        """
        try:
            async with async_timeout.timeout(10):
                async with self.session.get(url) as response:
                    if need_bytes:
                        return await response.read()
                    else:
                        return await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            if retry < MAX_RETRIES:
                log.debug("Failed to fetch %s, retry %s in %s seconds", url, retry + 1, SEC_BETWEEN_RETRIES)
                await asyncio.sleep(SEC_BETWEEN_RETRIES)
                return await self.fetch(url, need_bytes, retry + 1)
            else:
                log.debug("Failed to fetch %s", url)

    async def write_to_file(self, path: str, content: bytes):
        """
        Writes the content of a given URL to a file with error handling.
        """
        try:
            async with aiofiles.open(path, mode="wb") as f:
                await f.write(content)
        except Exception as exception:
            log.exception("Failed to write to file %s due to %s", path, exception)

    def get_path(self, link_id: int, post_id: int) -> str:
        """
        Returns the file path for a given comments link ID and post ID.
        """
        if link_id > 0:
            filename = "{}_{}.html".format(post_id, link_id)
        else:
            filename = "{}.html".format(post_id)

        return os.path.join(self.store_dir, filename)