"""Studio Minimalist design system and stylesheets for Yaze."""

DARK_THEME_QSS = """
/* Base Window & Global Styles */
QMainWindow, QDialog {
    background-color: #121214;
    color: #FFFFFF;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
}

QWidget {
    color: #F4F4F5;
    font-size: 13px;
    selection-background-color: #27272A;
    selection-color: #FFFFFF;
}

/* Sidebar Navigation Rail */
QFrame#sidebar {
    background-color: #0E0E10;
    border-right: 1px solid #27272A;
}

QPushButton.nav-item {
    background-color: transparent;
    color: #A1A1AA;
    border: none;
    border-radius: 6px;
    padding: 10px 14px;
    font-weight: 600;
    font-size: 13px;
    text-align: left;
}

QPushButton.nav-item:hover {
    background-color: #18181B;
    color: #FFFFFF;
}

QPushButton.nav-item:checked, QPushButton.nav-item.active {
    background-color: #27272A;
    color: #FFFFFF;
    font-weight: 700;
    border-left: 3px solid #38BDF8;
}

/* Card Surface Panels */
QFrame.card {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 8px;
    padding: 12px;
}

QFrame.card:hover {
    border: 1px solid #3F3F46;
}

/* Primary Action Buttons */
QPushButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #3B82F6;
}

QPushButton:pressed {
    background-color: #1D4ED8;
}

QPushButton:disabled {
    background-color: #27272A;
    color: #71717A;
}

/* Secondary & Utility Buttons */
QPushButton.secondary {
    background-color: #18181B;
    color: #E4E4E7;
    border: 1px solid #27272A;
}

QPushButton.secondary:hover {
    background-color: #27272A;
    color: #FFFFFF;
    border: 1px solid #3F3F46;
}

QPushButton.danger {
    background-color: #DC2626;
    color: #FFFFFF;
}

QPushButton.danger:hover {
    background-color: #EF4444;
}

/* Table View */
QTableWidget {
    background-color: #18181B;
    gridline-color: #27272A;
    border: 1px solid #27272A;
    border-radius: 8px;
    selection-background-color: #27272A;
    selection-color: #38BDF8;
    alternate-background-color: #141416;
}

QHeaderView::section {
    background-color: #121214;
    color: #A1A1AA;
    padding: 8px 10px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border: none;
    border-bottom: 1px solid #27272A;
}

QTableWidget::item {
    padding: 7px 10px;
    border-bottom: 1px solid #1E1E22;
}

QTableWidget::item:selected {
    background-color: #27272A;
    color: #FFFFFF;
}

/* Progress Bar */
QProgressBar {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 6px;
    text-align: center;
    color: #FFFFFF;
    font-weight: 600;
    font-size: 12px;
    height: 22px;
}

QProgressBar::chunk {
    background-color: #38BDF8;
    border-radius: 5px;
}

/* Inputs & Combo Boxes */
QLineEdit, QSpinBox, QComboBox {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 6px;
    padding: 7px 12px;
    color: #FFFFFF;
    font-size: 13px;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #38BDF8;
    background-color: #1C1C20;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #18181B;
    border: 1px solid #27272A;
    color: #FFFFFF;
    selection-background-color: #27272A;
    selection-color: #38BDF8;
    padding: 4px;
}

/* Checkbox */
QCheckBox {
    spacing: 10px;
    color: #F4F4F5;
    font-weight: 500;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #3F3F46;
    background-color: #18181B;
}

QCheckBox::indicator:hover {
    border: 1px solid #71717A;
}

QCheckBox::indicator:checked {
    background-color: #38BDF8;
    border: 1px solid #38BDF8;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background-color: #121214;
    width: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #27272A;
    border-radius: 3px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background-color: #3F3F46;
}

QScrollBar:horizontal {
    border: none;
    background-color: #121214;
    height: 6px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #27272A;
    border-radius: 3px;
    min-width: 24px;
}
"""
