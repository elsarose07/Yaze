"""Configuration and settings manager for Yaze."""

import json
import os
from pathlib import Path

DEFAULT_SETTINGS = {
    "auto_start": False,
    "low_speed_alert_enabled": False,
    "low_speed_threshold_kbps": 500,  # Alert if download speed is below 500 KB/s
    "low_speed_duration_seconds": 15,  # Trigger alert only if below threshold for 15s
    "alert_cooldown_minutes": 5,       # Do not spam alerts within 5 minutes
    "dark_mode": True,
    "graph_history_points": 60,        # 60 seconds rolling window
    "refresh_interval_ms": 1000,       # 1 second
    "minimize_to_tray_on_close": True,
    "notify_on_minimize": True,
    "selected_interface": "All Interfaces"
}

def get_app_dir() -> Path:
    """Return the user application data directory for Yaze."""
    app_data = os.getenv("APPDATA")
    if app_data:
        path = Path(app_data) / "Yaze"
    else:
        path = Path.home() / ".yaze"
    path.mkdir(parents=True, exist_ok=True)
    return path

class ConfigManager:
    """Thread-safe persistent settings manager."""

    def __init__(self, config_path: Path | None = None):
        if config_path is None:
            self.config_path = get_app_dir() / "settings.json"
        else:
            self.config_path = config_path
        self._settings = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self) -> dict:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._settings.update(loaded)
            except Exception:
                # Fallback to default settings if corrupted
                self._settings = dict(DEFAULT_SETTINGS)
        return self._settings

    def save(self) -> None:
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default=None):
        return self._settings.get(key, default)

    def set(self, key: str, value) -> None:
        self._settings[key] = value
        self.save()

    def all(self) -> dict:
        return dict(self._settings)
