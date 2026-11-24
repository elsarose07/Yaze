"""Modern dark/fluent design system and stylesheets for Yaze."""

DARK_THEME_QSS = """
/* Base Window & Background */
QMainWindow, QDialog {
    background-color: #0F172A;
    color: #F8FAFC;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
}

QWidget {
    color: #F8FAFC;
    font-size: 13px;
}

/* Card Panels */
QFrame.card {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 12px;
}

QFrame.card:hover {
    border: 1px solid #475569;
}

/* Tab Navigation */
QTabWidget::pane {
    border: 1px solid #334155;
    background-color: #0F172A;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #1E293B;
    color: #94A3B8;
    padding: 10px 22px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #334155;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #0F172A;
    color: #38BDF8;
    border-bottom: 2px solid #38BDF8;
}

QTabBar::tab:hover:!selected {
    background-color: #334155;
    color: #F1F5F9;
}

/* Buttons */
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
    background-color: #334155;
    color: #64748B;
}

QPushButton.secondary {
    background-color: #334155;
    color: #F8FAFC;
    border: 1px solid #475569;
}

QPushButton.secondary:hover {
    background-color: #475569;
}

QPushButton.danger {
    background-color: #DC2626;
}

QPushButton.danger:hover {
    background-color: #EF4444;
}

/* Table View */
QTableWidget {
    background-color: #1E293B;
    gridline-color: #334155;
    border: 1px solid #334155;
    border-radius: 8px;
    selection-background-color: #334155;
    selection-color: #38BDF8;
}

QHeaderView::section {
    background-color: #0F172A;
    color: #94A3B8;
    padding: 8px;
    font-weight: 600;
    border: none;
    border-bottom: 1px solid #334155;
}

QTableWidget::item {
    padding: 6px;
}

/* Progress Bar */
QProgressBar {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 6px;
    text-align: center;
    color: #F8FAFC;
    font-weight: bold;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #38BDF8;
    border-radius: 5px;
}

/* Inputs & Combo Boxes */
QLineEdit, QSpinBox, QComboBox {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    color: #F8FAFC;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #38BDF8;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1E293B;
    border: 1px solid #334155;
    color: #F8FAFC;
    selection-background-color: #38BDF8;
    selection-color: #0F172A;
}

/* Checkbox */
QCheckBox {
    spacing: 8px;
    color: #F8FAFC;
    font-weight: 500;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #475569;
    background-color: #1E293B;
}

QCheckBox::indicator:checked {
    background-color: #38BDF8;
    border: 1px solid #38BDF8;
}

/* ScrollBar */
QScrollBar:vertical {
    border: none;
    background-color: #0F172A;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #334155;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
