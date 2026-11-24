"""Yaze – Real-Time Network Monitoring System for Windows.

Entry point for starting the application in either standard GUI mode or background tray mode.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt

from core.config import ConfigManager
from core.database import DatabaseManager
from core.network_monitor import NetworkMonitor
from core.startup import StartupManager
from ui.theme import DARK_THEME_QSS
from ui.main_window import MainWindow

def create_app_icon() -> QIcon:
    """Generate high-resolution application icon."""
    pix = QPixmap(128, 128)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Rounded gradient background
    painter.setBrush(QColor("#0F172A"))
    painter.setPen(QColor("#38BDF8"))
    painter.drawRoundedRect(4, 4, 120, 120, 24, 24)

    # Lightning bolt or letter Y
    painter.setPen(QColor("#38BDF8"))
    font = QFont("Segoe UI", 68, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(0, 10, 128, 108, Qt.AlignmentFlag.AlignCenter, "Y")
    painter.end()
    return QIcon(pix)

def main():
    # Enable High DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("Yaze")
    app.setOrganizationName("YazeNetwork")

    # CRITICAL: Prevent Qt from terminating the application when the main window is closed
    app.setQuitOnLastWindowClosed(False)

    app_icon = create_app_icon()
    app.setWindowIcon(app_icon)

    # Apply Dark Fluent Theme
    app.setStyleSheet(DARK_THEME_QSS)

    # Initialize Core Subsystems
    config = ConfigManager()
    db = DatabaseManager()
    selected_iface = config.get("selected_interface", "All Interfaces")
    monitor = NetworkMonitor(interface=selected_iface)
    startup = StartupManager()

    window = MainWindow(config=config, db=db, monitor=monitor, startup=startup)

    # Check launch arguments (e.g. from Windows boot startup)
    start_in_tray = "--tray" in sys.argv or "--minimized" in sys.argv
    if not start_in_tray:
        window.show()
    else:
        # Running in background tray mode
        if config.get("notify_on_minimize", True):
            window.tray_icon.showMessage(
                "Yaze Started",
                "Yaze is running in the background monitoring your network.",
                window.tray_icon.MessageIcon.Information,
                2500
            )

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
