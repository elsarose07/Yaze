"""High-performance antialiased real-time network speed graph widget."""

from collections import deque
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont
from PyQt6.QtWidgets import QWidget
from core.network_monitor import format_speed

class SpeedGraphWidget(QWidget):
    """Visualizes live download and upload speeds over a rolling 60-second window."""

    def __init__(self, history_points: int = 60, parent=None):
        super().__init__(parent)
        self.history_points = history_points
        self.download_history = deque([0.0] * history_points, maxlen=history_points)
        self.upload_history = deque([0.0] * history_points, maxlen=history_points)

        self.current_down = 0.0
        self.current_up = 0.0
        self.peak_down = 0.0
        self.peak_up = 0.0

        self.setMinimumHeight(220)
        self.setStyleSheet("background-color: #18181B; border: 1px solid #27272A; border-radius: 8px;")

    def add_data_point(self, download_bps: float, upload_bps: float) -> None:
        """Append new sample to the rolling history and request a repaint."""
        self.current_down = download_bps
        self.current_up = upload_bps

        if download_bps > self.peak_down:
            self.peak_down = download_bps
        if upload_bps > self.peak_up:
            self.peak_up = upload_bps

        self.download_history.append(download_bps)
        self.upload_history.append(upload_bps)
        self.update()

    def reset_peaks(self) -> None:
        """Reset historical peak metrics."""
        self.peak_down = self.current_down
        self.peak_up = self.current_up
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Layout boundaries
        left_margin = 65
        right_margin = 20
        top_margin = 40
        bottom_margin = 26

        plot_w = max(10, w - left_margin - right_margin)
        plot_h = max(10, h - top_margin - bottom_margin)

        # 1. Background Fill & Rounded Border
        painter.setPen(QColor("#27272A"))
        painter.setBrush(QColor("#18181B"))
        painter.drawRoundedRect(QRectF(0, 0, w, h), 8, 8)

        # Determine ceiling scale (minimum 100 KB/s to prevent visual noise)
        max_val = max(max(self.download_history), max(self.upload_history), 100 * 1024)
        max_scale = max_val * 1.15

        # 2. Draw Horizontal Grid Lines & Y-axis labels
        grid_pen = QPen(QColor("#27272A"), 1, Qt.PenStyle.SolidLine)
        text_pen = QPen(QColor("#71717A"))
        axis_font = QFont("Segoe UI", 8)
        painter.setFont(axis_font)

        num_divisions = 4
        for i in range(num_divisions + 1):
            y_ratio = i / num_divisions
            y_pos = top_margin + plot_h * (1.0 - y_ratio)
            val_at_grid = max_scale * y_ratio

            # Grid Line
            painter.setPen(grid_pen)
            painter.drawLine(int(left_margin), int(y_pos), int(left_margin + plot_w), int(y_pos))

            # Y-Axis Text Label
            painter.setPen(text_pen)
            painter.drawText(
                QRectF(4, y_pos - 8, left_margin - 8, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                format_speed(val_at_grid)
            )

        # 3. Draw X-Axis Time Labels
        painter.setPen(text_pen)
        time_labels = [("-60s", 0.0), ("-45s", 0.25), ("-30s", 0.5), ("-15s", 0.75), ("Now", 1.0)]
        for lbl, ratio in time_labels:
            x_pos = left_margin + plot_w * ratio
            painter.drawText(
                QRectF(x_pos - 20, h - bottom_margin + 6, 40, 16),
                Qt.AlignmentFlag.AlignCenter,
                lbl
            )

        # 4. Plot Curves
        pts_down: list[QPointF] = []
        pts_up: list[QPointF] = []

        n = len(self.download_history)
        step_x = plot_w / max(1, n - 1)

        for i in range(n):
            x = left_margin + i * step_x

            # Download Y
            y_d_ratio = min(1.0, self.download_history[i] / max_scale)
            y_d = top_margin + plot_h * (1.0 - y_d_ratio)
            pts_down.append(QPointF(x, y_d))

            # Upload Y
            y_u_ratio = min(1.0, self.upload_history[i] / max_scale)
            y_u = top_margin + plot_h * (1.0 - y_u_ratio)
            pts_up.append(QPointF(x, y_u))

        # Helper to draw filled area and line
        def draw_stream(pts, stroke_color, grad_top_color):
            if not pts:
                return

            path_pts = [QPointF(pts[0].x(), top_margin + plot_h)] + pts + [QPointF(pts[-1].x(), top_margin + plot_h)]
            gradient = QLinearGradient(0, top_margin, 0, top_margin + plot_h)
            gradient.setColorAt(0.0, grad_top_color)
            gradient.setColorAt(1.0, QColor(0, 0, 0, 0))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawPolygon(path_pts)

            # Stroke Line
            pen = QPen(stroke_color, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for i in range(len(pts) - 1):
                painter.drawLine(pts[i], pts[i + 1])

        # Draw Upload (Emerald)
        draw_stream(pts_up, QColor("#10B981"), QColor(16, 185, 129, 35))

        # Draw Download (Cyan)
        draw_stream(pts_down, QColor("#38BDF8"), QColor(56, 189, 248, 55))

        # 5. Header / Telemetry Legend
        header_font = QFont("Segoe UI", 9, QFont.Weight.DemiBold)
        painter.setFont(header_font)

        # Download Badge
        painter.setPen(QColor("#38BDF8"))
        down_legend = f"● Download: {format_speed(self.current_down)}   (Peak: {format_speed(self.peak_down)})"
        painter.drawText(left_margin + 4, 24, down_legend)

        # Upload Badge
        painter.setPen(QColor("#10B981"))
        up_legend = f"● Upload: {format_speed(self.current_up)}   (Peak: {format_speed(self.peak_up)})"
        painter.drawText(left_margin + 330, 24, up_legend)

        painter.end()
