"""Unit tests for DatabaseManager."""

import unittest
import tempfile
import datetime
from pathlib import Path
from core.database import DatabaseManager

class TestDatabaseManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_history.db"
        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_record_and_get_today_usage(self):
        self.db.record_delta_traffic(bytes_recv=1024, bytes_sent=512)
        recv, sent = self.db.get_today_usage()
        self.assertEqual(recv, 1024)
        self.assertEqual(sent, 512)

        # Record more
        self.db.record_delta_traffic(bytes_recv=2048, bytes_sent=1024)
        recv, sent = self.db.get_today_usage()
        self.assertEqual(recv, 3072)
        self.assertEqual(sent, 1536)

    def test_weekly_usage(self):
        self.db.record_delta_traffic(1000, 500)
        weekly = self.db.get_weekly_usage()
        self.assertEqual(len(weekly), 7)
        today_str = datetime.date.today().isoformat()
        today_entry = [w for w in weekly if w["date"] == today_str][0]
        self.assertEqual(today_entry["bytes_recv"], 1000)
        self.assertEqual(today_entry["bytes_sent"], 500)

    def test_speed_test_record_and_retrieve(self):
        self.db.record_speed_test(download_mbps=78.5, upload_mbps=25.2, ping_ms=14.3, server="Cloudflare")
        history = self.db.get_speed_test_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["download_mbps"], 78.5)
        self.assertEqual(history[0]["upload_mbps"], 25.2)
        self.assertEqual(history[0]["ping_ms"], 14.3)

    def test_clear_history(self):
        self.db.record_delta_traffic(5000, 2000)
        self.db.record_speed_test(50.0, 10.0, 20.0)
        self.db.clear_history()

        recv, sent = self.db.get_today_usage()
        self.assertEqual(recv, 0)
        self.assertEqual(sent, 0)
        self.assertEqual(len(self.db.get_speed_test_history()), 0)

if __name__ == "__main__":
    unittest.main()
