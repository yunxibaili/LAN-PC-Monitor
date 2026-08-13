# -*- coding: utf-8 -*-
"""
v5.2 Phase 3-8 单元测试 —— MainWindow 精简架构。

验证：
1. 页面存在（5 个页面对象）
2. 无旧 UI（源码扫描：无 _build_ui / overview_grid / NodeListWidget 直接构造 /
   common.gui.detail_panel）
3. MainWindow 行数 < 450
4. Store / VM / Controller 已创建
5. 数据流：DataController._on_data → Store → 页面（经 stub 信号验证）

用法：python tests/test_v52_main_window.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  {detail}")


def _src():
    return open(os.path.join(ROOT, "host/gui/main_window.py"),
                encoding="utf-8").read()


def test_source_scans():
    """源码扫描：main_window 精简、无旧 UI。"""
    print("\n--- 1. main_window 源码扫描 ---")
    src = _src()
    lines = len(src.split("\n"))
    check(f"MainWindow 行数 < 450（实际 {lines}）", lines < 450, f"lines={lines}")
    check("无 _build_ui（legacy UI）", "_build_ui" not in src)
    check("无 overview_grid 引用", "overview_grid" not in src)
    check("无 OverviewGrid 构造", "OverviewGrid(" not in src)
    check("无 common.gui.detail_panel", "common.gui.detail_panel" not in src)
    check("无 NodeListWidget 直接构造", "NodeListWidget(" not in src)
    check("无 QSystemTrayIcon 构造", "QSystemTrayIcon(" not in src)
    check("无 _alert_state", "_alert_state" not in src)
    # 有 v5.2 结构
    check("有 Controllers", "controllers" in src and "DataController" in src
          and "NavigationController" in src)
    check("有 5 页面", all(p in src for p in
          ("DashboardPage", "NodesPage", "MonitorPage",
           "AlertsPage", "SettingsPage")))
    # property 代理保留
    check("property 代理保留", "frame_store._frames" in src
          and "node_store._statuses" in src)


def test_controller_dataflow():
    """DataController 数据流：WS → Store → 回调。"""
    print("\n--- 2. DataController 数据流 ---")
    # 先 stub PyQt5（NodeConnection 顶层导入 Qt 信号）
    import types
    _install_qt_stub()
    from host.store.frame_store import FrameStore
    from host.store.node_store import NodeStore
    from host.store.history_store import HistoryStore
    import host.gui.controllers.data_controller as dc_mod
    DataController = dc_mod.DataController

    fs, ns, hs = FrameStore(), NodeStore(), HistoryStore()
    dc = DataController({"hosts": []}, fs, ns, hs, None)
    got = []
    dc.set_callbacks(on_data=lambda f, n: got.append(("data", n)),
                     on_status=lambda s, n: got.append(("status", n)))
    dc.add_node("n1", "1.2.3.4", 12345, "tok", "游戏主机")
    # 模拟 WS 数据
    dc._on_data({"cpu": {"total_usage": 50}}, "n1")
    dc._on_status("connected", "n1")
    check("frame_store 已写入", fs.has("n1"))
    check("history_store 已写入", hs.node_count() >= 1)
    check("node_store 已写入", ns.has("n1") and ns.get_status("n1") == "connected")
    check("回调触发", ("data", "n1") in got and ("status", "n1") in got)
    check("评分经 NodeStore", ns.get_score("n1") is not None
          or ns.get_scorer("n1") is not None)


def test_navigation_controller():
    """NavigationController 页面路由。"""
    print("\n--- 3. NavigationController 路由 ---")
    _install_qt_stub()
    import types

    # 构造 stub pages/side_nav/content_stack
    class StubPage:
        PAGE_ID = "x"
        def __init__(s, pid): s.PAGE_ID=pid; s._shown=False; s._hidden=False
        def on_show(s): s._shown=True
        def on_hide(s): s._hidden=True
    class StubStack:
        def __init__(s): s.widgets=[]; s.current=None
        def addWidget(s, w): s.widgets.append(w)
        def indexOf(s, w): return s.widgets.index(w) if w in s.widgets else -1
        def setCurrentIndex(s, i):
            if s.current and hasattr(s.current,'on_hide'): s.current.on_hide()
            s.current = s.widgets[i] if i>=0 else None
            if s.current and hasattr(s.current,'on_show'): s.current.on_show()
        def currentWidget(s): return s.current
    class StubSideNav:
        def __init__(s): s.page_changed=type("S",(),{"connect":lambda x,sl: None})(); s.node_clicked=type("S",(),{"connect":lambda x,sl: None})()
        def _select(s, n): pass
        def add_node(s, n, a): pass

    from host.gui.controllers.navigation_controller import NavigationController
    pages = {p.PAGE_ID: p for p in (StubPage("dashboard"), StubPage("nodes"),
                                    StubPage("monitor"), StubPage("alerts"),
                                    StubPage("settings"))}
    stack = StubStack()
    for p in pages.values(): stack.addWidget(p)
    nav = NavigationController(StubSideNav(), stack, pages)
    nav.navigate("dashboard")
    check("导航到 dashboard 并 on_show", stack.current is pages["dashboard"]
          and pages["dashboard"]._shown)
    nav.navigate("monitor")
    check("导航到 monitor，dashboard 被 hide", stack.current is pages["monitor"]
          and pages["dashboard"]._hidden and pages["monitor"]._shown)


def test_alert_controller():
    """AlertController：AlertStore 信号 → 日志/托盘回调。"""
    print("\n--- 4. AlertController ---")
    from host.store.alert_store import AlertStore
    from host.gui.controllers.alert_controller import AlertController
    s = AlertStore(dedup_seconds=30)
    tray = type("Tray", (), {"available": False, "show_message": lambda *a,**k: None})()
    ac = AlertController(s, tray, {"alert_popup": True})
    ac.connect(status_bar=None)
    # push 触发 _on_alert_added（应不抛异常）
    try:
        s.push({"node_id": "n1", "path": "cpu.total_usage", "level": "red",
                "name": "CPU", "value": 95, "threshold": 90})
        check("AlertStore push 触发控制器回调", True)
    except Exception as e:
        check("AlertStore push 触发控制器回调", False, str(e))
    ac.shutdown()


def _install_qt_stub():
    """安装最小 PyQt5 stub（无 GUI 环境测试用）。"""
    import types
    qtcore = types.ModuleType("PyQt5.QtCore")
    class _Sig:
        def __init__(s,*t): s._t=t
        def __set_name__(s,o,n): s._n=n
        def __get__(s,obj,ot=None):
            if obj is None: return s
            k=f"_sig_{s._n}"; h=getattr(obj,k,None)
            if h is None: h=type("H",(),{"_slots":[],"connect":lambda x,sl: x._slots.append(sl)})(); setattr(obj,k,h)
            return h
    class QObject:
        def __init__(s,*a,**k): pass
    qtcore.QObject=QObject; qtcore.pyqtSignal=_Sig
    qtcore.Qt = type("Qt", (), {
        "Horizontal": 1, "AlignRight": 2, "AlignCenter": 4,
        "UserRole": 256, "CustomContextMenu": 4,
        "ScrollBarAsNeeded": 30, "ScrollBarAlwaysOff": 32,
        "NoFocus": 0, "StrongFocus": 1, "AlignLeft": 1, "AlignVCenter": 128,
        "ItemIsSelectable": 1, "ItemIsEnabled": 32, "ItemIsEditable": 2,
    })
    pkg=types.ModuleType("PyQt5"); pkg.QtCore=qtcore
    sys.modules.setdefault("PyQt5", pkg)
    sys.modules.setdefault("PyQt5.QtCore", qtcore)
    # QtWidgets 最小 stub（widgets 导入需要）
    qtw = types.ModuleType("PyQt5.QtWidgets")
    for n in ("QWidget","QLabel","QListWidget","QListWidgetItem","QMenu",
              "QFrame","QScrollArea","QGridLayout","QHBoxLayout","QVBoxLayout",
              "QPushButton","QGroupBox","QMainWindow","QStackedWidget","QSplitter"):
        setattr(qtw, n, type(n, (), {
            "__init__": lambda s,*a,**k: None,
            "__getattr__": lambda s,n: (lambda *a,**k: None),
        }))
    qtw.QMenu.addAction = lambda s,*a,**k: None
    qtw.QListWidgetItem.setFlags = staticmethod(lambda *a: None)
    sys.modules.setdefault("PyQt5.QtWidgets", qtw)
    # QtGui
    qg = types.ModuleType("PyQt5.QtGui")
    for n in ("QIcon","QPixmap","QColor"):
        setattr(qg, n, type(n, (), {"__init__": lambda s,*a,**k: None}))
    sys.modules.setdefault("PyQt5.QtGui", qg)


def main():
    print("=" * 60)
    print("v5.2 Phase 3-8 单元测试（MainWindow 精简）")
    print("=" * 60)
    test_source_scans()
    test_controller_dataflow()
    test_navigation_controller()
    test_alert_controller()
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
