"""Unit tests for ConfigManager."""

import unittest
import tempfile
from pathlib import Path
from core.config import ConfigManager, DEFAULT_SETTINGS

class TestConfigManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "test_settings.json"
        self.config = ConfigManager(self.config_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_values(self):
        for k, v in DEFAULT_SETTINGS.items():
            self.assertEqual(self.config.get(k), v)

    def test_set_and_persist(self):
        self.config.set("low_speed_threshold_kbps", 1200)
        self.assertEqual(self.config.get("low_speed_threshold_kbps"), 1200)

        # Reload from disk
        reloaded = ConfigManager(self.config_path)
        self.assertEqual(reloaded.get("low_speed_threshold_kbps"), 1200)

    def test_all_settings(self):
        all_s = self.config.all()
        self.assertIsInstance(all_s, dict)
        self.assertIn("auto_start", all_s)

if __name__ == "__main__":
    unittest.main()
