# -*- coding: utf-8 -*-
"""
ChartWidget —— 实时折线图组件（v5.2 Phase 3-5C）。

纯 UI 组件：接收 ChartPoint 列表并渲染折线图。
- 优先使用 pyqtgraph
- 无 pyqtgraph 时回退到空白 QWidget（不阻塞 Host 启动）
- 不访问 HistoryStore / FrameStore / NodeStore / MonitorViewModel
"""
import logging

log = logging.getLogger("host.gui.widgets.chart_widget")

from host.gui.theme.colors import ThemeColors as TC

# pyqtgraph 惰性导入
try:
    import pyqtgraph as pg
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QWidget
    _HAS_PG = True
except ImportError:
    _HAS_PG = False
    log.info("pyqtgraph 未安装，ChartWidget 将使用空白回退")


def has_pyqtgraph() -> bool:
    return _HAS_PG


if _HAS_PG:
    class ChartWidget(pg.PlotWidget):
        """实时折线图：接收 ChartPoint 列表渲染。"""

        def __init__(self, title: str = "", y_range: tuple = (0, 100),
                     parent=None):
            super().__init__(parent)
            self._title = title
            self._y_range = y_range
            self._curve = None
            self._warn_line = None
            self._danger_line = None
            self._setup()

        def _setup(self):
            self.setBackground(TC.BG_BASE)
            self.showGrid(x=True, y=True, alpha=0.3)
            self.setLabel("left", self._title, color=TC.TEXT_PRIMARY)
            self.setLabel("bottom", "时间 (s)", color=TC.TEXT_DISABLED)
            self.getAxis("bottom").setPen(pg.mkPen(color=TC.TEXT_DISABLED))
            self.getAxis("left").setPen(pg.mkPen(color=TC.TEXT_DISABLED))
            if self._y_range:
                self.setYRange(self._y_range[0], self._y_range[1], padding=0)
            self._curve = self.plot(pen=pg.mkPen(color=TC.CHART_PRIMARY, width=2),
                                    fillLevel=0, brush=pg.mkBrush(0, 122, 204, 30))

        def set_series(self, points, color=TC.CHART_PRIMARY) -> None:
            """设置数据点列表（list of ChartPoint）。"""
            if not points:
                self.clear()
                return
            x_vals = [p.timestamp for p in points]
            y_vals = [p.value for p in points]
            # 归一化 X 轴为相对时间（秒）
            t0 = x_vals[0] if x_vals else 0
            x_rel = [t - t0 for t in x_vals]
            self._curve.setData(x_rel, y_vals, pen=pg.mkPen(color=color, width=2))

        def set_thresholds(self, warn=None, danger=None) -> None:
            """设置阈值参考线。"""
            # 移除旧线
            if self._warn_line:
                self.removeItem(self._warn_line)
                self._warn_line = None
            if self._danger_line:
                self.removeItem(self._danger_line)
                self._danger_line = None
            # 添加新线
            if warn is not None:
                self._warn_line = pg.InfiniteLine(
                    pos=warn, angle=0, pen=pg.mkPen(
                        color=TC.CHART_THRESHOLD_WARN, style=Qt.DashLine, width=1))
                self.addItem(self._warn_line)
            if danger is not None:
                self._danger_line = pg.InfiniteLine(
                    pos=danger, angle=0, pen=pg.mkPen(
                        color=TC.CHART_THRESHOLD_DANGER, style=Qt.DashLine, width=1))
                self.addItem(self._danger_line)

        def clear(self) -> None:
            """清空图表。"""
            if self._curve:
                self._curve.setData([], [])

else:
    # pyqtgraph 不可用时的空白回退
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

    class ChartWidget(QWidget):
        """空白回退：pyqtgraph 不可用时保持接口兼容。"""

        def __init__(self, title: str = "", y_range: tuple = (0, 100),
                     parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(8, 8, 8, 8)
            lbl = QLabel(f"[{title}] pyqtgraph 未安装，图表不可用")
            lbl.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: 12px;")
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)

        def set_series(self, points, color=TC.CHART_PRIMARY) -> None:
            pass

        def set_thresholds(self, warn=None, danger=None) -> None:
            pass

        def clear(self) -> None:
            pass
