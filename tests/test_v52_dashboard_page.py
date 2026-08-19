# -*- coding: utf-8 -*-
"""
test_v52_dashboard_page.py —— DashboardPage 组装测试（v5.4 实时折线图版）。

验证：
1. ViewModel 注入成功
2. 指标条 + Summary 存在
3. 数据刷新 -> 指标条 / 折线图缓冲更新
4. 实时图表缓冲区上限
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


def make_frame(cpu=45.0, gpu=62.0, ram=50.0, net_up=12.0, net_down=45.0):
    return {
        "type": "monitor_data", "ts": time.time(), "hostname": "test",
        "cpu": {"total_usage": cpu, "package_temp_c": 65},
        "gpu": {"usage_percent": gpu, "core_temp_c": 71},
        "ram": {"usage_percent": ram, "total_gb": 32, "used_gb": 16},
        "net": {"upload_mb_s": net_up, "download_mb_s": net_down},
        "net_quality": {"quality_score": 90},
        "fps": {"fps": 0}, "disk": [], "processes": {"top_cpu": [], "top_gpu": []},
    }


def test_vm_injection():
    print("\n--- 1. VM 注入 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = DashboardViewModel(ns, fs)
    page = DashboardPage()
    page.set_view_model(vm)
    check("vm 已注入", page._vm is vm)


def test_components_exist():
    print("\n--- 2. 组件存在 ---")
    page = DashboardPage()
    check("有 _bar_cpu", hasattr(page, '_bar_cpu'))
    check("有 _bar_gpu", hasattr(page, '_bar_gpu'))
    check("有 _bar_ram", hasattr(page, '_bar_ram'))
    check("有 _bar_net", hasattr(page, '_bar_net'))
    check("有 _chart 折线图", hasattr(page, '_chart'))
    check("有 _card_total", hasattr(page, '_card_total'))
    check("有 _series 数据缓冲", hasattr(page, '_series'))


def test_data_update_bars():
    print("\n--- 3. 数据更新 -> 指标条 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = DashboardViewModel(ns, fs)
    page = DashboardPage()
    page.set_view_model(vm)
    page.show()

    ns.add_node("game-pc", alias="游戏主机")
    ns.update_status("game-pc", "connected")
    fs.push("game-pc", make_frame(cpu=73, gpu=88, ram=65))
    # 触发一次刷新
    page._flush_refresh()

    check("CPU 缓冲有数据", len(page._series["CPU"]) > 0)
    check("GPU 缓冲有数据", len(page._series["GPU"]) > 0)
    check("RAM 缓冲有数据", len(page._series["RAM"]) > 0)


def test_chart_buffer_limit():
    print("\n--- 4. 折线图缓冲上限 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = DashboardViewModel(ns, fs)
    page = DashboardPage()
    page.set_view_model(vm)
    page.show()

    ns.add_node("a", alias="A")
    ns.update_status("a", "connected")
    for i in range(80):
        fs.push("a", make_frame(cpu=i))
        page._flush_refresh()
        time.sleep(0.005)

    # 缓冲应限制在 MAX_POINTS=60
    check("CPU 缓冲 ≤60", len(page._series["CPU"]) <= 60)
    check("NET 缓冲 ≤60", len(page._series["NET"]) <= 60)


def test_summary_update():
    print("\n--- 5. Summary 更新 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = DashboardViewModel(ns, fs)
    page = DashboardPage()
    page.set_view_model(vm)
    page.show()

    ns.add_node("a", alias="A")
    ns.update_status("a", "connected")
    fs.push("a", make_frame())
    page._update_summary_vm()

    check("total=1", page._card_total._value_lbl.text() == "1")


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  DashboardPage 测试 (v5.4 实时折线图)")
    print("=" * 55)

    test_vm_injection()
    test_components_exist()
    test_data_update_bars()
    test_chart_buffer_limit()
    test_summary_update()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
