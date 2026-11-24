"""Unit tests for AlertManager."""

import unittest
from pathlib import Path
import tempfile
from core.config import ConfigManager
from core.alert_manager import AlertManager

class TestAlertManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "test_settings.json"
        self.config = ConfigManager(self.config_path)
        self.alerts_received = []

    def tearDown(self):
        self.temp_dir.cleanup()

    def _alert_callback(self, title, msg):
        self.alerts_received.append((title, msg))

    def test_alert_disabled(self):
        self.config.set("low_speed_alert_enabled", False)
        manager = AlertManager(self.config, self._alert_callback)
        triggered = manager.check_speed(100)  # Very low speed
        self.assertFalse(triggered)
        self.assertEqual(len(self.alerts_received), 0)

    def test_alert_duration_trigger(self):
        self.config.set("low_speed_alert_enabled", True)
        self.config.set("low_speed_threshold_kbps", 500)
        self.config.set("low_speed_duration_seconds", 0.0)  # Immediate trigger for test

        manager = AlertManager(self.config, self._alert_callback)
        # 100 KB/s in Bps
        triggered = manager.check_speed(100 * 1024)
        self.assertTrue(triggered)
        self.assertEqual(len(self.alerts_received), 1)

    def test_speed_above_threshold_resets(self):
        self.config.set("low_speed_alert_enabled", True)
        self.config.set("low_speed_threshold_kbps", 500)
        manager = AlertManager(self.config, self._alert_callback)

        manager.check_speed(100 * 1024)
        self.assertIsNotNone(manager.low_speed_start_time)

        # High speed should reset
        manager.check_speed(1000 * 1024)
        self.assertIsNone(manager.low_speed_start_time)

if __name__ == "__main__":
    unittest.main()
