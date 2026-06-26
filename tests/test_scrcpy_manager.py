import unittest

from scrcpy_manager.config import ScrcpyManagerConfig
from scrcpy_manager.device_pool import DevicePool


class DevicePoolTests(unittest.TestCase):
    def test_acquire_and_release(self):
        pool = DevicePool(["d1", "d2"])
        first = pool.get_idle_device()
        second = pool.get_idle_device()
        self.assertNotEqual(first, second)
        pool.release_device(first)
        third = pool.get_idle_device()
        self.assertEqual(third, first)


class ConfigTests(unittest.TestCase):
    def test_load_example_config(self):
        config = ScrcpyManagerConfig.load("config/config.ini.example")
        self.assertEqual(config.system.domain_id, "southnotary")
        self.assertIn("Yingke", config.target_apps)


if __name__ == "__main__":
    unittest.main()
