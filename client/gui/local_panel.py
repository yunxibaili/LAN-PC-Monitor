# -*- coding: utf-8 -*-
"""
副机端本机仪表盘面板 —— 显示本机全部采集数据（见《技术文档.md》§6.2 / §20.8）。

- 窗口顶部：本机主机名、IP、运行时间、"本机模式"标识。
- 中部：按分区显示本机全部采集数据（CPU/GPU/内存/磁盘/网络/帧率/进程）。
- 数值实时刷新，阈值变色（绿/橙/红三级）。
- 复用 host/gui/detail_panel 的 DetailPanel 分区渲染逻辑，改为本机专用头。
"""
import logging

from PyQt5.QtWidgets import (QLabel, QVBoxLayout, QWidget)

from common import theme
from common.theme import apply_color
from common.utils import format_uptime
from host.gui.detail_panel import DetailPanel, _fmt

log = logging.getLogger("client.gui.local_panel")


class LocalPanel(DetailPanel):
    """
    本机仪表盘面板（继承 DetailPanel 的分区渲染能力）。

    额外提供：
    - update_local(frame)：更新本机仪表盘（顶部显示主机名/IP/uptime/本机模式）
    """

    def _update_header(self, frame: dict) -> None:
        """顶部：本机主机名 / IP / uptime / 本机模式。"""
        sys_info = frame.get("system", {})
        uptime = format_uptime(sys_info.get("uptime_seconds", 0))
        self.header_label.setText(
            f"本机: {frame.get('hostname', 'N/A')}  |  "
            f"IP: {sys_info.get('local_ip', 'N/A')}  |  "
            f"运行: {uptime}  |  本机模式")
