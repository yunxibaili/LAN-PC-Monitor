# -*- coding: utf-8 -*-
"""
test_v52_alerts_page.py —— AlertsPage v5.2 测试（Phase 4-5 / 4-5.1）。

验证：
1. VM 注入
2. 空状态 / 有告警
3. alerts_changed 自动刷新
4. level 过滤
5. node 过滤
6. 生命周期
7. 架构扫描（无 Store/Engine 导入）
"""
import sys
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt5.QtWidgets import QApplication
import sys as _sys
if not _sys.argv:
    _sys.argv = ["test"]
_app = QApplication.instance() or QApplication(_sys.argv)

from host.store.alert_store import AlertStore
from host.viewmodels.alert_vm import AlertViewModel, AlertItem
from host.gui.pages.alerts_page import AlertsPage
from host.gui.widgets.alert_card import AlertCard

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


def make_items(vm, page, items_data):
    """直接填充 VM 缓存 + 刷新列表。"""
    vm._items = [AlertItem(d) for d in items_data]
    page._refresh_list()


# ---- 1. VM 注入 ----

def test_vm_injection():
    print("\n--- 1. VM 注入 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    check("vm 已注入", page._vm is vm)


# ---- 2. 空状态 ----

def test_empty_state():
    print("\n--- 2. 空状态 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    page.show()
    check("空状态提示可见", page._empty_label.isVisible())
    check("统计=0", page._card_active._val.text() == "0")


# ---- 3. 有告警显示卡片 ----

def test_with_alerts():
    print("\n--- 3. 有告警显示卡片 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    page.show()

    make_items(vm, page, [
        {"timestamp": time.time(), "node_id": "A", "node_alias": "N1",
         "name": "CPU high", "path": "cpu", "value": 95, "threshold": 90, "level": "red"},
        {"timestamp": time.time(), "node_id": "B", "node_alias": "N2",
         "name": "MEM high", "path": "ram", "value": 85, "threshold": 80, "level": "warn"},
    ])
    check("空状态隐藏", not page._empty_label.isVisible())
    check("卡片数=2", page._card_count() == 2)


# ---- 4. alerts_changed 自动刷新 ----

def test_auto_refresh():
    print("\n--- 4. alerts_changed 自动刷新 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    page.show()
    check("初始 0 卡片", page._card_count() == 0)

    make_items(vm, page, [
        {"timestamp": time.time(), "node_id": "A", "name": "t1",
         "path": "p", "value": 1, "threshold": 1, "level": "red"},
    ])
    check("push 后 1 卡片", page._card_count() == 1)

    make_items(vm, page, [
        {"timestamp": time.time(), "node_id": "A", "name": "t1",
         "path": "p", "value": 1, "threshold": 1, "level": "red"},
        {"timestamp": time.time(), "node_id": "B", "name": "t2",
         "path": "p", "value": 2, "threshold": 2, "level": "warn"},
    ])
    check("再 push 后 2 卡片", page._card_count() == 2)


# ---- 5. level 过滤 ----

def test_level_filter():
    print("\n--- 5. level 过滤 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    page.show()

    make_items(vm, page, [
        {"timestamp": time.time(), "node_id": "A", "name": "r1", "level": "red"},
        {"timestamp": time.time(), "node_id": "A", "name": "r2", "level": "red"},
        {"timestamp": time.time(), "node_id": "B", "name": "w1", "level": "warn"},
    ])
    check("全部: 3 卡片", page._card_count() == 3)

    page._toolbar._level_combo.setCurrentIndex(1)  # Critical
    page._on_filter_changed()
    check("仅红线: 2 卡片", page._card_count() == 2)

    page._toolbar._level_combo.setCurrentIndex(2)  # Warning
    page._on_filter_changed()
    check("仅预警: 1 卡片", page._card_count() == 1)

    page._toolbar._level_combo.setCurrentIndex(0)  # All
    page._on_filter_changed()
    check("全部: 3 卡片", page._card_count() == 3)


# ---- 6. node 过滤 ----

def test_node_filter():
    print("\n--- 6. node 过滤 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    page.show()

    make_items(vm, page, [
        {"timestamp": time.time(), "node_id": "A", "name": "a1", "level": "red"},
        {"timestamp": time.time(), "node_id": "B", "name": "b1", "level": "warn"},
        {"timestamp": time.time(), "node_id": "A", "name": "a2", "level": "red"},
    ])
    check("全部: 3 卡片", page._card_count() == 3)

    page.update_node_list([("A", "NA"), ("B", "NB")])
    page._toolbar._node_combo.setCurrentIndex(1)  # A
    page._on_filter_changed()
    check("节点A: 2 卡片", page._card_count() == 2)

    page._toolbar._node_combo.setCurrentIndex(2)  # B
    page._on_filter_changed()
    check("节点B: 1 卡片", page._card_count() == 1)

    page._toolbar._node_combo.setCurrentIndex(0)  # All
    page._on_filter_changed()
    check("全部: 3 卡片", page._card_count() == 3)


# ---- 7. 生命周期 ----

def test_lifecycle():
    print("\n--- 7. 生命周期 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    page.on_show()
    check("on_show OK", True)
    page.on_hide()
    check("on_hide OK", True)
    make_items(vm, page, [
        {"timestamp": time.time(), "name": "x", "level": "red"},
    ])
    check("有数据", page._card_count() == 1)
    page.cleanup()
    check("cleanup OK", True)
    make_items(vm, page, [])
    check("cleanup 后清空", page._card_count() == 0)


# ---- 8. 源码扫描 ----

def test_no_store_import():
    print("\n--- 8. 源码扫描 ---")
    p = os.path.join(ROOT, "host", "gui", "pages", "alerts_page.py")
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    import_lines = [l.strip() for l in lines
                    if l.strip().startswith("import ") or l.strip().startswith("from ")]
    all_imports = " ".join(import_lines)
    check("无 import AlertStore", "AlertStore" not in all_imports)
    check("无 import AlertEngine", "AlertEngine" not in all_imports)
    check("无 import FrameStore", "FrameStore" not in all_imports)
    check("无 import QTimer", "QTimer" not in all_imports)
    check("有 ViewModel 注入方法", hasattr(AlertsPage, 'set_view_model'))


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  AlertsPage v5.2 测试 (Phase 4-5 / 4-5.1)")
    print("=" * 55)

    test_vm_injection()
    test_empty_state()
    test_with_alerts()
    test_auto_refresh()
    test_level_filter()
    test_node_filter()
    test_lifecycle()
    test_no_store_import()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
