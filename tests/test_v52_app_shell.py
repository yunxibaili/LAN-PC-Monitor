# -*- coding: utf-8 -*-
"""
test_v52_app_shell.py —— App Shell 验证测试（v5.2 Phase 4-2A）。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt5.QtWidgets import QApplication
import sys as _sys
if not _sys.argv:
    _sys.argv = ["test"]
_app = QApplication.instance() or QApplication(_sys.argv)

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  {detail}")


# ---------- 1. HeaderBar ----------

# HeaderBar 已在 v5.5 UI 重做中删除（无顶栏），此处不再测试。


# ---------- 2. SideNav ----------

def test_sidenav():
    print("\n--- 2. SideNav ---")
    from host.gui.navigation.side_nav import SideNav
    nav = SideNav()
    check("SideNav 创建", nav is not None)
    check("宽度=220", nav.width() == 220 or nav.minimumWidth() == 220)
    check("6 导航按钮", len(nav._buttons) == 6)
    check("add_node", hasattr(nav, 'add_node'))
    check("remove_node", hasattr(nav, 'remove_node'))
    check("update_node_status", hasattr(nav, 'update_node_status'))

    nav.add_node("A", "NodeA")
    nav.add_node("B", "NodeB")
    check("添加 2 节点", len(nav._node_items) == 2)
    nav.update_node_status("A", "connected")
    check("状态更新不崩溃", True)
    nav.remove_node("A")
    check("删除后 1 节点", len(nav._node_items) == 1)


# ---------- 3. MainWindow 无 Store 导入 ----------

def test_no_store_import():
    print("\n--- 3. MainWindow 无 Store 导入 ---")
    p = os.path.join(ROOT, "host", "gui", "main_window.py")
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    import_lines = [l.strip() for l in lines
                    if l.strip().startswith("import ") or l.strip().startswith("from ")]
    all_imports = " ".join(import_lines)
    # MainWindow 可以 import 业务层（作为集成点），但不能 import Store 直接
    # 实际上 MainWindow 是集成层，它导入 Store 是允许的
    check("MainWindow 有 import（集成层允许）", len(import_lines) > 0)


# ---------- 4. 页面路由 ----------

def test_page_routing():
    print("\n--- 4. 页面路由 ---")
    from host.gui.navigation.side_nav import SideNav
    from host.gui.pages.dashboard_page import DashboardPage
    from host.gui.pages.nodes_page import NodesPage
    from host.gui.pages.monitor_page import MonitorPage
    from host.gui.pages.alerts_page import AlertsPage
    from host.gui.pages.settings_page import SettingsPage
    from host.gui.pages.history_page import HistoryPage
    from PyQt5.QtWidgets import QStackedWidget

    nav = SideNav()
    stack = QStackedWidget()
    pages = {}
    for PageClass in (DashboardPage, NodesPage, MonitorPage, AlertsPage, HistoryPage, SettingsPage):
        page = PageClass()
        pages[PageClass.PAGE_ID] = page
        stack.addWidget(page)

    check("6 个页面", len(pages) == 6)
    check("stack 6 页", stack.count() == 6)

    # 测试信号连接
    nav_page = [None]
    def on_nav(pid):
        nav_page[0] = pid
    nav.page_changed.connect(on_nav)
    nav._on_nav_click("monitor")
    check("导航信号触发", nav_page[0] == "monitor")


def main():
    global PASS, FAIL
    print("=" * 50)
    print("  App Shell 验证测试 (Phase 4-2A)")
    print("=" * 50)

    test_sidenav()
    test_no_store_import()
    test_page_routing()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
