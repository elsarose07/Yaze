"""System tray controller with dynamic speed painting and persistent background execution."""

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from core.network_monitor import format_speed_compact, format_speed, format_bytes

class YazeTrayIcon(QSystemTrayIcon):
    """Dynamic system tray icon displaying live download/upload speeds."""

    def __init__(self, main_window, startup_manager, config_manager, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.startup_manager = startup_manager
        self.config_manager = config_manager

        # Set initial blank icon
        self.update_tray_icon(0.0, 0.0)

        # Build context menu
        self._create_menu()

        # Connect click handlers
        self.activated.connect(self._on_tray_activated)

    def _create_menu(self) -> None:
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #2563EB;
            }
            QMenu::separator {
                height: 1px;
                background-color: #334155;
                margin: 4px 8px;
            }
        """)

        # Title
        title_action = menu.addAction("Yaze – Network Monitor")
        title_action.setEnabled(False)
        font = title_action.font()
        font.setBold(True)
        title_action.setFont(font)

        menu.addSeparator()

        # Show / Hide Dashboard
        self.show_action = menu.addAction("Open Dashboard")
        self.show_action.triggered.connect(self.toggle_window)

        # Run Speed Test
        self.speedtest_action = menu.addAction("Run Speed Test")
        self.speedtest_action.triggered.connect(self._on_run_speedtest)

        menu.addSeparator()

        # Info Actions (Live updates)
        self.wifi_info_action = menu.addAction("Wi-Fi: Scanning...")
        self.wifi_info_action.setEnabled(False)

        self.today_usage_action = menu.addAction("Today: 0 B / 0 B")
        self.today_usage_action.setEnabled(False)

        menu.addSeparator()

        # Auto-startup toggle
        self.startup_action = QAction("Start with Windows", menu)
        self.startup_action.setCheckable(True)
        self.startup_action.setChecked(self.startup_manager.is_auto_start_enabled())
        self.startup_action.toggled.connect(self._on_startup_toggled)
        menu.addAction(self.startup_action)

        # Settings
        self.settings_action = menu.addAction("Settings")
        self.settings_action.triggered.connect(self._on_open_settings)

        menu.addSeparator()

        # Explicit Exit option (critical requirement!)
        exit_action = menu.addAction("Exit Yaze")
        exit_action.triggered.connect(self._on_exit_application)

        self.setContextMenu(menu)

    def update_tray_icon(self, download_bps: float, upload_bps: float) -> None:
        """Render real-time download and upload rate directly on the tray icon."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dark pill container
        painter.setBrush(QColor("#0F172A"))
        painter.setPen(QColor("#334155"))
        painter.drawRoundedRect(QRectF(1, 1, 62, 62), 10, 10)

        # Compact speed text
        down_text = f"↓{format_speed_compact(download_bps)}"
        up_text = f"↑{format_speed_compact(upload_bps)}"

        # Font configuration
        font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        painter.setFont(font)

        # Download (Cyan)
        painter.setPen(QColor("#38BDF8"))
        painter.drawText(QRectF(2, 4, 60, 26), Qt.AlignmentFlag.AlignCenter, down_text)

        # Upload (Emerald Green)
        painter.setPen(QColor("#10B981"))
        painter.drawText(QRectF(2, 32, 60, 26), Qt.AlignmentFlag.AlignCenter, up_text)

        painter.end()
        self.setIcon(QIcon(pixmap))

        # Update Tray Tooltip
        self.setToolTip(
            f"Yaze – Real-Time Network Monitor\n"
            f"Download: {format_speed(download_bps)}\n"
            f"Upload:   {format_speed(upload_bps)}"
        )

    def update_status_info(self, wifi_info: dict, today_usage: tuple[int, int]) -> None:
        """Update context menu dynamic labels with connection and data usage."""
        if wifi_info.get("is_wifi"):
            self.wifi_info_action.setText(f"Wi-Fi: {wifi_info.get('ssid')} ({wifi_info.get('signal')})")
        else:
            self.wifi_info_action.setText(f"Network: {wifi_info.get('state', 'Connected')}")

        recv, sent = today_usage
        self.today_usage_action.setText(f"Today: ↓{format_bytes(recv)} | ↑{format_bytes(sent)}")

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.toggle_window()

    def toggle_window(self) -> None:
        if self.main_window.isVisible():
            if self.main_window.isMinimized():
                self.main_window.showNormal()
                self.main_window.activateWindow()
            else:
                self.main_window.hide()
        else:
            self.main_window.showNormal()
            self.main_window.activateWindow()

    def _on_run_speedtest(self) -> None:
        self.main_window.showNormal()
        self.main_window.activateWindow()
        self.main_window.tabs.setCurrentIndex(3)  # Speed test tab index

    def _on_open_settings(self) -> None:
        self.main_window.showNormal()
        self.main_window.activateWindow()
        self.main_window.tabs.setCurrentIndex(4)  # Settings tab index

    def _on_startup_toggled(self, checked: bool) -> None:
        self.startup_manager.set_auto_start(checked)
        self.config_manager.set("auto_start", checked)

    def _on_exit_application(self) -> None:
        """Explicit exit from the tray menu that shuts down the application completely."""
        self.main_window.force_quit()
