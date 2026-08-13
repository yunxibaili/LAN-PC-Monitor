# -*- coding: utf-8 -*-
"""
test_v52_monitor_page.py —— MonitorPage 前端测试（v5.2 Phase 3-5D）。

覆盖：
1. VM 注入
2. 节点切换
3. 指标切换
4. 图表更新
5. 生命周期 on_show / on_hide
6. 源码扫描：无 HistoryStore/FrameStore/NodeStore/Connection
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

from host.store.history_store import HistoryStore
from host.store.node_store import NodeStore
from host.viewmodels.monitor_vm import MonitorViewModel
from host.gui.pages.monitor_page import MonitorPage

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


def _setup():
    hs = HistoryStore(maxlen=60)
    ns = NodeStore()
    vm = MonitorViewModel(hs, ns)
    page = MonitorPage()
    page.set_view_model(vm)
    return hs, ns, vm, page


def _populate(hs, ns):
    """填充测试数据。"""
    ns.add_node("A", alias="主机A")
    ns.add_node("B", alias="主机B")
    now = time.time()
    for i in range(10):
        hs.push("A", "cpu", 40.0 + i * 2, now + i)
        hs.push("A", "gpu", 60.0 + i, now + i)
        hs.push("A", "ram", 50.0, now + i)
        hs.push("B", "cpu", 20.0 + i, now + i)


# ---------- 1. VM 注入 ----------

def test_vm_injection():
    print("\n--- 1. VM 注入 ---")
    _, _, vm, page = _setup()
    check("vm 已注入", page._vm is vm)


# ---------- 2. 节点切换 ----------

def test_node_switch():
    print("\n--- 2. 节点切换 ---")
    hs, ns, vm, page = _setup()
    _populate(hs, ns)
    page.show()

    page.set_node("A")
    check("当前节点=A", page.get_node() == "A")
    check("标题含 A", "A" in page._title.text())

    page.set_node("B")
    check("当前节点=B", page.get_node() == "B")
    check("标题含 B", "B" in page._title.text())


# ---------- 3. 指标切换 ----------

def test_metric_switch():
    print("\n--- 3. 指标切换 ---")
    hs, ns, vm, page = _setup()
    _populate(hs, ns)
    page.show()
    page.set_node("A")

    # 默认 CPU
    check("默认 CPU", page._current_metric == "cpu")
    check("CPU 按钮选中", page._metric_buttons["cpu"].isChecked())

    # 切到 GPU
    page._on_metric_clicked("gpu")
    check("切到 GPU", page._current_metric == "gpu")
    check("GPU 按钮选中", page._metric_buttons["gpu"].isChecked())
    check("CPU 按钮取消", not page._metric_buttons["cpu"].isChecked())


# ---------- 4. 图表更新 ----------

def test_chart_update():
    print("\n--- 4. 图表更新 ---")
    hs, ns, vm, page = _setup()
    _populate(hs, ns)
    page.show()
    page.set_node("A")

    # 手动刷新
    page._refresh_chart()
    check("图表有信息", page._info_label.text() != "选择节点和指标查看趋势")
    check("信息含 A", "A" in page._info_label.text() or "主机A" in page._info_label.text())


# ---------- 5. 生命周期 ----------

def test_lifecycle():
    print("\n--- 5. 生命周期 ---")
    hs, ns, vm, page = _setup()
    _populate(hs, ns)

    page.on_show()
    check("on_show OK", True)

    page.on_hide()
    check("on_hide OK", True)

    page.set_node("A")
    check("set_node 不崩溃", True)


# ---------- 6. 源码扫描 ----------

def test_no_store_import():
    print("\n--- 6. 源码扫描 ---")
    p = os.path.join(ROOT, "host", "gui", "pages", "monitor_page.py")
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    import_lines = [l.strip() for l in lines
                    if l.strip().startswith("import ") or l.strip().startswith("from ")]
    all_imports = " ".join(import_lines)
    check("无 HistoryStore import", "HistoryStore" not in all_imports)
    check("无 FrameStore import", "FrameStore" not in all_imports)
    check("无 NodeStore import", "NodeStore" not in all_imports)
    check("无 Connection import", "NodeConnection" not in all_imports
          or "connection" not in all_imports.lower())
    check("有 MonitorViewModel", "MonitorViewModel" in all_imports
          or "monitor_vm" in all_imports)
    check("有 ChartWidget/ChartPanel", "ChartWidget" in all_imports
          or "chart_widget" in all_imports or "ChartPanel" in all_imports
          or "chart_panel" in all_imports)


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  MonitorPage 前端测试 (Phase 3-5D)")
    print("=" * 55)

    test_vm_injection()
    test_node_switch()
    test_metric_switch()
    test_chart_update()
    test_lifecycle()
    test_no_store_import()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
