"""Network traffic monitoring, speed calculations, and Wi-Fi diagnostics."""

import time
import subprocess
import socket
import psutil

def format_bytes(num_bytes: float) -> str:
    """Format bytes to human readable string (B, KB, MB, GB, TB)."""
    if num_bytes < 1024:
        return f"{num_bytes:.0f} B"
    elif num_bytes < 1024 ** 2:
        return f"{num_bytes / 1024:.1f} KB"
    elif num_bytes < 1024 ** 3:
        return f"{num_bytes / (1024 ** 2):.2f} MB"
    elif num_bytes < 1024 ** 4:
        return f"{num_bytes / (1024 ** 3):.2f} GB"
    else:
        return f"{num_bytes / (1024 ** 4):.2f} TB"

def format_speed(bytes_per_sec: float) -> str:
    """Format bytes per second into human-readable transfer rate."""
    if bytes_per_sec < 1024:
        return f"{bytes_per_sec:.0f} B/s"
    elif bytes_per_sec < 1024 ** 2:
        return f"{bytes_per_sec / 1024:.1f} KB/s"
    elif bytes_per_sec < 1024 ** 3:
        return f"{bytes_per_sec / (1024 ** 2):.2f} MB/s"
    else:
        return f"{bytes_per_sec / (1024 ** 3):.2f} GB/s"

def format_speed_compact(bytes_per_sec: float) -> str:
    """Compact format for tray icons (e.g., '120K', '4.2M')."""
    if bytes_per_sec < 1024:
        return f"{int(bytes_per_sec)}B"
    elif bytes_per_sec < 1024 ** 2:
        kb = bytes_per_sec / 1024
        return f"{int(kb)}K" if kb >= 10 else f"{kb:.1f}K"
    elif bytes_per_sec < 1024 ** 3:
        mb = bytes_per_sec / (1024 ** 2)
        return f"{int(mb)}M" if mb >= 10 else f"{mb:.1f}M"
    else:
        gb = bytes_per_sec / (1024 ** 3)
        return f"{gb:.1f}G"

class NetworkMonitor:
    """Tracks network traffic deltas, computes live throughput, and polls network diagnostics."""

    def __init__(self, interface: str = "All Interfaces"):
        self.interface = interface
        self.last_time = time.time()
        self.last_recv, self.last_sent = self._get_raw_counters()
        self.download_speed = 0.0  # Bytes/sec
        self.upload_speed = 0.0    # Bytes/sec
        self.session_recv = 0
        self.session_sent = 0

    def _get_raw_counters(self) -> tuple[int, int]:
        """Fetch raw total sent/received bytes for the selected interface or all."""
        try:
            if self.interface == "All Interfaces" or not self.interface:
                counters = psutil.net_io_counters(pernic=False)
                return counters.bytes_recv, counters.bytes_sent
            else:
                per_nic = psutil.net_io_counters(pernic=True)
                if self.interface in per_nic:
                    c = per_nic[self.interface]
                    return c.bytes_recv, c.bytes_sent
                # Fallback to total if interface not found
                counters = psutil.net_io_counters(pernic=False)
                return counters.bytes_recv, counters.bytes_sent
        except Exception:
            return 0, 0

    def update(self) -> dict:
        """Calculate throughput since last call and update session statistics."""
        current_time = time.time()
        dt = current_time - self.last_time
        if dt <= 0:
            dt = 0.001

        current_recv, current_sent = self._get_raw_counters()

        # Handle counter rollover or reboot
        delta_recv = max(0, current_recv - self.last_recv)
        delta_sent = max(0, current_sent - self.last_sent)

        # Compute speed in Bytes per second
        self.download_speed = delta_recv / dt
        self.upload_speed = delta_sent / dt

        self.session_recv += delta_recv
        self.session_sent += delta_sent

        self.last_time = current_time
        self.last_recv = current_recv
        self.last_sent = current_sent

        return {
            "download_speed": self.download_speed,
            "upload_speed": self.upload_speed,
            "delta_recv": delta_recv,
            "delta_sent": delta_sent,
            "session_recv": self.session_recv,
            "session_sent": self.session_sent,
            "download_str": format_speed(self.download_speed),
            "upload_str": format_speed(self.upload_speed),
            "download_compact": format_speed_compact(self.download_speed),
            "upload_compact": format_speed_compact(self.upload_speed),
        }

    @staticmethod
    def get_available_interfaces() -> list[str]:
        """Return list of available network interfaces."""
        try:
            nics = list(psutil.net_if_addrs().keys())
            return ["All Interfaces"] + sorted(nics)
        except Exception:
            return ["All Interfaces"]

    @staticmethod
    def get_wifi_and_connection_info() -> dict:
        """Retrieve Wi-Fi SSID, signal quality, and active IP/Gateway configuration."""
        info = {
            "is_wifi": False,
            "ssid": "Not Connected",
            "bssid": "N/A",
            "signal": "N/A",
            "radio_type": "N/A",
            "state": "Disconnected",
            "local_ip": "127.0.0.1",
            "active_adapter": "N/A"
        }

        # 1. Fetch Local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info["local_ip"] = s.getsockname()[0]
            s.close()
        except Exception:
            info["local_ip"] = "127.0.0.1"

        # 2. Check Windows WLAN via netsh
        try:
            proc = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True,
                text=True,
                timeout=3,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            out = proc.stdout
            if proc.returncode == 0 and "State" in out:
                for line in out.splitlines():
                    line = line.strip()
                    if line.startswith("SSID") and not line.startswith("BSSID"):
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            info["ssid"] = parts[1].strip()
                            info["is_wifi"] = True
                    elif line.startswith("BSSID"):
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            info["bssid"] = parts[1].strip()
                    elif line.startswith("Signal"):
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            info["signal"] = parts[1].strip()
                    elif line.startswith("Radio type"):
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            info["radio_type"] = parts[1].strip()
                    elif line.startswith("State"):
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            info["state"] = parts[1].strip().capitalize()
                    elif line.startswith("Description"):
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            info["active_adapter"] = parts[1].strip()
        except Exception:
            pass

        # 3. If not Wi-Fi, find active Ethernet or default interface name
        if not info["is_wifi"] or info["ssid"] == "Not Connected":
            try:
                for nic_name, addrs in psutil.net_if_addrs().items():
                    for a in addrs:
                        if a.family == socket.AF_INET and a.address == info["local_ip"]:
                            info["active_adapter"] = nic_name
                            info["state"] = "Connected (Ethernet/LAN)"
                            break
            except Exception:
                pass

        return info
