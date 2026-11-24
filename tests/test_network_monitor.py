"""Unit tests for NetworkMonitor and formatting helpers."""

import unittest
from core.network_monitor import (
    format_bytes, format_speed, format_speed_compact, NetworkMonitor
)

class TestNetworkMonitor(unittest.TestCase):

    def test_format_bytes(self):
        self.assertEqual(format_bytes(500), "500 B")
        self.assertEqual(format_bytes(1024), "1.0 KB")
        self.assertEqual(format_bytes(1024 * 1024 * 5), "5.00 MB")
        self.assertEqual(format_bytes(1024 ** 3 * 2.5), "2.50 GB")

    def test_format_speed(self):
        self.assertEqual(format_speed(250), "250 B/s")
        self.assertEqual(format_speed(1024 * 50), "50.0 KB/s")
        self.assertEqual(format_speed(1024 ** 2 * 12.3), "12.30 MB/s")

    def test_format_speed_compact(self):
        self.assertEqual(format_speed_compact(400), "400B")
        self.assertEqual(format_speed_compact(1024 * 15), "15K")
        self.assertEqual(format_speed_compact(1024 * 5), "5.0K")
        self.assertEqual(format_speed_compact(1024 ** 2 * 3.4), "3.4M")
        self.assertEqual(format_speed_compact(1024 ** 2 * 45), "45M")

    def test_monitor_update(self):
        monitor = NetworkMonitor(interface="All Interfaces")
        result = monitor.update()
        self.assertIn("download_speed", result)
        self.assertIn("upload_speed", result)
        self.assertIn("download_str", result)
        self.assertIn("upload_str", result)
        self.assertIn("session_recv", result)
        self.assertIn("session_sent", result)

    def test_interfaces_and_wifi(self):
        ifaces = NetworkMonitor.get_available_interfaces()
        self.assertIsInstance(ifaces, list)
        self.assertIn("All Interfaces", ifaces)

        wifi_info = NetworkMonitor.get_wifi_and_connection_info()
        self.assertIn("is_wifi", wifi_info)
        self.assertIn("local_ip", wifi_info)
        self.assertIn("state", wifi_info)

if __name__ == "__main__":
    unittest.main()
