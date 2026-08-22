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
            self._curves = []            # [PlotDataItem]
            self._curve_map = {}         # name -> PlotDataItem
            self._series_data = {}       # name -> [(x, y), ...]
            self._warn_line = None
            self._danger_line = None
            self._window_sec = None      # None=显示全部；N=滚动最近N秒
            self._show_x_values = True
            self._setup()
            self._lock_interaction()

        def set_window_seconds(self, seconds) -> None:
            """设置滚动窗口秒数；None/0 表示显示全部数据。"""
            if seconds is None:
                self._window_sec = None
            else:
                self._window_sec = max(1, int(seconds))

        def set_show_x_values(self, show: bool) -> None:
            """是否显示 X 轴刻度数值。"""
            self._show_x_values = bool(show)
            self.getAxis("bottom").setStyle(showValues=self._show_x_values)

        # ---- 锁定交互：只读展示，禁用一切用户操作 ----

        def _lock_interaction(self):
            """折线图仅作展示，不允许用户缩放/平移/选择/右键菜单/滚轮等。"""
            self.setMouseEnabled(x=False, y=False)
            self.setMenuEnabled(False)
            self.hideButtons()
            self.setFocusPolicy(Qt.NoFocus)
            vb = self.getViewBox()
            if vb is not None:
                vb.setMouseEnabled(x=False, y=False)
                vb.setCursor(Qt.ForbiddenCursor)

        def wheelEvent(self, ev):
            ev.ignore()

        def keyPressEvent(self, ev):
            ev.ignore()

        def mousePressEvent(self, ev):
            ev.ignore()

        def mouseMoveEvent(self, ev):
            ev.ignore()

        def mouseReleaseEvent(self, ev):
            ev.ignore()

        def mouseDoubleClickEvent(self, ev):
            ev.ignore()

        def contextMenuEvent(self, ev):
            ev.ignore()

        def leaveEvent(self, ev):
            ev.ignore()

        def _setup(self):
            self.setBackground(TC.BG_BASE)
            self.showGrid(x=True, y=True, alpha=0.3)
            self.setLabel("left", self._title, color=TC.TEXT_PRIMARY)
            self.setLabel("bottom", "时间", color=TC.TEXT_DISABLED)
            self.getAxis("bottom").setStyle(showValues=self._show_x_values)
            self.getAxis("bottom").setPen(pg.mkPen(color=TC.TEXT_DISABLED))
            self.getAxis("left").setPen(pg.mkPen(color=TC.TEXT_DISABLED))
            if self._y_range:
                self.setYRange(self._y_range[0], self._y_range[1], padding=0)

        # ---- 数据接口 ----

        def set_series(self, points, color=TC.CHART_PRIMARY) -> None:
            """单曲线（向后兼容）。"""
            self.reset()
            if not points:
                return
            self.set_multi_series({"Data": (points, color)})

        def set_multi_series(self, series: dict) -> None:
            """
            多曲线叠加（增量更新）。
            series: {name: (points, color)}
              points: 有 .timestamp / .value
            复用已存在的曲线对象，仅用 setData() 更新点，避免重复重建对象。
            """
            # 移除本次未出现的旧曲线
            active = set(series.keys())
            for name in list(self._curve_map.keys()):
                if name not in active:
                    c = self._curve_map.pop(name)
                    if c in self._curves:
                        self._curves.remove(c)
                    self.removeItem(c)

            if not series:
                self._series_data.clear()
                return

            all_x = []
            for name, (points, color) in series.items():
                if not points:
                    continue
                x_vals = [p.timestamp for p in points]
                y_vals = [p.value for p in points]
                all_x.extend(x_vals)
                self._series_data[name] = list(zip(x_vals, y_vals))

                curve = self._curve_map.get(name)
                if curve is None:
                    pen = pg.mkPen(color=color, width=2)
                    curve = self.plot(x_vals, y_vals, pen=pen)
                    self._curve_map[name] = curve
                    self._curves.append(curve)
                else:
                    curve.setData(x=x_vals, y=y_vals)

            # 滚动窗口：window_sec 为 None 时显示全部，否则固定最近 N 秒
            window_sec = self._window_sec
            if all_x and window_sec:
                now = max(all_x)
                self.setXRange(now - window_sec, now, padding=0)

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

        def reset(self) -> None:
            """清空图表（避免与 pyqtgraph PlotItem.clear 重名冲突）。"""
            for c in self._curves:
                self.removeItem(c)
            self._curves.clear()
            self._curve_map.clear()
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
            lbl.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: {TT.BODY_SMALL['size']}px;")
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)

        def set_series(self, points, color=TC.CHART_PRIMARY):
            pass

        def set_multi_series(self, series):
            pass

        def set_thresholds(self, warn=None, danger=None):
            pass

        def set_window_seconds(self, seconds):
            pass

        def set_show_x_values(self, show):
            pass

        def reset(self):
            pass
