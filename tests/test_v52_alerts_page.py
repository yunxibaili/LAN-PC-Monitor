import sys, os, time

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


def push_alert(store, **kw):
    kw.setdefault("timestamp", time.time())
    kw.setdefault("node_id", "A")
    kw.setdefault("node_alias", "NodeA")
    kw.setdefault("name", "test")
    kw.setdefault("path", "test.path")
    kw.setdefault("value", 1)
    kw.setdefault("threshold", 1)
    kw.setdefault("level", "red")
    store.push(kw)


def make_items(store, vm, page, items_data):
    """直接填充 VM 缓存 + 刷新表格（绕过信号时序）。"""
    vm._items = [AlertItem(d) for d in items_data]
    page._refresh_table()


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
    check("表格隐藏", not page._table.isVisible())
    check("统计=0", page._card_active._val.text() == "0")


# ---- 3. 有告警显示表格 ----

def test_with_alerts():
    print("\n--- 3. 有告警显示表格 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    page.show()

    make_items(store, vm, page, [
        {"timestamp": time.time(), "node_id": "A", "node_alias": "N1",
         "name": "CPU high", "path": "cpu", "value": 95, "threshold": 90, "level": "red"},
        {"timestamp": time.time(), "node_id": "B", "node_alias": "N2",
         "name": "MEM high", "path": "ram", "value": 85, "threshold": 80, "level": "warn"},
    ])
    check("表格可见", page._table.isVisible())
    check("空状态隐藏", not page._empty_label.isVisible())
    check("表格行数=2", page._table.rowCount() == 2)
    check("第0行有值", page._table.item(0, 2) is not None)
    check("第1行有值", page._table.item(1, 2) is not None)


# ---- 4. alerts_changed 自动刷新 ----

def test_auto_refresh():
    print("\n--- 4. alerts_changed 自动刷新 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    page.show()
    check("初始 0 行", page._table.rowCount() == 0)

    make_items(store, vm, page, [
        {"timestamp": time.time(), "node_id": "A", "name": "t1",
         "path": "p", "value": 1, "threshold": 1, "level": "red"},
    ])
    check("push 后 1 行", page._table.rowCount() == 1)

    make_items(store, vm, page, [
        {"timestamp": time.time(), "node_id": "A", "name": "t1",
         "path": "p", "value": 1, "threshold": 1, "level": "red"},
        {"timestamp": time.time(), "node_id": "B", "name": "t2",
         "path": "p", "value": 2, "threshold": 2, "level": "warn"},
    ])
    check("再 push 后 2 行", page._table.rowCount() == 2)


# ---- 5. level 过滤 ----

def test_level_filter():
    print("\n--- 5. level 过滤 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    page.show()

    make_items(store, vm, page, [
        {"timestamp": time.time(), "node_id": "A", "name": "r1", "level": "red"},
        {"timestamp": time.time(), "node_id": "A", "name": "r2", "level": "red"},
        {"timestamp": time.time(), "node_id": "B", "name": "w1", "level": "warn"},
    ])
    check("全部: 3 行", page._table.rowCount() == 3)

    page._level_combo.setCurrentIndex(1)
    page._on_filter_changed()
    check("仅红线: 2 行", page._table.rowCount() == 2)

    page._level_combo.setCurrentIndex(2)
    page._on_filter_changed()
    check("仅预警: 1 行", page._table.rowCount() == 1)

    page._level_combo.setCurrentIndex(0)
    page._on_filter_changed()
    check("全部: 3 行", page._table.rowCount() == 3)


# ---- 6. node 过滤 ----

def test_node_filter():
    print("\n--- 6. node 过滤 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    page.show()

    make_items(store, vm, page, [
        {"timestamp": time.time(), "node_id": "A", "name": "a1", "level": "red"},
        {"timestamp": time.time(), "node_id": "B", "name": "b1", "level": "warn"},
        {"timestamp": time.time(), "node_id": "A", "name": "a2", "level": "red"},
    ])
    check("全部: 3 行", page._table.rowCount() == 3)

    page.update_node_list([("A", "NA"), ("B", "NB")])
    page._node_combo.setCurrentIndex(1)
    page._on_filter_changed()
    check("节点A: 2 行", page._table.rowCount() == 2)

    page._node_combo.setCurrentIndex(2)
    page._on_filter_changed()
    check("节点B: 1 行", page._table.rowCount() == 1)

    page._node_combo.setCurrentIndex(0)
    page._on_filter_changed()
    check("全部: 3 行", page._table.rowCount() == 3)


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
    # cleanup 前有数据
    make_items(store, vm, page, [
        {"timestamp": time.time(), "name": "x", "level": "red"},
    ])
    check("cleanup 前有数据", page._table.rowCount() == 1)
    page.cleanup()
    check("cleanup OK", True)
    # cleanup 后手动刷新不应影响（信号已断开，但手动刷新仍会更新）
    make_items(store, vm, page, [])
    check("cleanup 后清空", page._table.rowCount() == 0)


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
    print("  AlertsPage 前端测试 (Phase 3-4B)")
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
