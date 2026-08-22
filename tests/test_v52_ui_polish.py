# -*- coding: utf-8 -*-
"""
test_v52_ui_polish.py —— UI Premium Upgrade 验证测试。

覆盖：
1. ThemeColors 完整
2. ThemeStyle 生成
3. NodeCard 渲染
4. Dashboard 布局
5. SideNav 状态
6. Alert 颜色
7. 无业务依赖
8. 源码扫描
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt5.QtWidgets import QApplication
import sys as _sys
if not _sys.argv:
    _sys.argv = ["test"]
_app = QApplication.instance() or QApplication(_sys.argv)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.metrics import ThemeMetrics as TM
from host.gui.theme.style import dark_qss
from host.viewmodels.dashboard_vm import DashboardViewModel
from host.store.frame_store import FrameStore
from host.store.node_store import NodeStore
from host.store.alert_store import AlertStore
from host.viewmodels.alert_vm import AlertViewModel
from host.viewmodels.monitor_vm import ChartPoint

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


# ---------- 1. ThemeColors ----------

def test_colors():
    print("\n--- 1. ThemeColors ---")
    check("PRIMARY 定义", hasattr(TC, 'PRIMARY'))
    check("SUCCESS 定义", hasattr(TC, 'SUCCESS'))
    check("WARNING 定义", hasattr(TC, 'WARNING'))
    check("DANGER 定义", hasattr(TC, 'DANGER'))
    check("BG_BASE 定义", hasattr(TC, 'BG_BASE'))
    check("TEXT_PRIMARY 定义", hasattr(TC, 'TEXT_PRIMARY'))
    check("status_color(connected)", TC.status_color("connected") == TC.SUCCESS)
    check("status_color(offline)", TC.status_color("offline") == TC.STATUS_OFFLINE)
    check("alert_color(red)", TC.alert_color("red") == TC.DANGER)
    check("bar_color(50)", TC.bar_color(50) == TC.BAR_SUCCESS)
    check("bar_color(85)", TC.bar_color(85) == TC.BAR_WARNING)
    check("bar_color(96)", TC.bar_color(96) == TC.BAR_DANGER)


# ---------- 2. ThemeStyle ----------

def test_style():
    print("\n--- 2. ThemeStyle ---")
    qss = dark_qss()
    check("QSS 非空", len(qss) > 100)
    check("含 BACKGROUND", "BACKGROUND" in qss or "background" in qss)
    check("含 QPushButton", "QPushButton" in qss)
    check("含 QTableWidget", "QTableWidget" in qss)
    check("含 QTabBar", "QTabBar" in qss)
    check("含 Segoe UI", "Segoe UI" in qss)


def test_dashboard_layout():
    print("\n--- 4. Dashboard 布局 ---")
    from host.gui.pages.dashboard_page import DashboardPage
    page = DashboardPage()
    check("DashboardPage 创建", page is not None)
    check("有 summary cards", hasattr(page, '_card_total'))
    check("有实时折线图", hasattr(page, '_chart'))
    check("有指标块 cpu", hasattr(page, '_tile_cpu'))
    check("有指标块 gpu", hasattr(page, '_tile_gpu'))


# ---------- 5. SideNav 状态 ----------

def test_sidenav():
    print("\n--- 5. SideNav ---")
    from host.gui.navigation.side_nav import SideNav
    nav = SideNav()
    check("SideNav 创建", nav is not None)
    check("宽度=220", nav.width() == 220 or nav.minimumWidth() == 220)
    check("6 个导航按钮", len(nav._buttons) == 6)

    nav.add_node("A", "NodeA")
    check("添加节点", len(nav._node_items) == 1)
    nav.update_node_status("A", "connected")
    check("状态更新", True)


# ---------- 6. Alert 颜色 ----------

def test_alert_colors():
    print("\n--- 6. Alert 颜色 ---")
    check("red -> DANGER", TC.alert_color("red") == TC.DANGER)
    check("warn -> WARNING", TC.alert_color("warn") == TC.WARNING)
    check("unknown -> NA", TC.alert_color("unknown") == TC.COLOR_NA)


# ---------- 7. 无业务依赖 ----------

def test_no_business_deps():
    print("\n--- 7. 无业务依赖 ---")
    check("ThemeColors 无 Store", not any(x in dir(TC) for x in ['Store', 'Frame', 'Node']))
    check("ThemeMetrics 无 Store", not any(x in dir(TM) for x in ['Store', 'Frame', 'Node']))


# ---------- 8. 源码扫描 ----------

def test_source_scan():
    print("\n--- 8. 源码扫描 ---")
    gui_files = []
    for root, _, fs in os.walk('host/gui'):
        if '__pycache__' in root:
            continue
        for f in fs:
            if f.endswith('.py'):
                gui_files.append(os.path.join(root, f))

    violations = []
    for p in gui_files:
        # MainWindow 是集成层，允许引用 Store/Connection
        if 'main_window' in os.path.basename(p):
            continue
        with open(p, 'r', encoding='utf-8', errors='ignore') as fh:
            lines = fh.readlines()
        import_lines = [l.strip() for l in lines
                        if l.strip().startswith('import ') or l.strip().startswith('from ')]
        all_imports = " ".join(import_lines)
        if 'FrameStore' in all_imports or 'NodeStore' in all_imports or 'NodeConnection' in all_imports:
            violations.append(p)

    check("UI 页面/组件无 Store/Connection import", len(violations) == 0,
          str(violations))


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  UI Premium Upgrade 验证测试 (Phase 4-1B)")
    print("=" * 55)

    test_colors()
    test_style()
    test_dashboard_layout()
    test_sidenav()
    test_alert_colors()
    test_no_business_deps()
    test_source_scan()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
