"""SQLite database manager for recording bandwidth usage and speed test records."""

import sqlite3
import datetime
from pathlib import Path
from contextlib import contextmanager
from core.config import get_app_dir

class DatabaseManager:
    """Manages SQLite storage for network traffic analytics and speed tests."""

    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            self.db_path = get_app_dir() / "yaze_history.db"
        else:
            self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Daily aggregated usage table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_usage (
                    date TEXT PRIMARY KEY,
                    bytes_recv INTEGER DEFAULT 0,
                    bytes_sent INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Hourly / snapshot usage logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    bytes_recv INTEGER NOT NULL,
                    bytes_sent INTEGER NOT NULL,
                    interface TEXT DEFAULT 'All'
                )
            """)
            # Speed test history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS speed_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    download_mbps REAL NOT NULL,
                    upload_mbps REAL NOT NULL,
                    ping_ms REAL NOT NULL,
                    server TEXT DEFAULT 'Cloudflare'
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON usage_logs(timestamp)")
            conn.commit()

    def record_delta_traffic(self, bytes_recv: int, bytes_sent: int, interface: str = "All") -> None:
        """Add newly transferred bytes to today's cumulative total and log."""
        if bytes_recv <= 0 and bytes_sent <= 0:
            return

        today_str = datetime.date.today().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Upsert into daily_usage
            cursor.execute("""
                INSERT INTO daily_usage (date, bytes_recv, bytes_sent, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(date) DO UPDATE SET
                    bytes_recv = bytes_recv + excluded.bytes_recv,
                    bytes_sent = bytes_sent + excluded.bytes_sent,
                    last_updated = CURRENT_TIMESTAMP
            """, (today_str, bytes_recv, bytes_sent))

            # Record snapshot
            cursor.execute("""
                INSERT INTO usage_logs (bytes_recv, bytes_sent, interface)
                VALUES (?, ?, ?)
            """, (bytes_recv, bytes_sent, interface))
            conn.commit()

    def get_today_usage(self) -> tuple[int, int]:
        """Return (bytes_recv, bytes_sent) for today."""
        today_str = datetime.date.today().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT bytes_recv, bytes_sent FROM daily_usage WHERE date = ?", (today_str,))
            row = cursor.fetchone()
            if row:
                return int(row["bytes_recv"]), int(row["bytes_sent"])
            return 0, 0

    def get_weekly_usage(self) -> list[dict]:
        """Return usage for the past 7 days up to today."""
        today = datetime.date.today()
        seven_days_ago = (today - datetime.timedelta(days=6)).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, bytes_recv, bytes_sent
                FROM daily_usage
                WHERE date >= ?
                ORDER BY date ASC
            """, (seven_days_ago,))
            rows = cursor.fetchall()
            usage_map = {row["date"]: (row["bytes_recv"], row["bytes_sent"]) for row in rows}

        results = []
        for i in range(7):
            d = (today - datetime.timedelta(days=6 - i)).isoformat()
            recv, sent = usage_map.get(d, (0, 0))
            results.append({
                "date": d,
                "bytes_recv": recv,
                "bytes_sent": sent,
                "total_bytes": recv + sent
            })
        return results

    def get_monthly_usage(self) -> list[dict]:
        """Return usage for the past 30 days."""
        today = datetime.date.today()
        thirty_days_ago = (today - datetime.timedelta(days=29)).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, bytes_recv, bytes_sent
                FROM daily_usage
                WHERE date >= ?
                ORDER BY date ASC
            """, (thirty_days_ago,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_total_usage(self) -> tuple[int, int]:
        """Return (total_bytes_recv, total_bytes_sent) across all recorded history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(bytes_recv) as total_recv, SUM(bytes_sent) as total_sent FROM daily_usage")
            row = cursor.fetchone()
            if row and row["total_recv"] is not None:
                return int(row["total_recv"]), int(row["total_sent"])
            return 0, 0

    def record_speed_test(self, download_mbps: float, upload_mbps: float, ping_ms: float, server: str = "Cloudflare") -> None:
        """Store speed test result."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO speed_tests (download_mbps, upload_mbps, ping_ms, server)
                VALUES (?, ?, ?, ?)
            """, (download_mbps, upload_mbps, ping_ms, server))
            conn.commit()

    def get_speed_test_history(self, limit: int = 15) -> list[dict]:
        """Retrieve recent speed tests."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, download_mbps, upload_mbps, ping_ms, server
                FROM speed_tests
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def clear_history(self) -> None:
        """Purge all logs and usage history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM daily_usage")
            cursor.execute("DELETE FROM usage_logs")
            cursor.execute("DELETE FROM speed_tests")
            conn.commit()
