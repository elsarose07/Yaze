"""Process-level network activity and bandwidth consumption monitor."""

import time
import psutil
from core.network_monitor import format_speed, format_bytes

class ProcessNetworkMonitor:
    """Tracks per-process network I/O activity and active network connections."""

    def __init__(self):
        # Store previous {pid: (read_bytes, write_bytes, timestamp)}
        self._prev_io: dict[int, tuple[int, int, float]] = {}

    def get_active_network_processes(self, limit: int = 25) -> list[dict]:
        """Fetch active processes with network sockets, sorted by current throughput."""
        now = time.time()
        active_pids = set()

        try:
            for conn in psutil.net_connections(kind="inet"):
                if conn.pid and conn.pid > 0:
                    active_pids.add(conn.pid)
        except (psutil.AccessDenied, Exception):
            pass

        processes_data = []

        for pid in active_pids:
            try:
                proc = psutil.Process(pid)
                name = proc.name()
                io = proc.io_counters()
                read_bytes = io.read_bytes
                write_bytes = io.write_bytes

                down_speed = 0.0
                up_speed = 0.0

                if pid in self._prev_io:
                    prev_r, prev_w, prev_t = self._prev_io[pid]
                    dt = now - prev_t
                    if dt > 0:
                        down_speed = max(0.0, (read_bytes - prev_r) / dt)
                        up_speed = max(0.0, (write_bytes - prev_w) / dt)

                self._prev_io[pid] = (read_bytes, write_bytes, now)

                processes_data.append({
                    "pid": pid,
                    "name": name,
                    "download_speed": down_speed,
                    "upload_speed": up_speed,
                    "total_read": read_bytes,
                    "total_write": write_bytes,
                    "download_str": format_speed(down_speed),
                    "upload_str": format_speed(up_speed),
                    "total_data_str": format_bytes(read_bytes + write_bytes),
                    "total_speed": down_speed + up_speed
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                continue

        # Prune dead PIDs from history
        current_pids = set(self._prev_io.keys())
        for dead_pid in current_pids - active_pids:
            self._prev_io.pop(dead_pid, None)

        # Sort descending by current bandwidth consumption, then by total transferred
        processes_data.sort(key=lambda x: (x["total_speed"], x["total_read"] + x["total_write"]), reverse=True)
        return processes_data[:limit]
