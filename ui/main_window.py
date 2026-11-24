"""Main window dashboard for Yaze featuring a Studio Minimalist sidebar architecture."""

import time
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QStackedWidget, QFrame, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QProgressBar, QCheckBox, QSpinBox,
    QComboBox, QMessageBox, QApplication, QSystemTrayIcon, QButtonGroup
)
from PyQt6.QtGui import QFont, QIcon, QColor

from core.config import ConfigManager
from core.database import DatabaseManager
from core.network_monitor import NetworkMonitor, format_speed, format_bytes
from core.process_monitor import ProcessNetworkMonitor
from core.startup import StartupManager
from core.speedtest import SpeedTestWorker
from core.alert_manager import AlertManager
from ui.graph_widget import SpeedGraphWidget
from ui.tray import YazeTrayIcon

class TabAdapter(QStackedWidget):
    """StackedWidget adapter providing tab-compatible methods for test harnesses."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tab_titles = []

    def addTab(self, widget: QWidget, title: str) -> int:
        idx = self.addWidget(widget)
        self._tab_titles.append(title)
        return idx

    def tabText(self, index: int) -> str:
        if 0 <= index < len(self._tab_titles):
            return self._tab_titles[index]
        return ""

class MainWindow(QMainWindow):
    """Studio Minimalist dashboard featuring a vertical sidebar rail and live telemetry cockpit."""

    def __init__(self, config: ConfigManager, db: DatabaseManager, monitor: NetworkMonitor,
                 startup: StartupManager, parent=None):
        super().__init__(parent)
        self.config = config
        self.db = db
        self.monitor = monitor
        self.startup = startup
        self.process_monitor = ProcessNetworkMonitor()
        self._is_force_quitting = False

        self.setWindowTitle("Yaze – Real-Time Network Monitor")
        self.resize(1000, 680)
        self.setMinimumSize(850, 580)

        # Initialize Alert Engine
        self.alert_manager = AlertManager(self.config, self.show_toast_notification)

        # Speed test worker reference
        self.speedtest_worker: SpeedTestWorker | None = None

        # Build UI
        self._setup_ui()

        # Setup System Tray
        self.tray_icon = YazeTrayIcon(self, self.startup, self.config)
        self.tray_icon.show()

        # Live telemetry timer (1 second ticks)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(int(self.config.get("refresh_interval_ms", 1000)))

        # Process monitor timer (every 2.5 seconds to conserve CPU)
        self.proc_timer = QTimer(self)
        self.proc_timer.timeout.connect(self._on_process_tick)
        self.proc_timer.start(2500)

        # Initial tick
        self._on_tick()

    def _setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar Rail (210px)
        sidebar = self._create_sidebar()
        root_layout.addWidget(sidebar)

        # 2. Right Content Workspace (Stacked Widget)
        self.tabs = TabAdapter()
        self.tabs.addTab(self._create_overview_tab(), "Overview")
        self.tabs.addTab(self._create_applications_tab(), "Applications")
        self.tabs.addTab(self._create_analytics_tab(), "Analytics & History")
        self.tabs.addTab(self._create_speedtest_tab(), "Speed Test")
        self.tabs.addTab(self._create_settings_tab(), "Settings")

        # Keep sidebar buttons and stacked widget in sync
        self.tabs.currentChanged.connect(self._sync_sidebar_selection)

        root_layout.addWidget(self.tabs, stretch=1)

    def _create_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        sidebar.setStyleSheet("""
            QFrame#sidebar {
                background-color: #0E0E10;
                border-right: 1px solid #27272A;
            }
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 14, 16)
        layout.setSpacing(8)

        # Brand Header
        brand_box = QVBoxLayout()
        brand_box.setSpacing(3)
        brand_title = QLabel("⚡ YAZE")
        brand_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        brand_title.setStyleSheet("color: #FFFFFF; letter-spacing: 1px;")

        self.sidebar_status_badge = QLabel("● Live Telemetry")
        self.sidebar_status_badge.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 600;")

        brand_box.addWidget(brand_title)
        brand_box.addWidget(self.sidebar_status_badge)
        layout.addLayout(brand_box)
        layout.addSpacing(16)

        # Navigation Rail Buttons
        self.nav_btn_group = QButtonGroup(self)
        self.nav_btn_group.setExclusive(True)
        self.nav_buttons = []

        nav_items = [
            ("⚡ Overview", 0),
            ("📊 Applications", 1),
            ("📈 Analytics", 2),
            ("🚀 Speed Test", 3),
            ("⚙️ Settings", 4),
        ]

        for label, idx in nav_items:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("class", "nav-item")
            btn.setFixedHeight(38)
            btn.setStyleSheet("""
                QPushButton.nav-item {
                    background-color: transparent;
                    color: #A1A1AA;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-weight: 600;
                    font-size: 13px;
                    text-align: left;
                }
                QPushButton.nav-item:hover {
                    background-color: #18181B;
                    color: #FFFFFF;
                }
                QPushButton.nav-item:checked {
                    background-color: #27272A;
                    color: #FFFFFF;
                    font-weight: 700;
                    border-left: 3px solid #38BDF8;
                }
            """)
            btn.clicked.connect(lambda _, i=idx: self.tabs.setCurrentIndex(i))
            self.nav_btn_group.addButton(btn, idx)
            self.nav_buttons.append(btn)
            layout.addWidget(btn)

        self.nav_buttons[0].setChecked(True)

        layout.addStretch()

        # Sidebar Bottom Utilities
        self.sidebar_conn_label = QLabel("Wi-Fi: Detecting...")
        self.sidebar_conn_label.setStyleSheet("color: #71717A; font-size: 11px;")
        layout.addWidget(self.sidebar_conn_label)

        btn_min = QPushButton("Minimize to Tray")
        btn_min.setProperty("class", "secondary")
        btn_min.setFixedHeight(32)
        btn_min.setStyleSheet("""
            QPushButton {
                background-color: #18181B;
                color: #A1A1AA;
                border: 1px solid #27272A;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #27272A;
                color: #FFFFFF;
                border: 1px solid #3F3F46;
            }
        """)
        btn_min.clicked.connect(self.hide)
        layout.addWidget(btn_min)

        return sidebar

    def _sync_sidebar_selection(self, index: int) -> None:
        if 0 <= index < len(self.nav_buttons):
            self.nav_buttons[index].setChecked(True)
        # Immediate refresh on tab activation
        if index == 1:
            self._on_process_tick()
        elif index == 2:
            self._refresh_analytics()

    # =========================================================================
    # TAB 1: OVERVIEW (Immersive Real-Time Oscilloscope)
    # =========================================================================
    def _create_overview_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # 1. Four Metric KPI Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.card_down_speed = self._create_kpi_card("DOWNLOAD SPEED", "0.0 KB/s", "#38BDF8")
        self.card_up_speed = self._create_kpi_card("UPLOAD SPEED", "0.0 KB/s", "#10B981")
        self.card_today_down = self._create_kpi_card("TODAY RECEIVED", "0.0 MB", "#FFFFFF")
        self.card_today_up = self._create_kpi_card("TODAY SENT", "0.0 MB", "#FFFFFF")

        cards_layout.addWidget(self.card_down_speed["frame"])
        cards_layout.addWidget(self.card_up_speed["frame"])
        cards_layout.addWidget(self.card_today_down["frame"])
        cards_layout.addWidget(self.card_today_up["frame"])
        layout.addLayout(cards_layout)

        # 2. Immersive Real-Time Speed Oscilloscope
        self.speed_graph = SpeedGraphWidget(self.config.get("graph_history_points", 60))
        layout.addWidget(self.speed_graph, stretch=1)

        # 3. Connection & Wi-Fi Details Bar
        conn_bar = QFrame()
        conn_bar.setObjectName("conn_bar")
        conn_bar.setStyleSheet("""
            QFrame#conn_bar {
                background-color: #18181B;
                border: 1px solid #27272A;
                border-radius: 8px;
            }
            QLabel {
                background-color: transparent;
                border: none;
            }
        """)
        c_layout = QHBoxLayout(conn_bar)
        c_layout.setContentsMargins(14, 10, 14, 10)
        c_layout.setSpacing(18)

        self.wifi_ssid_label = QLabel("SSID: Detecting...")
        self.wifi_ssid_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.wifi_signal_label = QLabel("Signal: --")
        self.wifi_signal_label.setStyleSheet("color: #A1A1AA;")
        self.wifi_ip_label = QLabel("Local IP: 127.0.0.1")
        self.wifi_ip_label.setStyleSheet("color: #A1A1AA;")
        self.wifi_adapter_label = QLabel("Adapter: --")
        self.wifi_adapter_label.setStyleSheet("color: #A1A1AA;")

        c_layout.addWidget(self.wifi_ssid_label)
        c_layout.addWidget(self.wifi_signal_label)
        c_layout.addWidget(self.wifi_ip_label)
        c_layout.addWidget(self.wifi_adapter_label)
        c_layout.addStretch()

        btn_reset_peaks = QPushButton("Reset Peaks")
        btn_reset_peaks.setStyleSheet("""
            QPushButton {
                background-color: #27272A;
                color: #E4E4E7;
                border: 1px solid #3F3F46;
                padding: 4px 10px;
                font-size: 11px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3F3F46;
                color: #FFFFFF;
            }
        """)
        btn_reset_peaks.clicked.connect(self.speed_graph.reset_peaks)
        c_layout.addWidget(btn_reset_peaks)

        layout.addWidget(conn_bar)
        return tab

    def _create_kpi_card(self, title: str, initial_value: str, accent_color: str) -> dict:
        frame = QFrame()
        frame.setObjectName("kpi_card")
        frame.setStyleSheet(f"""
            QFrame#kpi_card {{
                background-color: #18181B;
                border: 1px solid #27272A;
                border-top: 2px solid {accent_color};
                border-radius: 8px;
            }}
            QFrame#kpi_card:hover {{
                border: 1px solid #3F3F46;
                border-top: 2px solid {accent_color};
            }}
            QLabel {{
                background-color: transparent;
                border: none;
            }}
        """)
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(12, 10, 12, 10)
        vbox.setSpacing(6)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #A1A1AA; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")

        lbl_val = QLabel(initial_value)
        lbl_val.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_val.setStyleSheet(f"color: {accent_color};")

        vbox.addWidget(lbl_title)
        vbox.addWidget(lbl_val)
        return {"frame": frame, "title": lbl_title, "value": lbl_val}

    # =========================================================================
    # TAB 2: APPLICATIONS (Per-Process Bandwidth Telemetry)
    # =========================================================================
    def _create_applications_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header controls
        ctrl_bar = QHBoxLayout()
        self.proc_search = QLineEdit()
        self.proc_search.setPlaceholderText("Filter active processes by name or PID...")
        self.proc_search.textChanged.connect(self._filter_process_table)

        btn_refresh = QPushButton("Refresh Now")
        btn_refresh.clicked.connect(self._on_process_tick)

        ctrl_bar.addWidget(self.proc_search)
        ctrl_bar.addWidget(btn_refresh)
        layout.addLayout(ctrl_bar)

        # Process Table
        self.proc_table = QTableWidget()
        self.proc_table.setColumnCount(5)
        self.proc_table.setHorizontalHeaderLabels([
            "APPLICATION / PROCESS", "PID", "DOWNLOAD RATE", "UPLOAD RATE", "TOTAL I/O DATA"
        ])
        header = self.proc_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.proc_table.verticalHeader().setVisible(False)
        self.proc_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.proc_table)
        return tab

    # =========================================================================
    # TAB 3: ANALYTICS & HISTORY
    # =========================================================================
    def _create_analytics_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # All-time summary cards
        sum_layout = QHBoxLayout()
        self.all_time_down = self._create_kpi_card("ALL-TIME DOWNLOAD", "0.0 GB", "#38BDF8")
        self.all_time_up = self._create_kpi_card("ALL-TIME UPLOAD", "0.0 GB", "#10B981")
        self.all_time_total = self._create_kpi_card("TOTAL BANDWIDTH", "0.0 GB", "#FFFFFF")
        sum_layout.addWidget(self.all_time_down["frame"])
        sum_layout.addWidget(self.all_time_up["frame"])
        sum_layout.addWidget(self.all_time_total["frame"])
        layout.addLayout(sum_layout)

        # Weekly Breakdown Table
        lbl_weekly = QLabel("Past 7 Days Bandwidth Consumption")
        lbl_weekly.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_weekly)

        self.weekly_table = QTableWidget()
        self.weekly_table.setColumnCount(4)
        self.weekly_table.setHorizontalHeaderLabels(["DATE", "DOWNLOADED", "UPLOADED", "TOTAL DATA"])
        w_header = self.weekly_table.horizontalHeader()
        w_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        w_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        w_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        w_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.weekly_table.verticalHeader().setVisible(False)
        self.weekly_table.setMaximumHeight(180)
        layout.addWidget(self.weekly_table)

        # Speed Test History
        lbl_speed = QLabel("Recent Speed Test Records")
        lbl_speed.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_speed)

        self.speed_history_table = QTableWidget()
        self.speed_history_table.setColumnCount(5)
        self.speed_history_table.setHorizontalHeaderLabels(["TIMESTAMP", "DOWNLOAD", "UPLOAD", "PING", "SERVER"])
        s_header = self.speed_history_table.horizontalHeader()
        s_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        s_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        s_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        s_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        s_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.speed_history_table.verticalHeader().setVisible(False)
        layout.addWidget(self.speed_history_table)

        btn_refresh_analytics = QPushButton("Refresh Analytics")
        btn_refresh_analytics.setProperty("class", "secondary")
        btn_refresh_analytics.clicked.connect(self._refresh_analytics)
        layout.addWidget(btn_refresh_analytics)

        return tab

    # =========================================================================
    # TAB 4: SPEED TEST
    # =========================================================================
    def _create_speedtest_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(18, 20, 18, 20)
        layout.setSpacing(16)

        # Title & Server Info
        header_box = QVBoxLayout()
        header_box.setSpacing(4)
        st_title = QLabel("Internet Bandwidth Speed Test")
        st_title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        st_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.st_server_lbl = QLabel("Testing Server: Cloudflare Edge Global Network")
        self.st_server_lbl.setStyleSheet("color: #A1A1AA; font-size: 12px;")
        self.st_server_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_box.addWidget(st_title)
        header_box.addWidget(self.st_server_lbl)
        layout.addLayout(header_box)

        # Results Cards
        res_layout = QHBoxLayout()
        res_layout.setSpacing(14)
        self.st_ping_card = self._create_kpi_card("LATENCY (PING)", "-- ms", "#F59E0B")
        self.st_down_card = self._create_kpi_card("DOWNLOAD BANDWIDTH", "-- Mbps", "#38BDF8")
        self.st_up_card = self._create_kpi_card("UPLOAD BANDWIDTH", "-- Mbps", "#10B981")
        res_layout.addWidget(self.st_ping_card["frame"])
        res_layout.addWidget(self.st_down_card["frame"])
        res_layout.addWidget(self.st_up_card["frame"])
        layout.addLayout(res_layout)

        # Progress Section
        self.st_status_lbl = QLabel("Click 'Start Speed Test' to measure network bandwidth")
        self.st_status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.st_status_lbl.setStyleSheet("color: #A1A1AA; font-weight: 600;")
        layout.addWidget(self.st_status_lbl)

        self.st_progress = QProgressBar()
        self.st_progress.setValue(0)
        layout.addWidget(self.st_progress)

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_start_test = QPushButton("Start Speed Test")
        self.btn_start_test.setFixedSize(160, 40)
        self.btn_start_test.clicked.connect(self._start_speed_test)
        btn_box.addWidget(self.btn_start_test)

        self.btn_cancel_test = QPushButton("Cancel")
        self.btn_cancel_test.setFixedSize(100, 40)
        self.btn_cancel_test.setProperty("class", "secondary")
        self.btn_cancel_test.setEnabled(False)
        self.btn_cancel_test.clicked.connect(self._cancel_speed_test)
        btn_box.addWidget(self.btn_cancel_test)

        btn_box.addStretch()
        layout.addLayout(btn_box)
        layout.addStretch()

        return tab

    # =========================================================================
    # TAB 5: SETTINGS
    # =========================================================================
    def _create_settings_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(18, 20, 18, 20)
        layout.setSpacing(16)

        # General Card
        card_gen = QFrame()
        card_gen.setStyleSheet("background-color: #18181B; border: 1px solid #27272A; border-radius: 8px; padding: 14px;")
        gen_layout = QVBoxLayout(card_gen)
        gen_layout.setSpacing(10)

        lbl_gen = QLabel("General Application Settings")
        lbl_gen.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        gen_layout.addWidget(lbl_gen)

        self.chk_startup = QCheckBox("Launch Yaze automatically when Windows starts up")
        self.chk_startup.setChecked(self.startup.is_auto_start_enabled())
        self.chk_startup.toggled.connect(self._on_setting_startup_toggled)
        gen_layout.addWidget(self.chk_startup)

        self.chk_tray_close = QCheckBox("Keep running in the background when window is closed (minimize to tray)")
        self.chk_tray_close.setChecked(self.config.get("minimize_to_tray_on_close", True))
        self.chk_tray_close.toggled.connect(lambda v: self.config.set("minimize_to_tray_on_close", v))
        gen_layout.addWidget(self.chk_tray_close)

        self.chk_tray_notify = QCheckBox("Show notification balloon when minimizing to tray")
        self.chk_tray_notify.setChecked(self.config.get("notify_on_minimize", True))
        self.chk_tray_notify.toggled.connect(lambda v: self.config.set("notify_on_minimize", v))
        gen_layout.addWidget(self.chk_tray_notify)

        layout.addWidget(card_gen)

        # Alerts Card
        card_alert = QFrame()
        card_alert.setStyleSheet("background-color: #18181B; border: 1px solid #27272A; border-radius: 8px; padding: 14px;")
        alert_layout = QVBoxLayout(card_alert)
        alert_layout.setSpacing(10)

        lbl_alert = QLabel("Low-Speed Alert Thresholds")
        lbl_alert.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        alert_layout.addWidget(lbl_alert)

        self.chk_low_speed = QCheckBox("Enable Low-Speed Notifications")
        self.chk_low_speed.setChecked(self.config.get("low_speed_alert_enabled", False))
        self.chk_low_speed.toggled.connect(lambda v: self.config.set("low_speed_alert_enabled", v))
        alert_layout.addWidget(self.chk_low_speed)

        thresh_box = QHBoxLayout()
        thresh_box.addWidget(QLabel("Notify when download speed falls below (KB/s):"))
        self.spin_threshold = QSpinBox()
        self.spin_threshold.setRange(10, 500000)
        self.spin_threshold.setValue(int(self.config.get("low_speed_threshold_kbps", 500)))
        self.spin_threshold.valueChanged.connect(lambda v: self.config.set("low_speed_threshold_kbps", v))
        thresh_box.addWidget(self.spin_threshold)
        alert_layout.addLayout(thresh_box)

        dur_box = QHBoxLayout()
        dur_box.addWidget(QLabel("Trigger notification after low speed persists for (seconds):"))
        self.spin_duration = QSpinBox()
        self.spin_duration.setRange(3, 300)
        self.spin_duration.setValue(int(self.config.get("low_speed_duration_seconds", 15)))
        self.spin_duration.valueChanged.connect(lambda v: self.config.set("low_speed_duration_seconds", v))
        dur_box.addWidget(self.spin_duration)
        alert_layout.addLayout(dur_box)

        layout.addWidget(card_alert)

        # Network Adapter Selector Card
        card_adapter = QFrame()
        card_adapter.setStyleSheet("background-color: #18181B; border: 1px solid #27272A; border-radius: 8px; padding: 14px;")
        ad_layout = QVBoxLayout(card_adapter)
        ad_layout.setSpacing(10)

        lbl_ad = QLabel("Network Adapter Selection")
        lbl_ad.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        ad_layout.addWidget(lbl_ad)

        ad_select_box = QHBoxLayout()
        ad_select_box.addWidget(QLabel("Monitored Interface:"))
        self.combo_interfaces = QComboBox()
        interfaces = NetworkMonitor.get_available_interfaces()
        self.combo_interfaces.addItems(interfaces)
        current_iface = self.config.get("selected_interface", "All Interfaces")
        idx = self.combo_interfaces.findText(current_iface)
        if idx >= 0:
            self.combo_interfaces.setCurrentIndex(idx)
        self.combo_interfaces.currentTextChanged.connect(self._on_interface_changed)
        ad_select_box.addWidget(self.combo_interfaces)
        ad_layout.addLayout(ad_select_box)

        layout.addWidget(card_adapter)

        # Maintenance & Reset
        card_maint = QFrame()
        card_maint.setStyleSheet("background-color: #18181B; border: 1px solid #27272A; border-radius: 8px; padding: 14px;")
        maint_layout = QHBoxLayout(card_maint)
        maint_layout.addWidget(QLabel("Data Management:"))
        maint_layout.addStretch()

        btn_clear_db = QPushButton("Clear Usage History")
        btn_clear_db.setStyleSheet("background-color: #DC2626; color: white;")
        btn_clear_db.clicked.connect(self._on_clear_history)
        maint_layout.addWidget(btn_clear_db)

        layout.addWidget(card_maint)
        layout.addStretch()
        return tab

    # =========================================================================
    # EVENT HANDLERS & UPDATES
    # =========================================================================
    def _on_tick(self) -> None:
        """1-second timer tick: updates real-time speed, graph, tray icon, and logs traffic."""
        data = self.monitor.update()
        down_bps = data["download_speed"]
        up_bps = data["upload_speed"]
        delta_recv = data["delta_recv"]
        delta_sent = data["delta_sent"]

        # Record to database
        self.db.record_delta_traffic(delta_recv, delta_sent, self.monitor.interface)

        # Update Live Cards
        self.card_down_speed["value"].setText(data["download_str"])
        self.card_up_speed["value"].setText(data["upload_str"])

        # Update Today Totals
        today_recv, today_sent = self.db.get_today_usage()
        self.card_today_down["value"].setText(format_bytes(today_recv))
        self.card_today_up["value"].setText(format_bytes(today_sent))

        # Update 60-Second Real-Time Graph
        self.speed_graph.add_data_point(down_bps, up_bps)

        # Update Tray Icon & Tooltip
        self.tray_icon.update_tray_icon(down_bps, up_bps)

        # Query Wi-Fi info (every 5 seconds)
        if not hasattr(self, "_wifi_counter"):
            self._wifi_counter = 0
        self._wifi_counter += 1
        if self._wifi_counter % 5 == 1:
            wifi_info = NetworkMonitor.get_wifi_and_connection_info()
            self._update_wifi_display(wifi_info)
            self.tray_icon.update_status_info(wifi_info, (today_recv, today_sent))

        # Low-speed evaluation
        self.alert_manager.check_speed(down_bps)

    def _update_wifi_display(self, wifi_info: dict) -> None:
        if wifi_info.get("is_wifi"):
            self.wifi_ssid_label.setText(f"SSID: {wifi_info.get('ssid')}")
            self.wifi_signal_label.setText(f"Signal: {wifi_info.get('signal')}")
            self.sidebar_status_badge.setText(f"● Wi-Fi: {wifi_info.get('ssid')}")
            self.sidebar_conn_label.setText(f"Wi-Fi: {wifi_info.get('ssid')}")
        else:
            self.wifi_ssid_label.setText(f"Network: {wifi_info.get('state', 'Connected')}")
            self.wifi_signal_label.setText("Type: Ethernet / LAN")
            self.sidebar_status_badge.setText("● LAN Connected")
            self.sidebar_conn_label.setText("Ethernet / LAN")

        self.wifi_ip_label.setText(f"Local IP: {wifi_info.get('local_ip', '127.0.0.1')}")
        self.wifi_adapter_label.setText(f"Adapter: {wifi_info.get('active_adapter', 'N/A')}")

    def _on_process_tick(self) -> None:
        """Periodic query for active application processes."""
        if self.tabs.currentIndex() != 1:
            return

        processes = self.process_monitor.get_active_network_processes(limit=30)
        self._populate_process_table(processes)

    def _populate_process_table(self, processes: list[dict]) -> None:
        filter_text = self.proc_search.text().lower()
        filtered = [p for p in processes if filter_text in p["name"].lower() or filter_text in str(p["pid"])]

        self.proc_table.setRowCount(len(filtered))
        for row, p in enumerate(filtered):
            name_item = QTableWidgetItem(p["name"])
            pid_item = QTableWidgetItem(str(p["pid"]))
            pid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            down_item = QTableWidgetItem(p["download_str"])
            down_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            down_item.setForeground(QColor("#38BDF8"))

            up_item = QTableWidgetItem(p["upload_str"])
            up_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            up_item.setForeground(QColor("#10B981"))

            data_item = QTableWidgetItem(p["total_data_str"])
            data_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            self.proc_table.setItem(row, 0, name_item)
            self.proc_table.setItem(row, 1, pid_item)
            self.proc_table.setItem(row, 2, down_item)
            self.proc_table.setItem(row, 3, up_item)
            self.proc_table.setItem(row, 4, data_item)

    def _filter_process_table(self) -> None:
        self._on_process_tick()

    def _refresh_analytics(self) -> None:
        """Fetch and populate analytics and historical records."""
        total_recv, total_sent = self.db.get_total_usage()
        self.all_time_down["value"].setText(format_bytes(total_recv))
        self.all_time_up["value"].setText(format_bytes(total_sent))
        self.all_time_total["value"].setText(format_bytes(total_recv + total_sent))

        # Weekly Table
        weekly = self.db.get_weekly_usage()
        self.weekly_table.setRowCount(len(weekly))
        for row, entry in enumerate(reversed(weekly)):
            self.weekly_table.setItem(row, 0, QTableWidgetItem(entry["date"]))
            self.weekly_table.setItem(row, 1, QTableWidgetItem(format_bytes(entry["bytes_recv"])))
            self.weekly_table.setItem(row, 2, QTableWidgetItem(format_bytes(entry["bytes_sent"])))
            self.weekly_table.setItem(row, 3, QTableWidgetItem(format_bytes(entry["total_bytes"])))

        # Speed Tests
        tests = self.db.get_speed_test_history(limit=15)
        self.speed_history_table.setRowCount(len(tests))
        for row, t in enumerate(tests):
            self.speed_history_table.setItem(row, 0, QTableWidgetItem(str(t["timestamp"])))
            self.speed_history_table.setItem(row, 1, QTableWidgetItem(f"{t['download_mbps']:.2f} Mbps"))
            self.speed_history_table.setItem(row, 2, QTableWidgetItem(f"{t['upload_mbps']:.2f} Mbps"))
            self.speed_history_table.setItem(row, 3, QTableWidgetItem(f"{t['ping_ms']:.1f} ms"))
            self.speed_history_table.setItem(row, 4, QTableWidgetItem(str(t["server"])))

    # =========================================================================
    # SPEED TEST ACTIONS
    # =========================================================================
    def _start_speed_test(self) -> None:
        self.btn_start_test.setEnabled(False)
        self.btn_cancel_test.setEnabled(True)
        self.st_progress.setValue(0)
        self.st_ping_card["value"].setText("-- ms")
        self.st_down_card["value"].setText("-- Mbps")
        self.st_up_card["value"].setText("-- Mbps")
        self.st_status_lbl.setText("Connecting to test server...")

        self.speedtest_worker = SpeedTestWorker(self)
        self.speedtest_worker.status_changed.connect(self.st_status_lbl.setText)
        self.speedtest_worker.progress_changed.connect(self.st_progress.setValue)
        self.speedtest_worker.partial_result.connect(self._on_speedtest_partial)
        self.speedtest_worker.finished.connect(self._on_speedtest_finished)
        self.speedtest_worker.error.connect(self._on_speedtest_error)
        self.speedtest_worker.start()

    def _cancel_speed_test(self) -> None:
        if self.speedtest_worker and self.speedtest_worker.isRunning():
            self.speedtest_worker.cancel()
            self.st_status_lbl.setText("Speed test cancelled")
        self.btn_start_test.setEnabled(True)
        self.btn_cancel_test.setEnabled(False)

    def _on_speedtest_partial(self, metric: str, value: float) -> None:
        if metric == "ping":
            self.st_ping_card["value"].setText(f"{value:.1f} ms")
        elif metric == "download":
            self.st_down_card["value"].setText(f"{value:.2f} Mbps")
        elif metric == "upload":
            self.st_up_card["value"].setText(f"{value:.2f} Mbps")

    def _on_speedtest_finished(self, results: dict) -> None:
        self.btn_start_test.setEnabled(True)
        self.btn_cancel_test.setEnabled(False)
        self.st_progress.setValue(100)
        self.st_status_lbl.setText("Speed test finished successfully!")

        # Save to database
        self.db.record_speed_test(
            results["download_mbps"],
            results["upload_mbps"],
            results["ping_ms"],
            results["server"]
        )

    def _on_speedtest_error(self, err_msg: str) -> None:
        self.btn_start_test.setEnabled(True)
        self.btn_cancel_test.setEnabled(False)
        self.st_status_lbl.setText(err_msg)

    # =========================================================================
    # SETTINGS ACTIONS
    # =========================================================================
    def _on_setting_startup_toggled(self, checked: bool) -> None:
        self.startup.set_auto_start(checked)
        self.config.set("auto_start", checked)
        self.tray_icon.startup_action.setChecked(checked)

    def _on_interface_changed(self, iface_name: str) -> None:
        self.config.set("selected_interface", iface_name)
        self.monitor.interface = iface_name
        self.monitor.last_recv, self.monitor.last_sent = self.monitor._get_raw_counters()

    def _on_clear_history(self) -> None:
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Are you sure you want to clear all historical usage and speed test logs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_history()
            self._refresh_analytics()
            QMessageBox.information(self, "History Cleared", "All usage logs have been cleared.")

    def show_toast_notification(self, title: str, message: str) -> None:
        """Display native Windows toast notification balloon via the system tray."""
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Warning, 4000)

    # =========================================================================
    # LIFECYCLE & BACKGROUND EXECUTION
    # =========================================================================
    def closeEvent(self, event) -> None:
        """
        Intercept close event to keep application running in the background tray
        unless force_quit is explicitly invoked from the tray menu.
        """
        if self._is_force_quitting or not self.config.get("minimize_to_tray_on_close", True):
            event.accept()
        else:
            event.ignore()
            self.hide()
            if self.config.get("notify_on_minimize", True):
                self.tray_icon.showMessage(
                    "Yaze Network Monitor",
                    "Yaze is running continuously in the background.\nRight-click the tray icon to exit or reopen.",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )
                self.config.set("notify_on_minimize", False)

    def force_quit(self) -> None:
        """Explicit exit action called only from tray menu."""
        self._is_force_quitting = True
        self.timer.stop()
        self.proc_timer.stop()
        if self.speedtest_worker and self.speedtest_worker.isRunning():
            self.speedtest_worker.cancel()
            self.speedtest_worker.wait(1000)
        self.close()
        QApplication.quit()
