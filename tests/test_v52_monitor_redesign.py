# -*- coding: utf-8 -*-
"""
test_v52_monitor_redesign.py —— MonitorPage Redesign 验证测试（v5.2 Phase 4-4）。
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
from host.gui.widgets.monitor_header import MonitorHeader
from host.gui.widgets.metric_selector import MetricSelector
from host.gui.widgets.chart_panel import ChartPanel, SummaryCard

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
    ns.add_node("A", alias="主机A")
    ns.add_node("B", alias="主机B")
    now = time.time()
    for i in range(10):
        hs.push("A", "cpu", 40.0 + i * 2, now + i)
        hs.push("A", "gpu", 60.0 + i, now + i)
        hs.push("A", "ram", 50.0, now + i)
        hs.push("A", "net_up", 12.0 + i, now + i)
        hs.push("A", "net_down", 45.0 + i * 2, now + i)
        hs.push("B", "cpu", 20.0 + i, now + i)


# ---------- 1. MonitorHeader ----------

def test_monitor_header():
    print("\n--- 1. MonitorHeader ---")
    h = MonitorHeader()
    h.set_node("A", alias="主机A", status="connected")
    check("node label", h._node_lbl.text() == "主机A")
    check("status badge", h._status_badge.text() == "ONLINE")
    h.set_stats({"POINTS": "100", "METRIC": "CPU"})
    check("stats keys", len(h._stats_widgets) == 2)
    h.clear()
    check("clear", h._node_lbl.text() == "未选择节点")


# ---------- 2. MetricSelector ----------

def test_metric_selector():
    print("\n--- 2. MetricSelector ---")
    s = MetricSelector()
    check("default cpu", s.get_current() == "cpu")
    check("5 tabs", len(s._tabs) == 5)
    s.set_current("gpu")
    check("set gpu", s.get_current() == "gpu")
    # signal from click
    signals = []
    s.metric_changed.connect(lambda m: signals.append(m))
    s._on_tab_clicked("ram")
    check("signal emitted", len(signals) == 1 and signals[0] == "ram")


# ---------- 3. ChartPanel ----------

def test_chart_panel():
    print("\n--- 3. ChartPanel ---")
    p = ChartPanel()
    check("chart exists", p._chart is not None)
    p.update_summary(current=45.2, average=42.1, peak=68.0,
                     status_text="NORMAL", status_color="#22C55E", unit="%")
    check("current card", p._current_card._value_lbl.text() == "45.2%")
    check("avg card", p._avg_card._value_lbl.text() == "42.1%")
    check("peak card", p._peak_card._value_lbl.text() == "68.0%")
    check("status card", p._status_card._value_lbl.text() == "NORMAL")
    p.clear_summary()
    check("clear", p._current_card._value_lbl.text() == "—")


# ---------- 4. MonitorPage 结构 ----------

def test_page_structure():
    print("\n--- 4. MonitorPage 结构 ---")
    hs, ns, vm, page = _setup()
    check("has _header", hasattr(page, '_header'))
    check("has _selector", hasattr(page, '_selector'))
    check("has _chart_panel", hasattr(page, '_chart_panel'))
    check("has _chart", hasattr(page, '_chart'))
    check("vm injected", page._vm is vm)


# ---------- 5. 节点切换 ----------

def test_node_switch():
    print("\n--- 5. 节点切换 ---")
    hs, ns, vm, page = _setup()
    _populate(hs, ns)
    page.show()
    page.set_node("A")
    check("current_node=A", page.get_node() == "A")
    check("header shows A", "主机A" in page._header._node_lbl.text())
    page.set_node("B")
    check("current_node=B", page.get_node() == "B")


# ---------- 6. 指标切换 ----------

def test_metric_switch():
    print("\n--- 6. 指标切换 ---")
    hs, ns, vm, page = _setup()
    _populate(hs, ns)
    page.show()
    page.set_node("A")
    check("默认 CPU", page._current_metric == "cpu")
    page._on_metric_clicked("gpu")
    check("切到 GPU", page._current_metric == "gpu")
    page._on_metric_clicked("ram")
    check("切到 RAM", page._current_metric == "ram")


# ---------- 7. 图表更新 + 汇总卡片 ----------

def test_chart_update():
    print("\n--- 7. 图表更新 + 汇总卡片 ---")
    hs, ns, vm, page = _setup()
    _populate(hs, ns)
    page.show()
    page.set_node("A")
    page._refresh_chart()
    # 汇总卡片应有值
    current = page._chart_panel._current_card._value_lbl.text()
    check("current 有值", current != "—" and "%" in current)
    avg = page._chart_panel._avg_card._value_lbl.text()
    check("avg 有值", avg != "—" and "%" in avg)


# ---------- 8. 生命周期 ----------

def test_lifecycle():
    print("\n--- 8. 生命周期 ---")
    hs, ns, vm, page = _setup()
    _populate(hs, ns)
    page.on_show()
    check("on_show OK", True)
    page.on_hide()
    check("on_hide OK", True)
    page.set_node("A")
    check("set_node 不崩溃", True)


# ---------- 9. 向后兼容属性 ----------

def test_backward_compat():
    print("\n--- 9. 向后兼容属性 ---")
    hs, ns, vm, page = _setup()
    _populate(hs, ns)
    page.show()
    check("_metric_buttons dict", isinstance(page._metric_buttons, dict))
    check("_metric_buttons has cpu", "cpu" in page._metric_buttons)
    check("_title label", page._title is not None)
    check("_info_label label", page._info_label is not None)
    check("_chart widget", page._chart is not None)


# ---------- 10. 源码扫描 ----------

def test_no_store_import():
    print("\n--- 10. 源码扫描 ---")
    for fname in ['monitor_page.py', 'monitor_header.py', 'metric_selector.py', 'chart_panel.py']:
        p = os.path.join(ROOT, "host", "gui", "widgets" if fname != "monitor_page.py" else "pages", fname)
        if not os.path.isfile(p):
            p = os.path.join(ROOT, "host", "gui", "pages", fname)
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            import_lines = [l.strip() for l in lines
                            if l.strip().startswith("import ") or l.strip().startswith("from ")]
            all_imports = " ".join(import_lines)
            check(f"{fname} 无 HistoryStore", "HistoryStore" not in all_imports)
            check(f"{fname} 无 FrameStore", "FrameStore" not in all_imports)
            check(f"{fname} 无 NodeStore", "NodeStore" not in all_imports)


# ---------- 11. Theme 引用 ----------

def test_theme_refs():
    print("\n--- 11. Theme 引用 ---")
    import re
    for fname in ['monitor_header.py', 'metric_selector.py', 'chart_panel.py']:
        p = os.path.join(ROOT, "host", "gui", "widgets", fname)
        if os.path.isfile(p):
            with open(p, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            violations = []
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("import") or stripped.startswith("from "):
                    continue
                for m in re.finditer(r'"(#[0-9a-fA-F]{6})"', stripped):
                    violations.append(f"L{i}: {m.group(1)}")
            check(f"{fname} 无硬编码颜色", len(violations) == 0, str(violations[:3]))


def main():
    global PASS, FAIL
    print("=" * 50)
    print("  MonitorPage Redesign (Phase 4-4)")
    print("=" * 50)

    test_monitor_header()
    test_metric_selector()
    test_chart_panel()
    test_page_structure()
    test_node_switch()
    test_metric_switch()
    test_chart_update()
    test_lifecycle()
    test_backward_compat()
    test_no_store_import()
    test_theme_refs()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
