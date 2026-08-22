# -*- coding: utf-8 -*-
"""
test_v52_alerts_redesign.py —— AlertsPage v5.2 Phase 4-5 重构测试。

验证：
1. 新增 AlertWidget 组件（AlertSummaryCard / AlertCard / AlertToolbar / AlertDetail）
2. AlertsPage VM 注入 + Signal 刷新
3. 过滤 / 搜索 / 清除
4. Theme 扫描（无硬编码颜色）
5. 架构扫描（无 Store/Engine 导入）
"""
import os
import sys
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
from host.gui.widgets.alert_detail import AlertDetail
from host.gui.theme.colors import ThemeColors as TC

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


# ---------- 4. AlertDetail ----------

def test_detail():
    print("\n--- 4. AlertDetail ---")
    d = AlertDetail()
    check("initially hidden", not d.isVisible())
    item = AlertItem({"name": "Test", "node_id": "A", "level": "warn",
                      "value": 80, "threshold": 75, "path": "ram",
                      "timestamp": time.time()})
    d.set_alert(item)
    check("visible after set", d.isVisible())
    check("severity", d._fields["severity"].text() == "WARNING")
    d.clear()
    check("hidden after clear", not d.isVisible())


# ---------- 5. AlertsPage VM 注入 ----------

def test_vm_injection():
    print("\n--- 5. AlertsPage VM 注入 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    check("vm 已注入", page._vm is vm)
    check("has _card_active", hasattr(page, '_card_active'))
    check("has _card_total", hasattr(page, '_card_total'))
    check("has toolbar", hasattr(page, '_toolbar'))
    check("has detail", hasattr(page, '_detail'))


# ---------- 6. 空状态 ----------

def test_empty_state():
    print("\n--- 6. 空状态 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    page.show()
    check("空状态提示可见", page._empty_label.isVisible())
    check("统计=0", page._card_critical._val.text() == "0")


# ---------- 7. 有告警显示卡片 ----------

def test_with_alerts():
    print("\n--- 7. 有告警显示卡片 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    page.show()

    vm._items = [
        AlertItem({"timestamp": time.time(), "node_id": "A", "node_alias": "N1",
                   "name": "CPU high", "path": "cpu", "value": 95, "threshold": 90, "level": "red"}),
        AlertItem({"timestamp": time.time(), "node_id": "B", "node_alias": "N2",
                   "name": "MEM high", "path": "ram", "value": 85, "threshold": 80, "level": "warn"}),
    ]
    page._refresh_list()
    check("空状态隐藏", not page._empty_label.isVisible())
    check("卡片数=2", page._list_layout.count() - 1 == 2)  # -1 for stretch


# ---------- 8. level 过滤 ----------

def test_level_filter():
    print("\n--- 8. level 过滤 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    page.show()

    vm._items = [
        AlertItem({"timestamp": time.time(), "node_id": "A", "name": "r1", "level": "red"}),
        AlertItem({"timestamp": time.time(), "node_id": "A", "name": "r2", "level": "red"}),
        AlertItem({"timestamp": time.time(), "node_id": "B", "name": "w1", "level": "warn"}),
    ]
    page._refresh_list()
    check("全部: 3 cards", page._list_layout.count() - 1 == 3)

    page._toolbar._level_combo.setCurrentIndex(1)  # Critical
    page._on_filter_changed()
    page._refresh_list()
    check("仅红线: cards", page._list_layout.count() - 1 == 2)

    page._toolbar._level_combo.setCurrentIndex(0)  # All
    page._on_filter_changed()
    page._refresh_list()
    check("全部: 3 cards", page._list_layout.count() - 1 == 3)


# ---------- 9. 生命周期 ----------

def test_lifecycle():
    print("\n--- 9. 生命周期 ---")
    store = AlertStore()
    vm = AlertViewModel(store)
    page = AlertsPage()
    page.set_view_model(vm)
    page.on_show()
    check("on_show OK", True)
    page.on_hide()
    check("on_hide OK", True)
    page.cleanup()
    check("cleanup OK", True)


# ---------- 10. 架构扫描 ----------

def test_no_store_import():
    print("\n--- 10. 架构扫描 ---")
    p = os.path.join(ROOT, "host", "gui", "pages", "alerts_page.py")
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()
    check("无 import AlertStore", "import AlertStore" not in source)
    check("无 import AlertEngine", "import AlertEngine" not in source)
    check("无 import FrameStore", "import FrameStore" not in source)
    check("无 import QTimer", "import QTimer" not in source)
    check("有 set_view_model", "set_view_model" in source)

    for wname in ["alert_entry", "alert_detail"]:
        wp = os.path.join(ROOT, "host", "gui", "widgets", f"{wname}.py")
        with open(wp, "r", encoding="utf-8", errors="ignore") as f:
            wsource = f.read()
        check(f"{wname} 无 import AlertStore", "import AlertStore" not in wsource)
        check(f"{wname} 无 import AlertEngine", "import AlertEngine" not in wsource)


# ---------- 11. Theme 扫描 ----------

def test_no_hardcoded_colors():
    print("\n--- 11. Theme 扫描 ---")
    import re
    for wname in ["alert_entry", "alert_detail", "alerts_page"]:
        if wname == "alerts_page":
            wp = os.path.join(ROOT, "host", "gui", "pages", f"{wname}.py")
        else:
            wp = os.path.join(ROOT, "host", "gui", "widgets", f"{wname}.py")
        if not os.path.isfile(wp):
            continue
        with open(wp, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        violations = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("import") or stripped.startswith("from "):
                continue
            for m in re.finditer(r'#[0-9a-fA-F]{3,8}', stripped):
                violations.append(f"L{i}: {m.group(0)}")
        check(f"{wname} 无硬编码颜色", len(violations) == 0, str(violations[:3]))


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  AlertsPage v5.2 Phase 4-5 重构测试")
    print("=" * 55)

    test_detail()
    test_vm_injection()
    test_empty_state()
    test_with_alerts()
    test_level_filter()
    test_lifecycle()
    test_no_store_import()
    test_no_hardcoded_colors()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
