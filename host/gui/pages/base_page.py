# -*- coding: utf-8 -*-
"""
PageBase —— 所有页面的抽象基类（v5.2 Phase 3-1）。

生命周期由 MainWindow 管理：
  __init__()  -> 构造（可延迟初始化）
  on_show()   -> 页面被切换到前台时调用
  on_hide()   -> 页面被切换到后台时调用
  cleanup()   -> 窗口关闭或页面被永久移除时调用

页面只能通过 Store/Facade/ViewModel 访问数据，禁止直接访问 MainWindow 内部属性。
"""
from PyQt5.QtWidgets import QWidget


class PageBase(QWidget):
    """所有 Host 页面的抽象基类。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stores = {}      # 注入的 Store 引用（由 MainWindow 设置）
        self._facade = None    # 注入的 SettingsFacade
        self._visible = False  # 当前是否可见

    # ---------- 生命周期 ----------

    def on_show(self) -> None:
        """页面被切换到前台时调用。子类可重写。"""
        self._visible = True

    def on_hide(self) -> None:
        """页面被切换到后台时调用。子类可重写。"""
        self._visible = False

    def cleanup(self) -> None:
        """窗口关闭或页面永久移除时调用。子类应释放资源。"""
        pass

    # ---------- 数据注入 ----------

    def set_stores(self, **stores) -> None:
        """注入 Store 引用（由 MainWindow 在创建页面时调用）。

        用法：page.set_stores(frame=frame_store, node=node_store, ...)
        """
        self._stores.update(stores)

    def set_facade(self, facade) -> None:
        """注入 SettingsFacade。"""
        self._facade = facade

    def get_store(self, name: str):
        """按名称获取 Store。"""
        return self._stores.get(name)

    # ---------- 辅助 ----------

    @property
    def is_visible(self) -> bool:
        return self._visible

    def refresh(self) -> None:
        """数据更新后由 MainWindow 调用，子类重写此方法刷新 UI。

        默认空实现——子类按需重写。
        """
        pass
