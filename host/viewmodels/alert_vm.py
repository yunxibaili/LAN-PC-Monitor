# -*- coding: utf-8 -*-
"""
AlertViewModel —— Alerts 页面数据转换层（v5.2 Phase 3-4A）。

职责：
  - 监听 AlertStore.alert_added / alert_cleared / count_changed 信号
  - 将 AlertStore 告警转换为 AlertItem（UI 可直接渲染的扁平结构）
  - 提供过滤（level / node / 搜索）与统计

数据流：
  AlertStore
      |  alert_added / alert_cleared / count_changed
      v
  AlertViewModel
      |  AlertItem
      v
  AlertsPage

重点：
  - **不复制 AlertStore 去重逻辑**（30s 去重已在 AlertStore 完成）
  - 本 VM 只做"展示层转换 + 过滤"，不碰告警产生/去重
"""
import logging

from host.store.signals import Signal

log = logging.getLogger("host.viewmodels.alert_vm")


class AlertItem:
    """告警展示项（扁平，UI 可直接渲染）。"""

    __slots__ = (
        "timestamp", "node_id", "node_alias",
        "name", "path", "value", "level", "threshold",
    )

    def __init__(self, alert: dict):
        self.timestamp = alert.get("timestamp", 0.0)
        self.node_id = alert.get("node_id", "")
        self.node_alias = alert.get("node_alias", "")
        self.name = alert.get("name", "")
        self.path = alert.get("path", "")
        self.value = alert.get("value")
        self.level = alert.get("level", "warn")
        self.threshold = alert.get("threshold")

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "node_id": self.node_id,
            "node_alias": self.node_alias,
            "name": self.name,
            "path": self.path,
            "value": self.value,
            "level": self.level,
            "threshold": self.threshold,
        }


class AlertViewModel:
    """告警视图模型：转换 + 过滤 + 统计，不复制 Store 去重。"""

    alerts_changed = Signal()      # 过滤结果变化（新增/清除/过滤变更）
    count_changed = Signal(int)    # 活动告警总数变化

    def __init__(self, alert_store):
        """
        :param alert_store: AlertStore 实例（已含 30s 去重）
        """
        self._store = alert_store
        # 内部缓存：AlertItem 列表（按时间倒序，新→旧）
        self._items = []
        self._filter_level = None    # None / "red" / "warn"
        self._filter_node = None     # None / node_id
        self._search_text = ""       # 搜索：匹配 name/alias/path
        self._subscribed = False
        self.subscribe()

    # ---------- 订阅 ----------

    def subscribe(self) -> None:
        """订阅 AlertStore 信号。"""
        if self._subscribed:
            return
        self._store.alert_added.connect(self._on_added)
        self._store.alert_cleared.connect(self._on_cleared)
        self._store.count_changed.connect(self._on_count)
        self._subscribed = True
        self._rebuild()

    def unsubscribe(self) -> None:
        """取消订阅。"""
        if self._subscribed:
            self._store.alert_added.disconnect(self._on_added)
            self._store.alert_cleared.disconnect(self._on_cleared)
            self._store.count_changed.disconnect(self._on_count)
            self._subscribed = False

    # ---------- 内部信号回调 ----------

    def _on_added(self, alert: dict) -> None:
        """AlertStore 新增告警（去重后）→ 插入缓存顶部。"""
        self._items.insert(0, AlertItem(alert))
        self.alerts_changed.emit()

    def _on_cleared(self, node_id: str) -> None:
        """AlertStore 清除某节点 → 移除该节点活动项。"""
        self._items = [i for i in self._items if i.node_id != node_id]
        self.alerts_changed.emit()

    def _on_count(self, count: int) -> None:
        """活动告警总数变化。"""
        self.count_changed.emit(count)

    # ---------- 查询 ----------

    def get_items(self) -> list:
        """按当前过滤条件返回 AlertItem 列表（新→旧）。"""
        return [i for i in self._items if self._match(i)]

    def get_count(self) -> int:
        """活动告警总数（未过滤，读 Store）。"""
        return self._store.active_count()

    def get_red_count(self) -> int:
        return self._store.red_count()

    def get_warn_count(self) -> int:
        return self._store.warn_count()

    def get_summary(self) -> dict:
        """统计摘要：red/warn/active/total。"""
        return self._store.summary()

    # ---------- 过滤 ----------

    def set_filter_level(self, level: str | None) -> None:
        """按等级过滤：None 全部 / "red" / "warn"。"""
        if self._filter_level != level:
            self._filter_level = level
            self.alerts_changed.emit()

    def set_filter_node(self, node_id: str | None) -> None:
        """按节点过滤：None 全部 / node_id。"""
        if self._filter_node != node_id:
            self._filter_node = node_id
            self.alerts_changed.emit()

    def set_search(self, text: str) -> None:
        """搜索过滤：匹配 name / node_alias / path（大小写不敏感）。"""
        t = (text or "").strip().lower()
        if self._search_text != t:
            self._search_text = t
            self.alerts_changed.emit()

    def clear_filters(self) -> None:
        """清除全部过滤。"""
        if self._filter_level or self._filter_node or self._search_text:
            self._filter_level = None
            self._filter_node = None
            self._search_text = ""
            self.alerts_changed.emit()

    # ---------- 清除 ----------

    def clear_node(self, node_id: str) -> None:
        """清除某节点告警（委托 Store，不复制逻辑）。"""
        self._store.clear_node(node_id)

    def clear_all(self) -> None:
        """清除全部活动告警（委托 Store）。"""
        self._store.clear_all()
        self._rebuild()
        self.alerts_changed.emit()

    # ---------- 内部 ----------

    def _match(self, item: AlertItem) -> bool:
        """是否匹配当前过滤条件。"""
        if self._filter_level and item.level != self._filter_level:
            return False
        if self._filter_node and item.node_id != self._filter_node:
            return False
        if self._search_text:
            haystack = f"{item.name} {item.node_alias} {item.path}".lower()
            if self._search_text not in haystack:
                return False
        return True

    def _rebuild(self) -> None:
        """从 Store 全量重建缓存（subscribe / clear_all 时）。"""
        self._items = [AlertItem(a) for a in self._store.alerts(limit=None)]
        # alerts() 已按新→旧排序（内部 reversed）
