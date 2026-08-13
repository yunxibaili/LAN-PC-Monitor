# -*- coding: utf-8 -*-
"""
AlertAdapter —— 告警桥接层（v5.2 Phase 0）。

职责：将 AlertEngine.check(frame) 的输出接入 AlertStore，并补充 node 上下文
（node_id/node_alias）。UI（状态栏/托盘/AlertsPage/SideNav 徽标）只消费
AlertStore 的信号，不直接调 AlertEngine。

- 本模块不修改 AlertEngine（保留其纯规则检测）。
- 30s 去重由 AlertStore 内部实现（评审 §8.4）。
- 不依赖 PyQt5（AlertEngine 是纯逻辑）。
"""
import logging

from host.store.alert_store import AlertStore
from host.store.node_store import NodeStore

log = logging.getLogger("host.facade.alert")


class AlertAdapter:
    """将 AlertEngine 输出桥接到 AlertStore。"""

    def __init__(self, alert_engine, alert_store: AlertStore | None = None,
                 node_store: NodeStore | None = None):
        """
        :param alert_engine: AlertEngine 实例（提供 check(frame)）
        :param alert_store:  AlertStore 实例（默认新建）
        :param node_store:   NodeStore 实例（用于补 node_id/alias，可空）
        """
        self.engine = alert_engine
        self.alert_store = alert_store or AlertStore()
        self.node_store = node_store

    def evaluate(self, node_id: str, frame: dict, alias: str = "") -> list:
        """
        对一帧数据跑告警检测，命中则推入 AlertStore。
        返回本次实际新增的告警列表（去重后）。
        """
        try:
            hits = self.engine.check(frame)
        except Exception as e:
            log.debug("告警检测异常: %s", e)
            return []
        if not hits:
            # 无告警 → 尝试清空该节点活动告警（若本帧各项恢复正常）
            self.alert_store.clear_node(node_id)
            return []

        added = []
        for h in hits:
            alert = {
                "timestamp": _now(),
                "node_id": node_id,
                "node_alias": alias or self._alias(node_id),
                "path": h.get("path", ""),
                "name": h.get("name", ""),
                "value": h.get("value"),
                "threshold": h.get("threshold"),
                "level": h.get("level", "warn"),
            }
            if self.alert_store.push(alert):
                added.append(alert)
        return added

    def _alias(self, node_id: str) -> str:
        if self.node_store is not None:
            return self.node_store.get_alias(node_id)
        return node_id

    def clear_node(self, node_id: str) -> None:
        self.alert_store.clear_node(node_id)

    def reset(self) -> None:
        self.alert_store.reset()


def _now() -> float:
    import time
    return time.time()
