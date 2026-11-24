"""Comprehensive UI stability and interaction tests using PyQt6 QTest."""

import os
import unittest
import tempfile
from pathlib import Path

# Run in offscreen mode for reliable headless execution
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

from core.config import ConfigManager
from core.database import DatabaseManager
from core.network_monitor import NetworkMonitor
from core.startup import StartupManager
from core.speedtest import SpeedTestWorker
from ui.main_window import MainWindow

# Ensure single QApplication instance across test runner
app = QApplication.instance()
if app is None:
    app = QApplication([])

class TestUIStability(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "test_settings.json"
        self.db_path = Path(self.temp_dir.name) / "test_history.db"

        self.config = ConfigManager(self.config_path)
        self.db = DatabaseManager(self.db_path)
        self.monitor = NetworkMonitor(interface="All Interfaces")
        self.startup = StartupManager()

        self.window = MainWindow(
            config=self.config,
            db=self.db,
            monitor=self.monitor,
            startup=self.startup
        )

    def tearDown(self):
        self.window.timer.stop()
        self.window.proc_timer.stop()
        if self.window.speedtest_worker and self.window.speedtest_worker.isRunning():
            self.window.speedtest_worker.cancel()
            self.window.speedtest_worker.wait(500)
        self.window.close()
        self.temp_dir.cleanup()

    def test_window_initialization(self):
        self.assertIn("Yaze", self.window.windowTitle())
        self.assertIsNotNone(self.window.speed_graph)
        self.assertIsNotNone(self.window.tray_icon)
        self.assertEqual(self.window.tabs.count(), 5)

    def test_tab_navigation(self):
        """Verify seamless switching through all tabs without crashes."""
        tab_names = ["Overview", "Applications", "Analytics & History", "Speed Test", "Settings"]
        for idx, name in enumerate(tab_names):
            self.window.tabs.setCurrentIndex(idx)
            self.assertEqual(self.window.tabs.tabText(idx), name)
            self.assertEqual(self.window.tabs.currentIndex(), idx)

    def test_overview_tick_and_cards(self):
        """Simulate timer tick and verify metrics update."""
        self.window._on_tick()
        self.assertNotEqual(self.window.card_down_speed["value"].text(), "")
        self.assertNotEqual(self.window.card_up_speed["value"].text(), "")

    def test_graph_widget_interaction(self):
        """Verify adding data points to graph, painting, and peak reset."""
        self.window.speed_graph.add_data_point(1024 * 500, 1024 * 200)
        self.assertGreater(self.window.speed_graph.current_down, 0)
        self.window.speed_graph.reset_peaks()
        self.assertEqual(self.window.speed_graph.peak_down, self.window.speed_graph.current_down)

    def test_applications_table_filter(self):
        """Test process monitoring table population and filtering."""
        self.window.tabs.setCurrentIndex(1)  # Applications tab
        self.window._on_process_tick()

        # Type filter in search box
        self.window.proc_search.setText("py")
        self.window._filter_process_table()
        self.assertIsNotNone(self.window.proc_table)

        # Clear search filter
        self.window.proc_search.setText("")
        self.window._filter_process_table()

    def test_analytics_refresh(self):
        """Test analytics calculation and table population."""
        self.db.record_delta_traffic(bytes_recv=1024 * 1024 * 25, bytes_sent=1024 * 1024 * 5)
        self.db.record_speed_test(download_mbps=85.0, upload_mbps=30.0, ping_ms=12.5)
        self.window._refresh_analytics()

        self.assertIn("MB", self.window.all_time_down["value"].text())
        self.assertGreater(self.window.weekly_table.rowCount(), 0)
        self.assertGreater(self.window.speed_history_table.rowCount(), 0)

    def test_speedtest_ui_controls(self):
        """Test speed test start, partial signals, and cancellation."""
        self.window.tabs.setCurrentIndex(3)  # Speed Test Tab

        # Simulate partial progress callbacks
        self.window._on_speedtest_partial("ping", 15.4)
        self.assertEqual(self.window.st_ping_card["value"].text(), "15.4 ms")

        self.window._on_speedtest_partial("download", 120.5)
        self.assertEqual(self.window.st_down_card["value"].text(), "120.50 Mbps")

        self.window._on_speedtest_partial("upload", 45.2)
        self.assertEqual(self.window.st_up_card["value"].text(), "45.20 Mbps")

        # Test finish handler
        self.window._on_speedtest_finished({
            "download_mbps": 120.5,
            "upload_mbps": 45.2,
            "ping_ms": 15.4,
            "server": "Cloudflare Test"
        })
        self.assertEqual(self.window.st_progress.value(), 100)
        self.assertTrue(self.window.btn_start_test.isEnabled())

        # Test error handler
        self.window._on_speedtest_error("Network timeout")
        self.assertEqual(self.window.st_status_lbl.text(), "Network timeout")

    def test_settings_controls(self):
        """Test modifying settings toggles and spinboxes."""
        self.window.tabs.setCurrentIndex(4)  # Settings tab
        self.window.chk_low_speed.setChecked(True)
        self.assertTrue(self.config.get("low_speed_alert_enabled"))

        self.window.spin_threshold.setValue(800)
        self.assertEqual(self.config.get("low_speed_threshold_kbps"), 800)

        self.window.spin_duration.setValue(20)
        self.assertEqual(self.config.get("low_speed_duration_seconds"), 20)

        # Test interface combo
        self.window.combo_interfaces.setCurrentIndex(0)
        self.assertEqual(self.monitor.interface, "All Interfaces")

    def test_close_event_minimizes_to_tray(self):
        """Test that clicking close hides window instead of quitting."""
        self.config.set("minimize_to_tray_on_close", True)
        self.window.show()

        event = QCloseEvent()
        self.window.closeEvent(event)

        # Close should be ignored (intercepted)
        self.assertFalse(event.isAccepted())
        # Window should now be hidden
        self.assertFalse(self.window.isVisible())

    def test_tray_menu_and_icon_rendering(self):
        """Verify dynamic tray icon generation and menu toggling."""
        # Test varying speed scales
        speeds_to_test = [
            (0, 0),
            (1024 * 50, 1024 * 10),
            (1024 * 1024 * 4.2, 1024 * 850),
            (1024 * 1024 * 1024 * 1.5, 1024 * 1024 * 250)
        ]
        for down, up in speeds_to_test:
            self.window.tray_icon.update_tray_icon(down, up)
            self.assertFalse(self.window.tray_icon.icon().isNull())

        # Test toggle window from tray
        self.window.hide()
        self.window.tray_icon.toggle_window()
        self.assertTrue(self.window.isVisible())

        self.window.tray_icon.toggle_window()
        self.assertFalse(self.window.isVisible())

    def test_force_quit_flow(self):
        """Verify force_quit sets flag and stops timers."""
        self.window.force_quit()
        self.assertTrue(self.window._is_force_quitting)
        self.assertFalse(self.window.timer.isActive())

if __name__ == "__main__":
    unittest.main()
