"""
Module for score counting
"""
# pylint:disable=too-many-arguments

import hashlib
import json
import datetime


def get_score(store,
              phone,
              email,
              birthday=None,
              gender=None,
              first_name=None,
              last_name=None):
    """
    Gets score from cache base, if not there - calculates and adds to cache
    """
    key_parts = [
        first_name or "",
        last_name or "",
        datetime.datetime.strptime(str(birthday), '%d.%m.%Y').strftime("%Y%m%d"),
    ]
    key = "uid:" + hashlib.md5(("".join(key_parts)).encode('utf-8')).hexdigest()
    # Maybe we cached value already?
    score = store.cache_get(key) or 0
    if score:
        return score
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5
    store.cache_set(key, score,  60 * 60)
    return score


def get_interests(store, cid):
    """
    Get interests from DB and parse them
    """
    result = store.get(cid)
    return json.loads(result) if result else []
