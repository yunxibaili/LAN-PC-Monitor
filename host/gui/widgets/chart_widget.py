# -*- coding: utf-8 -*-
"""
ChartWidget —— 折线图组件（v5.3.3 增强）。

支持：
  - 单曲线 / 多曲线叠加
  - 十字准线 + tooltip（时间 + 值）
  - 自适应时间格式 X 轴
  - 阈值参考线

优先使用 pyqtgraph；不可用时回退空白 QWidget。
不访问 Store / Facade / Repository。
"""
import logging
import time as _time
from datetime import datetime

log = logging.getLogger("host.gui.widgets.chart_widget")

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT

try:
    import pyqtgraph as pg
    from PyQt5.QtCore import Qt, QPointF
    from PyQt5.QtWidgets import QWidget, QGraphicsSimpleTextItem
    _HAS_PG = True
except ImportError:
    _HAS_PG = False
    log.info("pyqtgraph 未安装，ChartWidget 将使用空白回退")


def has_pyqtgraph() -> bool:
    return _HAS_PG


# ---------- 格式化工具 ----------

def _fmt_time(ts):
    """时间戳 → 短字符串（自适应精度）。"""
    try:
        dt = datetime.fromtimestamp(ts)
    except (OSError, ValueError, OverflowError):
        return str(ts)
    now = datetime.now()
    delta = (now - dt).total_seconds()
    if delta < 3600:
        return dt.strftime("%H:%M:%S")
    elif delta < 86400:
        return dt.strftime("%H:%M")
    else:
        return dt.strftime("%m-%d %H:%M")


def _fmt_value(v):
    """数值格式化（自动精度）。"""
    if v is None:
        return "N/A"
    if abs(v) >= 100:
        return f"{v:.0f}"
    if abs(v) >= 10:
        return f"{v:.1f}"
    return f"{v:.2f}"


if _HAS_PG:
    class ChartWidget(pg.PlotWidget):
        """折线图：单/多曲线 + 十字准线 + tooltip。"""

        def __init__(self, title: str = "", y_range: tuple = (0, 100),
                     parent=None):
            super().__init__(parent)
            self._title = title
            self._y_range = y_range
            self._curves = []
            self._series_data = {}   # name -> [(x, y), ...]
            self._warn_line = None
            self._danger_line = None
            self._setup()
            self._setup_crosshair()

        def _setup(self):
            self.setBackground(TC.BG_BASE)
            self.showGrid(x=True, y=True, alpha=0.3)
            self.setLabel("left", self._title, color=TC.TEXT_PRIMARY)
            self.setLabel("bottom", "时间", color=TC.TEXT_DISABLED)
            self.getAxis("bottom").setPen(pg.mkPen(color=TC.TEXT_DISABLED))
            self.getAxis("left").setPen(pg.mkPen(color=TC.TEXT_DISABLED))
            if self._y_range:
                self.setYRange(self._y_range[0], self._y_range[1], padding=0)

        # ---- 十字准线 + Tooltip ----

        def _setup_crosshair(self):
            self._vLine = pg.InfiniteLine(
                angle=90, movable=False,
                pen=pg.mkPen(color=TC.TEXT_DISABLED, style=Qt.DashLine, width=1))
            self._hLine = pg.InfiniteLine(
                angle=0, movable=False,
                pen=pg.mkPen(color=TC.TEXT_DISABLED, style=Qt.DashLine, width=1))
            self._vLine.setVisible(False)
            self._hLine.setVisible(False)
            self.addItem(self._vLine, ignoreBounds=True)
            self.addItem(self._hLine, ignoreBounds=True)

            self._tooltip = QGraphicsSimpleTextItem()
            self._tooltip.setBrush(pg.mkBrush(30, 30, 30, 220))
            self._tooltip.setPen(pg.mkPen(color=TC.TEXT_DISABLED))
            self._tooltip.setVisible(False)
            self._tooltip.setZValue(100)
            self.addItem(self._tooltip)

        def mouseMoveEvent(self, ev):
            super().mouseMoveEvent(ev)
            pos = ev.pos()
            mouse_point = self.getViewBox().mapToView(pos)
            x = mouse_point.x()
            y = mouse_point.y()

            self._vLine.setVisible(True)
            self._hLine.setVisible(True)
            self._vLine.setPos(x)
            self._hLine.setPos(y)

            # 查找最近数据点
            lines = []
            for name, data in self._series_data.items():
                if not data:
                    continue
                # 二分查找最近 x
                lo, hi = 0, len(data) - 1
                while lo < hi:
                    mid = (lo + hi) // 2
                    if data[mid][0] < x:
                        lo = mid + 1
                    else:
                        hi = mid
                idx = lo
                if idx > 0 and abs(data[idx - 1][0] - x) < abs(data[idx][0] - x):
                    idx -= 1
                ts, val = data[idx]
                lines.append(f"{name}: {_fmt_value(val)}%")

            time_str = _fmt_time(x) if x > 0 else ""
            tooltip_text = f"{time_str}\n" + "\n".join(lines) if lines else time_str
            self._tooltip.setText(tooltip_text)
            self._tooltip.setPos(pos.x() + 15, pos.y() - 10)
            self._tooltip.setVisible(True)

        def leaveEvent(self, ev):
            super().leaveEvent(ev)
            self._vLine.setVisible(False)
            self._hLine.setVisible(False)
            self._tooltip.setVisible(False)

        # ---- 数据接口 ----

        def set_series(self, points, color=TC.CHART_PRIMARY) -> None:
            """单曲线（向后兼容）。"""
            self.clear()
            if not points:
                return
            self.set_multi_series({"Data": (points, color)})

        def set_multi_series(self, series: dict) -> None:
            """
            多曲线叠加。
            series: {name: (points, color)}
              points: MetricRecord 列表（有 .timestamp, .value）
            """
            # 清除旧曲线
            for c in self._curves:
                self.removeItem(c)
            self._curves.clear()
            self._series_data.clear()

            if not series:
                return

            all_x = []
            for name, (points, color) in series.items():
                if not points:
                    continue
                x_vals = [p.timestamp for p in points]
                y_vals = [p.value for p in points]
                all_x.extend(x_vals)
                self._series_data[name] = list(zip(x_vals, y_vals))

                pen = pg.mkPen(color=color, width=2)
                curve = self.plot(x_vals, y_vals, pen=pen)
                self._curves.append(curve)

            # X 轴自适应格式
            if all_x:
                span = max(all_x) - min(all_x)
                if span < 600:
                    self.setLabel("bottom", "时间 (秒)", color=TC.TEXT_DISABLED)
                else:
                    self.setLabel("bottom", "", color=TC.TEXT_DISABLED)
                    self.getAxis("bottom").setTickValues(all_x)

        def set_thresholds(self, warn=None, danger=None) -> None:
            """设置阈值参考线。"""
            if self._warn_line:
                self.removeItem(self._warn_line)
                self._warn_line = None
            if self._danger_line:
                self.removeItem(self._danger_line)
                self._danger_line = None
            if warn is not None:
                self._warn_line = pg.InfiniteLine(
                    pos=warn, angle=0, pen=pg.mkPen(
                        color=TC.CHART_THRESHOLD_WARN,
                        style=Qt.DashLine, width=1))
                self.addItem(self._warn_line)
            if danger is not None:
                self._danger_line = pg.InfiniteLine(
                    pos=danger, angle=0, pen=pg.mkPen(
                        color=TC.CHART_THRESHOLD_DANGER,
                        style=Qt.DashLine, width=1))
                self.addItem(self._danger_line)

        def clear(self) -> None:
            """清空图表。"""
            for c in self._curves:
                self.removeItem(c)
            self._curves.clear()
            self._series_data.clear()

else:
    # ---- pyqtgraph 不可用：空白回退 ----
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

    class ChartWidget(QWidget):
        def __init__(self, title="", y_range=(0, 100), parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(8, 8, 8, 8)
            lbl = QLabel(f"[{title}] pyqtgraph 未安装，图表不可用")
            lbl.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: TT.BODY_SMALL['size']px;")
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)

        def set_series(self, points, color=TC.CHART_PRIMARY):
            pass

        def set_multi_series(self, series):
            pass

        def set_thresholds(self, warn=None, danger=None):
            pass

        def clear(self):
            pass
