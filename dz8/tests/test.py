# pylint:disable=no-member
"""
Tests for memcload module
"""
import math
import unittest

from dz8 import appsinstalled_pb2
from dz8.types import AppsInstalled, DeviceType


class TestMemcLoad(unittest.TestCase):
    """
    Main test class
    """

    def test_proto(self):
        """
        Protobuf test
        """
        sample = (
            "idfa\t1rfw452y52g2gq4g\t55.55\t42.42\t1423,43,567,3,7,23\n"
            "gaid\t7rfw452y52g2gq4g\t55.55\t42.42\t7423,424"
        )
        for line in sample.splitlines():
            _, _, lat, lon, raw_apps = line.strip().split("\t")
            apps = [int(a) for a in raw_apps.split(",") if a.isdigit()]
            lat, lon = float(lat), float(lon)
            user_apps = appsinstalled_pb2.UserApps()
            user_apps.lat = lat
            user_apps.lon = lon
            user_apps.apps.extend(apps)
            packed = user_apps.SerializeToString()
            unpacked = appsinstalled_pb2.UserApps()
            unpacked.ParseFromString(packed)
            self.assertEqual(user_apps, unpacked)

    def test_apps_installed_parse_valid(self):
        """
        Valid types memcload test
        """
        app_inst = AppsInstalled.from_raw("  idfa\t1\t0\t0\t1423,   ")
        self.assertIs(app_inst.dev_type, DeviceType.IDFA)
        self.assertEqual(app_inst.lat, 0)
        self.assertEqual(app_inst.lon, 0)
        self.assertEqual(len(app_inst.apps), 1)

        app_inst = AppsInstalled.from_raw("     gaid\t1\t-100"
                                          "\t-1000\t-1,0,1   ")
        self.assertIs(app_inst.dev_type, DeviceType.GAID)
        self.assertEqual(app_inst.lat, -100)
        self.assertEqual(app_inst.lon, -1000)
        self.assertEqual(len(app_inst.apps), 3)

        app_inst = AppsInstalled.from_raw("adid\t1\ta\tb\t      "
                                          "1,  2,  aaa, 42   ")
        self.assertIs(app_inst.dev_type, DeviceType.ADID)
        self.assertTrue(math.isnan(app_inst.lat))
        self.assertTrue(math.isnan(app_inst.lon))
        self.assertEqual(app_inst.apps, [1, 2, 42])

    def test_apps_installed_parse_invalid(self):
        """
        Invalid types memcload test
        """
        with self.assertRaises(ValueError):
            AppsInstalled.from_raw("idfa\t1\t0\t0")

        with self.assertRaises(ValueError):
            AppsInstalled.from_raw("xxxx\t1\t0\t0\t1,2,3")

        with self.assertRaises(ValueError):
            AppsInstalled.from_raw("gaid\t\t0\t0\t1,2,3")


if __name__ == "__main__":
    """
    Entry point
    """
    unittest.main()
