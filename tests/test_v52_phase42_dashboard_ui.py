# -*- coding: utf-8 -*-
"""
test_v52_phase42_dashboard_ui.py —— DashboardPage 重构验证测试（v5.2 Phase 4-2B）。
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

from host.store.frame_store import FrameStore
from host.store.node_store import NodeStore
from host.viewmodels.dashboard_vm import DashboardViewModel
from host.gui.pages.dashboard_page import DashboardPage

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


def make_frame(cpu=45, gpu=62, ram=50, net_up=12, net_down=45, score=90):
    return {
        "type": "monitor_data", "ts": 1.0, "hostname": "test",
        "cpu": {"total_usage": cpu, "package_temp_c": 65},
        "gpu": {"usage_percent": gpu, "core_temp_c": 71},
        "ram": {"usage_percent": ram, "total_gb": 32, "used_gb": 16},
        "net": {"upload_mb_s": net_up, "download_mb_s": net_down},
        "net_quality": {"quality_score": score, "quality_grade": "good"},
        "fps": {"fps": 0}, "disk": [], "processes": {"top_cpu": [], "top_gpu": []},
        "system": {"hostname": "test", "local_ip": "1.2.3.4", "uptime_seconds": 100},
    }


# ---------- 1. VM 注入 ----------

def test_vm_injection():
    print("\n--- 1. VM 注入 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = DashboardViewModel(ns, fs)
    page = DashboardPage()
    page.set_view_model(vm)
    check("vm 已注入", page._vm is vm)


# ---------- 2. 空节点状态 ----------

def test_empty_state():
    print("\n--- 2. 空节点状态 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = DashboardViewModel(ns, fs)
    page = DashboardPage()
    page.set_view_model(vm)
    page.show()

    page._rebuild_grid()
    check("空状态提示可见", page._empty.isVisible())
    check("滚动区域隐藏", not page._scroll.isVisible())
    check("total=0", page._card_total._value_lbl.text() == "0")


# ---------- 3. 多节点渲染 ----------

def test_multi_node():
    print("\n--- 3. 多节点渲染 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = DashboardViewModel(ns, fs)
    page = DashboardPage()
    page.set_view_model(vm)
    page.show()

    for i in range(4):
        ns.add_node(f"node-{i}", alias=f"Node{i}")
        fs.push(f"node-{i}", make_frame(cpu=10 * i))

    page._rebuild_grid()
    check("4 cards", len(page._cards) == 4)
    check("空状态隐藏", not page._empty.isVisible())
    check("滚动区域显示", page._scroll.isVisible())
    check("total=4", page._card_total._value_lbl.text() == "4")


# ---------- 4. card 点击 ----------

def test_card_click():
    print("\n--- 4. card 点击 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = DashboardViewModel(ns, fs)
    page = DashboardPage()
    page.set_view_model(vm)
    page.show()

    ns.add_node("A", alias="NodeA")
    page._rebuild_grid()

    clicked_ids = []
    page.card_clicked.connect(lambda nid: clicked_ids.append(nid))
    page._on_card_clicked("A")
    check("card_clicked 信号", clicked_ids == ["A"])


# ---------- 5. theme 引用扫描 ----------

def test_theme_refs():
    print("\n--- 5. theme 引用扫描 ---")
    p = os.path.join(ROOT, "host", "gui", "pages", "dashboard_page.py")
    with open(p, "r", encoding="utf-8") as f:
        lines = f.readlines()

    violations = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("import") or stripped.startswith("from "):
            continue
        for m in re.finditer(r'"(#[0-9a-fA-F]{6})"', stripped):
            violations.append(f"L{i}: {m.group(1)}")

    check("无硬编码颜色", len(violations) == 0, str(violations[:3]))

    # 检查 ThemeColors / ThemeSpacing 引用
    all_imports = " ".join(l.strip() for l in lines
                          if l.strip().startswith("import ") or l.strip().startswith("from "))
    check("使用 ThemeColors", "ThemeColors" in all_imports)
    check("使用 ThemeSpacing", "ThemeSpacing" in all_imports)


# ---------- 6. DashboardPage 生命周期 ----------

def test_lifecycle():
    print("\n--- 6. 生命周期 ---")
    page = DashboardPage()
    page.on_show()
    check("on_show OK", True)
    page.on_hide()
    check("on_hide OK", True)


def main():
    global PASS, FAIL
    print("=" * 50)
    print("  DashboardPage 重构验证 (Phase 4-2B)")
    print("=" * 50)

    test_vm_injection()
    test_empty_state()
    test_multi_node()
    test_card_click()
    test_theme_refs()
    test_lifecycle()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
