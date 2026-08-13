# -*- coding: utf-8 -*-
"""
AlertService —— 告警编排服务（v5.2）。

职责（规格）：
    FrameStore.frame_updated
        ↓
    AlertService.evaluate()
        ↓
    AlertEngine.check()
        ↓
    AlertAdapter
        ↓
    AlertStore

- 订阅 FrameStore.frame_updated，收到新帧自动评估告警。
- 复用现有 AlertEngine（不修改）与 AlertAdapter / AlertStore。
- 不依赖 PyQt5（纯逻辑；信号由 store 层统一提供）。
"""
import logging

from host.store.frame_store import FrameStore
from host.store.alert_store import AlertStore
from host.facade.alert_adapter import AlertAdapter
from host.store.signals import Signal

log = logging.getLogger("host.service.alert")


class AlertService:
    """告警编排服务：连接 FrameStore / AlertEngine / AlertStore。"""

    def __init__(self, alert_engine, frame_store: FrameStore | None = None,
                 alert_store: AlertStore | None = None,
                 node_store=None, auto_subscribe: bool = True):
        """
        :param alert_engine:   AlertEngine 实例（提供 check(frame)）
        :param frame_store:    FrameStore（默认新建）
        :param alert_store:    AlertStore（默认新建）
        :param node_store:     NodeStore（可选，补 alias）
        :param auto_subscribe: 是否自动连接 frame_store.frame_updated
        """
        self.engine = alert_engine
        self.frame_store = frame_store or FrameStore()
        self.alert_store = alert_store or AlertStore()
        self.adapter = AlertAdapter(alert_engine, self.alert_store, node_store)
        self._subscribed = False
        if auto_subscribe:
            self.subscribe()

    # ---------- 订阅 ----------

    def subscribe(self) -> None:
        """连接 FrameStore.frame_updated → evaluate。"""
        if not self._subscribed:
            self.frame_store.frame_updated.connect(self._on_frame)
            self._subscribed = True

    def unsubscribe(self) -> None:
        """断开订阅。"""
        if self._subscribed:
            self.frame_store.frame_updated.disconnect(self._on_frame)
            self._subscribed = False

    # ---------- 处理 ----------

    def _on_frame(self, node_id: str, frame: dict) -> None:
        """FrameStore 新帧回调（主线程经 Qt 信号调用）。"""
        self.evaluate(node_id, frame)

    def evaluate(self, node_id: str, frame: dict, alias: str = "") -> list:
        """对一帧数据评估告警，返回新增告警列表。"""
        return self.adapter.evaluate(node_id, frame, alias)

    # ---------- 清理 ----------

    def clear_node(self, node_id: str) -> None:
        self.alert_store.clear_node(node_id)

    def reset(self) -> None:
        self.alert_store.reset_all()

    def shutdown(self) -> None:
        """断开订阅并清空。"""
        self.unsubscribe()
        self.alert_store.reset_all()
