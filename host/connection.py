# -*- coding: utf-8 -*-
"""
监控主机单节点连接器 —— NodeConnection（见《README.md》§6.2 / §4.7）。

v5.0：网络层为 WebSocket（ws://<ip>:port/ws?token=xxx）。
本模块为 **PyQt5 适配层**，将 ConnectionCore（纯 Python，见 connection_core.py）
的事件转为 Qt 信号，供 GUI 消费。核心逻辑在 connection_core.py，无 GUI 环境
可直接测试 connection_core。

接口兼容：类名 `NodeConnection`、信号
`data_received/status_changed/rtt_updated/loss_updated` 与 v4.0 一致，
GUI 无需改动装配。

稳定性优化（v5.0）：
- 状态机：connecting → authenticating → connected / failed。
- 错误 token 明确表现为 failed（鉴权失败），不表现为已连接。
"""
import logging

from PyQt5.QtCore import QObject, pyqtSignal

from host.connection_core import ConnectionCore

log = logging.getLogger("host.connection")


class NodeConnection(QObject):
    """
    单个 Agent 的连接对象（WebSocket）。

    信号：
        data_received(dict, str)  — (monitor_data 帧, node_id)
        status_changed(str, str)  — (状态文本, node_id)
        rtt_updated(float, str)   — (rtt_ms, node_id)
        loss_updated(float, str)  — (丢包率%, node_id)
    """

    data_received = pyqtSignal(dict, str)
    status_changed = pyqtSignal(str, str)
    rtt_updated = pyqtSignal(float, str)
    loss_updated = pyqtSignal(float, str)

    def __init__(self, node_id: str, ip: str, port: int, token: str, alias: str = ""):
        super().__init__()
        # 事件回调 → Qt 信号
        callbacks = {
            "on_state": self._on_state,
            "on_data": self._on_data,
            "on_rtt": self._on_rtt,
            "on_loss": self._on_loss,
        }
        self._core = ConnectionCore(node_id, ip, port, token, alias,
                                     callbacks=callbacks)

    # ---------- 属性 ----------

    @property
    def alias(self) -> str:
        return self._core.alias

    @property
    def node_id(self) -> str:
        return self._core.node_id

    # ---------- 生命周期（转发到 core） ----------

    def start(self) -> None:
        self._core.start()

    def stop(self) -> None:
        self._core.stop()

    def is_connected(self) -> bool:
        return self._core.is_connected()

    @property
    def state(self) -> str:
        return self._core.state

    def get_loss(self) -> float:
        return self._core.get_loss()

    def get_rtt(self) -> float:
        return self._core.get_rtt()

    # ---------- core 回调 → Qt 信号 ----------

    def _on_state(self, state: str, node_id: str) -> None:
        """状态回调 → status_changed 信号（跨线程安全）。"""
        try:
            self.status_changed.emit(state, node_id)
        except RuntimeError:
            pass

    def _on_data(self, frame: dict, node_id: str) -> None:
        try:
            self.data_received.emit(frame, node_id)
        except RuntimeError:
            pass

    def _on_rtt(self, rtt_ms: float, node_id: str) -> None:
        try:
            self.rtt_updated.emit(rtt_ms, node_id)
        except RuntimeError:
            pass

    def _on_loss(self, loss: float, node_id: str) -> None:
        try:
            self.loss_updated.emit(loss, node_id)
        except RuntimeError:
            pass
