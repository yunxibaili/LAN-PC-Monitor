# -*- coding: utf-8 -*-
"""
便捷连接对话框（见《技术文档.md》§2.5 / §23）。

提供三种便捷添加入口，供副机端/主机端复用：
- ConnectCodeDialog：连接码接入（§23.2）
- ClipboardDialog：从剪贴板连接串添加（§23.3）
- OnboardingDialog：首屏引导 + 一键接入全部（§23.5）

依赖 PyQt5。connect_code.py 提供底层解析逻辑（无 GUI）。
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem,
                             QPushButton, QVBoxLayout, QMessageBox)

from common import theme
from common.connect_code import (parse_connect_uri, resolve_connect_code,
                                 make_connect_code)
from common.theme import remove_help_button
from common.utils import make_host_id

log = logging.getLogger("common.connect_dialog")


class ConnectCodeDialog(QDialog):
    """
    连接码接入弹窗（§23.2）。

    用户在节点端看到纯数字连接码（6 位数字），在此输入；
    结合本地发现的候选节点（mDNS/UDP）做摘要匹配，自动解析接入。
    """

    def __init__(self, candidates: dict, on_add=None, parent=None):
        """
        :param candidates: 本地发现的候选节点 {ip: {"port","token",...}}
        :param on_add:     回调 fn(ip, port, token, alias)
        """
        super().__init__(parent)
        self.candidates = candidates
        self.on_add = on_add
        remove_help_button(self)   # 移除 Windows 标题栏问号按钮，防闪退
        self.setWindowTitle("连接码接入")
        self.resize(380, 160)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        hint = QLabel("请输入采集节点端显示的连接码（6 位数字，如 482913）：")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {theme.COLOR_NA};")
        root.addWidget(hint)

        row = QHBoxLayout()
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("6 位数字连接码")
        row.addWidget(self.code_edit, 1)
        root.addLayout(row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _on_accept(self) -> None:
        code = self.code_edit.text().strip()
        if not code:
            return
        match = resolve_connect_code(code, self.candidates)
        if not match:
            QMessageBox.warning(
                self, "未匹配到节点",
                "该连接码未匹配到本地发现的节点。\n"
                "请确认采集节点与本机在同一网段，且 mDNS/UDP 发现正常。")
            return
        if self.on_add:
            self.on_add(match["ip"], match["port"], match["token"],
                        match.get("hostname", ""))
        self.accept()


class ClipboardDialog(QDialog):
    """
    从剪贴板连接串添加（§23.3）。

    用户在节点端复制 pcmonitor:// 连接串，粘贴到此自动解析添加。
    """

    def __init__(self, on_add=None, parent=None):
        super().__init__(parent)
        self.on_add = on_add
        remove_help_button(self)   # 移除 Windows 标题栏问号按钮，防闪退
        self.setWindowTitle("从剪贴板添加")
        self.resize(400, 150)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        hint = QLabel("粘贴节点端复制的连接串（pcmonitor://...）：")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {theme.COLOR_NA};")
        root.addWidget(hint)

        self.uri_edit = QLineEdit()
        self.uri_edit.setPlaceholderText("pcmonitor://192.168.1.100:12345?token=...")
        root.addWidget(self.uri_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _on_accept(self) -> None:
        parsed = parse_connect_uri(self.uri_edit.text())
        if not parsed:
            QMessageBox.warning(
                self, "解析失败",
                "连接串格式不正确。\n应为 pcmonitor://<IP>:<端口>?token=<token>")
            return
        if self.on_add:
            self.on_add(parsed["ip"], parsed["port"], parsed["token"],
                        parsed["alias"])
        self.accept()


class OnboardingDialog(QDialog):
    """
    首屏引导（§23.5）。

    首次运行时弹出：扫描局域网节点 → 按 IP 段匹配度排序 → 一键接入全部。
    接入完成后写入 onboarded 标记，下次不再弹出。
    """

    def __init__(self, merged_hosts: dict, local_ip: str = "",
                 on_add_all=None, parent=None):
        """
        :param merged_hosts: 已发现节点 {ip: {"port","token","hostname",...}}
        :param local_ip:     本机 IP（用于 IP 段匹配度排序）
        :param on_add_all:   回调 fn(ip, port, token, alias) 批量接入
        """
        super().__init__(parent)
        self.merged_hosts = merged_hosts
        self.local_ip = local_ip
        self.on_add_all = on_add_all
        remove_help_button(self)   # 移除 Windows 标题栏问号按钮，防闪退
        self.setWindowTitle("欢迎使用 · 节点引导")
        self.resize(460, 380)
        self._build_ui()
        self._populate()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        title = QLabel("正在扫描局域网内的采集节点...")
        title.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {theme.COLOR_TEXT};")
        root.addWidget(title)

        self.list_widget = QListWidget()
        root.addWidget(self.list_widget, 1)

        row = QHBoxLayout()
        btn_all = QPushButton("一键接入全部")
        btn_all.clicked.connect(self._on_add_all)
        row.addWidget(btn_all)
        row.addStretch(1)
        btn_skip = QPushButton("跳过")
        btn_skip.clicked.connect(self.reject)
        row.addWidget(btn_skip)
        root.addLayout(row)

    def _sort_key(self, item):
        """按 IP 段匹配度降序（与本机同网段优先，§23.5）。"""
        ip = item.get("ip", "")
        same = ip.split(".")[0:3] == self.local_ip.split(".")[0:3]
        return (0 if same else 1, ip)

    def _populate(self) -> None:
        """填充发现的节点列表。"""
        self.list_widget.clear()
        if not self.merged_hosts:
            self.list_widget.addItem("（未发现局域网节点，可稍后手动添加或点\"跳过\"）")
            return
        items = sorted(self.merged_hosts.values(), key=self._sort_key)
        for info in items:
            hostname = info.get("hostname", "")
            ip = info.get("ip", "?")
            port = info.get("port") or info.get("tcp_port", 12345)
            text = f"{hostname}  ({ip}:{port})" if hostname else f"({ip}:{port})"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, {
                "ip": ip, "port": port,
                "token": info.get("token", ""),
                "alias": hostname or f"{ip}:{port}",
            })
            self.list_widget.addItem(item)

    def _on_add_all(self) -> None:
        """一键接入全部发现的节点。"""
        if not self.on_add_all:
            self.accept()
            return
        added = 0
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            info = item.data(Qt.UserRole)
            if info and info.get("ip"):
                self.on_add_all(info["ip"], info["port"], info["token"],
                                info["alias"])
                added += 1
        if added:
            log.info("首屏引导一键接入 %d 台节点", added)
        self.accept()
