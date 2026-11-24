"""Manages low-speed alert detection and notification throttling."""

import time
from core.network_monitor import format_speed

class AlertManager:
    """Evaluates network speed against configured thresholds and fires throttled notifications."""

    def __init__(self, config_manager, notification_callback=None):
        self.config = config_manager
        self.notification_callback = notification_callback
        self.low_speed_start_time: float | None = None
        self.last_alert_time: float = 0.0

    def check_speed(self, current_download_speed_bps: float) -> bool:
        """Evaluate current speed. Returns True if an alert was triggered."""
        if not self.config.get("low_speed_alert_enabled", False):
            self.low_speed_start_time = None
            return False

        threshold_bps = float(self.config.get("low_speed_threshold_kbps", 500)) * 1024.0
        duration_req = float(self.config.get("low_speed_duration_seconds", 15))
        cooldown_sec = float(self.config.get("alert_cooldown_minutes", 5)) * 60.0
        now = time.time()

        if current_download_speed_bps < threshold_bps:
            if self.low_speed_start_time is None:
                self.low_speed_start_time = now

            if (now - self.low_speed_start_time) >= duration_req:
                # Trigger alert if cooldown has elapsed
                if (now - self.last_alert_time) >= cooldown_sec:
                    self.last_alert_time = now
                    speed_str = format_speed(current_download_speed_bps)
                    threshold_str = format_speed(threshold_bps)
                    title = "Yaze – Low Internet Speed Alert"
                    msg = (f"Download speed is currently {speed_str}, "
                           f"below your threshold of {threshold_str} for over {int(duration_req)}s.")
                    if self.notification_callback:
                        self.notification_callback(title, msg)
                    return True
        else:
            # Speed is healthy, reset the timer
            self.low_speed_start_time = None

        return False
