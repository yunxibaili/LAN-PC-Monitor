# -*- coding: utf-8 -*-
"""
AlertStore —— 告警队列 + 30s 去重 + 计数 分片状态（v5.2 Phase 0）。

职责：集中管理告警，替代 v5.1 MainWindow 的 `_alert_state`（状态变化去重）与
散落的告警展示逻辑。v5.2 采用 **30s 时间窗口去重**（评审 §8.4）。

- 告警来源：AlertEngine.check(frame) 输出（经 AlertService 桥接，本 Store 不依赖 AlertEngine）。
- 数据结构：{timestamp, node_id, node_alias, path, name, value, threshold, level}。
- 内存只保留最近 N 条（防无限增长）；v6 由 event/ 持久化接管。

信号（统一规范）：
    alert_added(alert)              新告警
    alert_cleared(node_id)          某节点告警清空
    count_changed(count)            未恢复告警数变化
    reset()                         整体清空
"""
import time

from host.store.signals import Signal


class AlertStore:
    """告警 Store（30s 窗口去重 + 计数）。"""

    alert_added = Signal(dict)
    alert_cleared = Signal(str)
    count_changed = Signal(int)
    reset = Signal()

    def __init__(self, dedup_seconds: int = 30, max_entries: int = 500):
        self._dedup_seconds = max(1, int(dedup_seconds))
        self._max_entries = max(10, int(max_entries))
        self._alerts = []                 # 完整告警列表（新→旧或旧→新，见 _append）
        self._last_alert_ts = {}          # (node_id, path) -> ts（去重）
        self._active = {}                 # (node_id, path) -> alert（未恢复）

    # ---------- 写入 ----------

    def push(self, alert: dict) -> bool:
        """
        推入一条告警；30s 窗口内同一 (node_id, path) 已存在则跳过（去重）。
        返回是否真正新增。
        """
        node_id = alert.get("node_id")
        path = alert.get("path")
        if not node_id or not path:
            return False
        now = time.time()
        key = (node_id, path)
        last = self._last_alert_ts.get(key)
        if last is not None and (now - last) < self._dedup_seconds:
            return False

        self._last_alert_ts[key] = now
        self._alerts.append(alert)
        # 截断：只保留最近 max_entries 条
        if len(self._alerts) > self._max_entries:
            self._alerts = self._alerts[-self._max_entries:]
        self._active[key] = alert
        self.alert_added.emit(alert)
        self.count_changed.emit(self.active_count())
        return True

    def clear_node(self, node_id: str) -> None:
        """清空某节点的活动告警（节点恢复/离线时调用）。"""
        changed = False
        for key in list(self._active.keys()):
            if key[0] == node_id:
                del self._active[key]
                changed = True
        # 保留去重时间戳（避免瞬时抖动重复告警）；清活动态即可
        if changed:
            self.alert_cleared.emit(node_id)
            self.count_changed.emit(self.active_count())

    def remove(self, node_id: str) -> None:
        """规格要求：移除某节点的全部告警（等价 clear_node）。"""
        self.clear_node(node_id)

    def clear_all(self) -> None:
        """清空全部活动告警（保留历史列表）。"""
        self._active.clear()
        self.count_changed.emit(0)

    def reset_all(self) -> None:
        """整体重置（清空历史、去重表、活动告警）。"""
        self._alerts.clear()
        self._last_alert_ts.clear()
        self._active.clear()
        self.reset.emit()
        self.count_changed.emit(0)

    # ---------- 查询 ----------

    def alerts(self, limit: int | None = None) -> list:
        """告警历史（最新在前）。"""
        seq = list(reversed(self._alerts))
        if limit is not None and limit > 0:
            seq = seq[:limit]
        return seq

    def active(self) -> list:
        """未恢复告警（最新在前）。"""
        return list(reversed(list(self._active.values())))

    def active_count(self) -> int:
        return len(self._active)

    def red_count(self) -> int:
        return sum(1 for a in self._active.values()
                   if a.get("level") == "red")

    def warn_count(self) -> int:
        return sum(1 for a in self._active.values()
                   if a.get("level") == "warn")

    def node_alerts(self, node_id: str) -> list:
        """某节点的未恢复告警。"""
        return [a for k, a in self._active.items() if k[0] == node_id]

    # ---------- 统计 ----------

    def summary(self) -> dict:
        return {
            "red": self.red_count(),
            "warn": self.warn_count(),
            "active": self.active_count(),
            "total": len(self._alerts),
        }
