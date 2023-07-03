"""
Types for protobuf and memcload
"""

import logging

from enum import Enum
from typing import List, NamedTuple


class DeviceType(Enum):
    """
    Types class by thread
    """
    IDFA = 0
    GAID = 1
    ADID = 2
    DVID = 3

    def __str__(self):
        return self.name.lower()


class ProcessingStatus(Enum):
    """
    Results class
    """
    OK = 1
    ERROR = -1
    SKIP = 0


class AppsInstalled(NamedTuple):
    """
    Tuple types class
    """
    dev_type: DeviceType
    dev_id: str
    lat: float
    lon: float
    apps: List[int]

    @classmethod
    def from_raw(cls, line: str) -> "AppsInstalled":
        """
        Load raw data
        """
        line_parts = line.strip().split("\t")

        if len(line_parts) < 5:
            raise ValueError("Invalid format.")

        raw_dev_type, dev_id, raw_lat, raw_lon, raw_apps = line_parts

        try:
            raw_dev_type = raw_dev_type.strip().upper()
            dev_type = DeviceType[raw_dev_type]
        except KeyError:
            raise KeyError("Unknown device type: {%s}", raw_dev_type)

        if not dev_id:
            raise ValueError("Device ID missed.")

        try:
            apps = [int(a.strip()) for a in raw_apps.split(",")]
        except ValueError:
            apps = [
                int(a.strip())
                for a in raw_apps.split(",")
                if a.strip().isdigit()
            ]
            logging.info("Not all user apps are digits: `%s`", line)

        try:
            lat, lon = float(raw_lat), float(raw_lon)
        except ValueError:
            lat = lon = float("nan")
            logging.info("Invalid geo coords: `%s`",line)

        return cls(dev_type, dev_id, lat, lon, apps)
