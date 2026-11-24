"""Speed test worker measuring latency, download, and upload throughput."""

import time
import ssl
import urllib.request
from PyQt6.QtCore import QThread, pyqtSignal

def get_ssl_context():
    """Create a resilient SSL context."""
    try:
        ctx = ssl.create_default_context()
        return ctx
    except Exception:
        return ssl._create_unverified_context()

class SpeedTestWorker(QThread):
    """Asynchronous background worker for running speed tests without freezing the UI."""

    status_changed = pyqtSignal(str)          # E.g. "Measuring latency...", "Testing download..."
    progress_changed = pyqtSignal(int)        # 0 to 100
    partial_result = pyqtSignal(str, float)   # ("ping", 18.2), ("download", 45.1), ("upload", 22.0)
    finished = pyqtSignal(dict)               # Full results dictionary
    error = pyqtSignal(str)                   # Error message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_cancelled = False
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Yaze/1.0"}

    def cancel(self):
        """Cancel the ongoing test."""
        self._is_cancelled = True

    def run(self):
        self._is_cancelled = False
        results = {
            "ping_ms": 0.0,
            "download_mbps": 0.0,
            "upload_mbps": 0.0,
            "server": "Cloudflare Edge",
        }

        try:
            ctx = get_ssl_context()

            # --- 1. Ping / Latency Test ---
            self.status_changed.emit("Measuring Latency (Ping)...")
            self.progress_changed.emit(10)

            ping_samples = []
            for _ in range(3):
                if self._is_cancelled:
                    return
                t0 = time.perf_counter()
                req = urllib.request.Request("https://speed.cloudflare.com/cdn-cgi/trace", headers=self.headers)
                with urllib.request.urlopen(req, timeout=6, context=ctx) as resp:
                    resp.read(512)
                t1 = time.perf_counter()
                ping_samples.append((t1 - t0) * 1000)
                time.sleep(0.1)

            avg_ping = sum(ping_samples) / len(ping_samples)
            results["ping_ms"] = round(avg_ping, 1)
            self.partial_result.emit("ping", results["ping_ms"])
            self.progress_changed.emit(30)

            # --- 2. Download Test ---
            if self._is_cancelled:
                return

            self.status_changed.emit("Testing Download Bandwidth...")
            download_bytes_target = 10_000_000  # 10 MB payload
            req = urllib.request.Request(
                f"https://speed.cloudflare.com/__down?bytes={download_bytes_target}",
                headers=self.headers
            )

            t_start = time.perf_counter()
            received_bytes = 0

            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                chunk_size = 64 * 1024
                while True:
                    if self._is_cancelled:
                        return
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    received_bytes += len(chunk)
                    elapsed = time.perf_counter() - t_start

                    # Intermediate progress updates
                    pct = 30 + int((received_bytes / download_bytes_target) * 35)
                    self.progress_changed.emit(min(pct, 65))
                    if elapsed > 0.3:
                        instant_mbps = (received_bytes * 8) / (elapsed * 1_000_000)
                        self.partial_result.emit("download", round(instant_mbps, 2))

            t_end = time.perf_counter()
            total_time = max(0.001, t_end - t_start)
            download_mbps = (received_bytes * 8) / (total_time * 1_000_000)
            results["download_mbps"] = round(download_mbps, 2)
            self.partial_result.emit("download", results["download_mbps"])
            self.progress_changed.emit(65)

            # --- 3. Upload Test ---
            if self._is_cancelled:
                return

            self.status_changed.emit("Testing Upload Bandwidth...")
            upload_payload = b"0" * 3_000_000  # 3 MB payload
            req = urllib.request.Request(
                "https://speed.cloudflare.com/__up",
                data=upload_payload,
                headers=self.headers,
                method="POST"
            )

            t_up_start = time.perf_counter()
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                resp.read()
            t_up_end = time.perf_counter()

            up_time = max(0.001, t_up_end - t_up_start)
            upload_mbps = (len(upload_payload) * 8) / (up_time * 1_000_000)
            results["upload_mbps"] = round(upload_mbps, 2)
            self.partial_result.emit("upload", results["upload_mbps"])
            self.progress_changed.emit(100)

            self.status_changed.emit("Speed Test Complete")
            self.finished.emit(results)

        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(f"Speed test failed: {str(e)}")
