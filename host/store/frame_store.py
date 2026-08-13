# -*- coding: utf-8 -*-
"""
FrameStore —— 最新帧缓存 分片状态（v5.2 Phase 0）。

职责：缓存每个节点最新 monitor_data 帧，替代 v5.1 MainWindow 的 `self.frames`。

- 纯逻辑实现，不修改 monitor_data 协议。
- 帧按 node_id 存储，最新覆盖旧帧。
- 提供按指标提取/健康度判定辅助（供 ViewModel/页面消费）。

信号（统一规范）：
    frame_updated(node_id, frame)   新帧到达
    node_removed(node_id)           节点移除时清理其缓存
    reset()                         整体清空
"""
from host.store.signals import Signal


class FrameStore:
    """最新帧缓存 Store。"""

    frame_updated = Signal(str, object)
    node_removed = Signal(str)
    reset = Signal()

    def __init__(self):
        self._frames = {}          # node_id -> dict（最新帧）
        self._last_seen = {}       # node_id -> ts（帧到达时间）

    # ---------- 写入 ----------

    def push(self, node_id: str, frame: dict, ts: float | None = None) -> None:
        """写入最新帧（覆盖旧帧）。空帧也接受（调用方决定是否跳过）。"""
        if not isinstance(frame, dict):
            return
        self._frames[node_id] = frame
        if ts is not None:
            self._last_seen[node_id] = ts
        self.frame_updated.emit(node_id, frame)

    def remove_node(self, node_id: str) -> None:
        """移除节点帧缓存（幂等）。"""
        if node_id in self._frames:
            del self._frames[node_id]
            self._last_seen.pop(node_id, None)
            self.node_removed.emit(node_id)

    def clear(self) -> None:
        self._frames.clear()
        self._last_seen.clear()
        self.reset.emit()

    # ---------- 查询 ----------

    def get(self, node_id: str) -> dict | None:
        """最新帧副本；不存在返回 None。"""
        frame = self._frames.get(node_id)
        return dict(frame) if frame else None

    def has(self, node_id: str) -> bool:
        return node_id in self._frames

    def count(self) -> int:
        return len(self._frames)

    def node_ids(self) -> list:
        return list(self._frames.keys())

    def get_metric(self, node_id: str, path: str, default=None):
        """按点号路径提取指标，如 'cpu.total_usage' / 'disk[0].usage_percent'。"""
        frame = self._frames.get(node_id)
        if frame is None:
            return default
        return _extract_path(frame, path, default)

    def last_seen(self, node_id: str) -> float | None:
        return self._last_seen.get(node_id)

    # ---------- 健康度 ----------

    def is_stale(self, node_id: str, timeout: float = 30.0,
                 now: float | None = None) -> bool:
        """是否超时无新帧（stale）。无帧或超过 timeout 视为 stale。"""
        import time as _t
        seen = self._last_seen.get(node_id)
        if seen is None:
            return True
        now = now if now is not None else _t.time()
        return (now - seen) > timeout


def _extract_path(frame: dict, path: str, default=None):
    """从帧中提取 'section.key' 或 'disk[0].key' 路径值。"""
    if "[" in path:
        head, rest = path.split("]", 1)
        section = head.split("[")[0]
        try:
            idx = int(head.split("[")[1])
        except ValueError:
            return default
        sub = rest.lstrip(".")
        try:
            return frame.get(section, [])[idx].get(sub, default)
        except (IndexError, KeyError, TypeError, AttributeError):
            return default
    section, _, key = path.partition(".")
    try:
        return frame.get(section, {}).get(key, default)
    except AttributeError:
        return default
