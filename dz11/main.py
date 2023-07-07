# -*- coding: utf-8 -*-
# pylint:disable=broad-exception-caught
"""
This module implements an async web crawler for fetching top posts from news.ycombinator.com.
"""

import argparse
import asyncio

from dz11.crawler import Crawler


async def main(store_dir: str, num_posts: int, logfile: str):
    """
    Start the crawler and wait for it to finish
    """
    crawler = Crawler(store_dir, num_posts, logfile)
    if num_posts <= 0:
        raise ValueError("num_posts must be a positive integer")
    await crawler.start()


if __name__ == "__main__":
    """
    Entry point
    """
    parser = argparse.ArgumentParser(description="Async crawler for news.ycombinator.com")
    parser.add_argument("store_dir", type=str, help="directory to store the fetched content")
    parser.add_argument("num_posts", type=int, help="number of top posts to fetch")
    parser.add_argument("--logfile", type=str, default="crawler.log", help="path to the log file")
    args = parser.parse_args()

    try:
        asyncio.run(main(args.store_dir, args.num_posts, args.logfile))
    except Exception as exception:
        print(f"Error: {exception}")
