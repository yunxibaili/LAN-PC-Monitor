# -*- coding: utf-8 -*-
"""
副机端本机仪表盘面板 —— 显示本机全部采集数据（见《技术文档.md》§6.2 / §20.8）。

- 窗口顶部：本机主机名、IP、运行时间、"本机模式"标识、本机采集节点 token。
- 中部：按分区显示本机全部采集数据（CPU/GPU/内存/磁盘/网络/帧率/进程）。
- 数值实时刷新，阈值变色（绿/橙/红三级）。
- 复用 host/gui/detail_panel 的 DetailPanel 分区渲染逻辑，改为本机专用头。

IP 显示：优先取帧内 system.local_ip；若为空（采集器预热未完成等），
兜底用 get_lan_ip() 直接获取，保证仪表盘一定显示本机局域网 IP。
token 显示：读取本机 node_config.json 的 token（该电脑作为采集节点时
别人连接所需），若未部署节点则显示 "—"。
"""
import logging
import os

from PyQt5.QtWidgets import QLabel

from common.utils import format_uptime, get_lan_ip
from host.gui.detail_panel import DetailPanel

log = logging.getLogger("client.gui.local_panel")

# 采集节点配置文件路径（本机 token 来源）
NODE_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "node_config.json")


def _read_local_token() -> str:
    """读取本机 node_config.json 的 token；文件不存在或解析失败返回空串。"""
    try:
        import json
        with open(NODE_CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg.get("token", "")
    except Exception:
        return ""


class LocalPanel(DetailPanel):
    """
    本机仪表盘面板（继承 DetailPanel 的分区渲染能力）。

    额外提供：
    - update_local(frame)：更新本机仪表盘（顶部显示主机名/IP/uptime/本机模式/token）
    """

    def __init__(self):
        super().__init__()
        # 缓存兜底 IP（在构造时获取一次，避免每次刷新都探测网卡）
        self._fallback_ip = get_lan_ip()

    def _update_header(self, frame: dict) -> None:
        """顶部：本机主机名 / IP / uptime / 本机模式 / token。"""
        sys_info = frame.get("system", {})
        uptime = format_uptime(sys_info.get("uptime_seconds", 0))

        # IP：优先帧内值，空则兜底直接获取
        ip = sys_info.get("local_ip") or self._fallback_ip or "N/A"
        # token：读本机 node_config.json，方便用户查看/告知他人连接
        token = _read_local_token() or "—"

        self.header_label.setText(
            f"本机: {frame.get('hostname', 'N/A')}  |  "
            f"IP: {ip}  |  "
            f"运行: {uptime}  |  本机模式  |  "
            f"Token: {token}")
        self.header_label.setToolTip("Token 为本机采集节点的连接密钥，"
                                     "其他电脑添加本机节点时需要填写")
