# -*- coding: utf-8 -*-
"""
副机端本机仪表盘面板 —— 显示本机全部采集数据（见《技术文档.md》§6.2 / §20.8）。

- 窗口顶部：本机主机名、IP、运行时间、"本机模式"标识。
- **连接信息区**：IP / 端口 / Token / 连接码 用只读输入框展示，可一键复制（§2.5）。
- 中部：按分区显示本机全部采集数据（CPU/GPU/内存/磁盘/网络/帧率/进程）。
- 数值实时刷新，阈值变色（绿/橙/红三级）。
- 复用 host/gui/detail_panel 的 DetailPanel 分区渲染逻辑，改为本机专用头。

IP 显示：优先取帧内 system.local_ip；若为空（采集器预热未完成等），
兜底用 get_lan_ip() 直接获取，保证仪表盘一定显示本机局域网 IP。
Token/连接码：读取本机 node_config.json 与 make_connect_code 生成。
"""
import logging
import os

from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout, QWidget)

from common.utils import format_uptime, get_lan_ip
from host.gui.detail_panel import DetailPanel

log = logging.getLogger("client.gui.local_panel")

# 采集节点配置文件路径（本机 token 来源）
NODE_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "node_config.json")


def _read_local_node_info() -> dict:
    """读取本机 node_config.json 的连接信息；失败返回空 dict。"""
    try:
        import json
        with open(NODE_CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return {
            "token": cfg.get("token", ""),
            "port": cfg.get("tcp_port", 12345),
        }
    except Exception:
        return {}


def _copy_to_clipboard(text: str) -> None:
    """将文本写入系统剪贴板。"""
    try:
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(text)
    except Exception:
        pass


class LocalPanel(DetailPanel):
    """
    本机仪表盘面板（继承 DetailPanel 的分区渲染能力）。

    额外提供：
    - 连接信息区（IP/端口/Token/连接码），可一键复制
    - update_local(frame)：更新本机仪表盘
    """

    def __init__(self):
        super().__init__()
        # 缓存兜底 IP（在构造时获取一次，避免每次刷新都探测网卡）
        self._fallback_ip = get_lan_ip()
        # 在分区之上插入"连接信息"区（可复制）
        self._build_connect_info()

    def _build_connect_info(self) -> None:
        """在头部标签下插入连接信息面板（只读输入框 + 复制按钮）。"""
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 6)
        v.setSpacing(2)

        title = QLabel("本机连接信息（可直接复制告知他人接入本机）")
        title.setStyleSheet("color: #007acc; font-weight: bold; font-size: 12px;")
        v.addWidget(title)

        # 每行：名称 + 只读输入框 + 复制按钮
        self._info_edits = {}   # key → QLineEdit
        row_defs = [
            ("IP", "ip"),
            ("端口", "port"),
            ("Token", "token"),
            ("连接码", "code"),
        ]
        for label, key in row_defs:
            row = QHBoxLayout()
            name = QLabel(label)
            name.setFixedWidth(50)
            edit = QLineEdit()
            edit.setReadOnly(True)
            edit.setText("—")
            edit.setCursorPosition(0)   # 光标在开头，便于全选
            btn = QPushButton("复制")
            btn.setFixedWidth(48)
            btn.clicked.connect(lambda _=False, k=key: self._copy_field(k))
            row.addWidget(name)
            row.addWidget(edit, 1)
            row.addWidget(btn)
            v.addLayout(row)
            self._info_edits[key] = edit

        # 整串复制：IP:端口
        row2 = QHBoxLayout()
        self._copy_all_btn = QPushButton("复制 IP:端口")
        self._copy_all_btn.clicked.connect(self._copy_address)
        row2.addWidget(self._copy_all_btn)
        self._copy_uri_btn = QPushButton("复制连接串")
        self._copy_uri_btn.setToolTip("复制 pcmonitor:// 连接串，可在其他电脑\"剪贴板添加\"")
        self._copy_uri_btn.clicked.connect(self._copy_uri)
        row2.addWidget(self._copy_uri_btn)
        row2.addStretch(1)
        v.addLayout(row2)

        # 插入到 header_label 之后（_root 第 1 个元素是 header_label）
        self._root.insertWidget(1, box)

    def _copy_field(self, key: str) -> None:
        """复制指定字段。"""
        edit = self._info_edits.get(key)
        if edit:
            _copy_to_clipboard(edit.text())

    def _copy_address(self) -> None:
        """复制 IP:端口。"""
        ip = self._info_edits["ip"].text()
        port = self._info_edits["port"].text()
        if ip and port and ip != "—":
            _copy_to_clipboard(f"{ip}:{port}")

    def _copy_uri(self) -> None:
        """复制 pcmonitor:// 连接串（§23.3）。"""
        ip = self._info_edits["ip"].text()
        port = self._info_edits["port"].text()
        token = self._info_edits["token"].text()
        if ip and token and ip != "—":
            from common.connect_code import make_connect_uri
            _copy_to_clipboard(make_connect_uri(ip, int(port or 12345), token))

    def _update_connect_info(self) -> None:
        """刷新连接信息区的 IP/端口/Token/连接码。"""
        node_info = _read_local_node_info()
        token = node_info.get("token", "")
        port = node_info.get("port", 12345)

        ip = self._fallback_ip or "N/A"
        self._info_edits["ip"].setText(ip)
        self._info_edits["port"].setText(str(port))
        self._info_edits["token"].setText(token or "—")

        # 连接码：用本机 IP/端口/token 生成
        code = "—"
        if token and ip and ip != "N/A":
            try:
                from common.connect_code import make_connect_code
                code = make_connect_code(ip, port, token)
            except Exception:
                pass
        self._info_edits["code"].setText(code)

    def _update_header(self, frame: dict) -> None:
        """顶部：本机主机名 / IP / uptime / 本机模式。"""
        sys_info = frame.get("system", {})
        uptime = format_uptime(sys_info.get("uptime_seconds", 0))

        # IP 兜底（帧内值优先）
        ip = sys_info.get("local_ip") or self._fallback_ip or "N/A"
        self._fallback_ip = ip if ip != "N/A" else self._fallback_ip

        self.header_label.setText(
            f"本机: {frame.get('hostname', 'N/A')}  |  "
            f"IP: {ip}  |  "
            f"运行: {uptime}  |  本机模式")

        # 刷新连接信息区（IP 可能随帧更新）
        self._update_connect_info()
