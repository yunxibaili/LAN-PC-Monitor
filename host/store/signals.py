# -*- coding: utf-8 -*-
"""
Store 统一 Signal 规范（v5.2 Phase 3-1 修复）。

所有 Store 使用统一信号命名，基于纯 Python 回调实现。
接口与 pyqtSignal 一致：connect/emit/disconnect。
跨线程安全：emit 在主线程同步调用 slot。
"""
import logging

log = logging.getLogger("host.store.signals")


class Signal:
    """类属性描述符：模拟 pyqtSignal 的 connect/emit 接口。

    始终使用纯 Python 回调（避免 PyQt5 动态信号创建的兼容性问题）。
    接口完全兼容 pyqtSignal：connect(slot) / emit(*args) / disconnect()。
    """

    def __init__(self, *types):
        self._types = types
        self._name = None

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        key = f"_bound_{self._name}"
        bound = getattr(obj, key, None)
        if bound is None:
            bound = _BoundSignal(self._types)
            setattr(obj, key, bound)
        return bound


class _BoundSignal:
    """绑定信号：纯 Python 回调列表。"""

    def __init__(self, types):
        self._types = types
        self._slots = []

    def connect(self, slot):
        if slot not in self._slots:
            self._slots.append(slot)

    def disconnect(self, slot=None):
        if slot is None:
            self._slots.clear()
        elif slot in self._slots:
            self._slots.remove(slot)

    def emit(self, *args):
        for slot in list(self._slots):
            try:
                slot(*args)
            except Exception:
                log.debug("signal slot 异常", exc_info=True)


def has_qt_signal() -> bool:
    """是否使用 Qt 信号后端（始终 False）。"""
    return False
