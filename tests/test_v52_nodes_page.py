# -*- coding: utf-8 -*-
"""
test_v52_nodes_page.py —— NodesPage 组装测试（v5.2 Phase 3-3B）。

验证：
1. VM 注入成功
2. 节点列表显示
3. 选中节点 -> DetailPanel 更新
4. 多节点切换
5. 页面生命周期 on_show/on_hide
6. context_action 信号转发
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
from host.viewmodels.node_detail_vm import NodeDetailViewModel
from host.gui.pages.nodes_page import NodesPage

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


def full_frame():
    return {
        "type": "monitor_data", "ts": time.time(), "hostname": "test",
        "system": {"hostname": "test", "local_ip": "1.2.3.4", "uptime_seconds": 100},
        "cpu": {"name": "X", "total_usage": 45.2, "physical_cores": 8,
                "logical_cores": 16, "core_freq_mhz": 4500,
                "package_temp_c": 65.0, "power_w": 65.0},
        "ram": {"total_gb": 32, "used_gb": 16, "available_gb": 16,
                "usage_percent": 50.0, "swap_used_mb": 0},
        "gpu": {"name": "RTX", "usage_percent": 62.1,
                "vram_used_mb": 8192, "vram_total_mb": 12288,
                "core_temp_c": 71.0, "hotspot_temp_c": 82.0,
                "core_freq_mhz": 2400, "power_w": 185.0},
        "disk": [{"drive": "C:", "read_mb_s": 120, "write_mb_s": 85,
                  "usage_percent": 78, "free_gb": 45}],
        "net": {"interface": "eth", "upload_mb_s": 12.3,
                "download_mb_s": 45.6, "link_speed_mbps": 1000},
        "net_quality": {"latency_to_client_ms": 0.45,
                        "latency_to_gateway_ms": 1.2,
                        "packet_loss_percent": 0.0,
                        "quality_score": 95, "quality_grade": "优秀"},
        "fps": {"window_title": "Game", "fps": 142,
                "frame_time_ms": 7.04, "low_1_percent": 118, "source": "presentmon"},
        "processes": {"top_cpu": [{"name": "chrome", "usage_percent": 12}],
                      "top_gpu": [{"name": "game", "usage_percent": 48}]},
    }


def test_vm_injection():
    print("\n--- 1. VM 注入 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = NodeDetailViewModel(ns, fs)
    page = NodesPage()
    page.set_view_model(vm)
    page.set_stores(frame=fs, node=ns)
    check("vm 已注入", page._node_detail_vm is vm)


def test_node_list_display():
    print("\n--- 2. 节点列表 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = NodeDetailViewModel(ns, fs)
    page = NodesPage()
    page.set_view_model(vm)
    page.show()

    # 添加节点到 NodeExplorer（v5.2 Phase 4-3：_explorer 替代 node_list）
    page._explorer.add_node("localhost", "本机", "127.0.0.1")
    page._explorer.add_node("game-pc", "游戏主机", "192.168.1.100")
    check("列表有 2 项", len(page._explorer._items) == 2)


def test_select_updates_detail():
    print("\n--- 3. 选中节点 -> DetailDashboard ---")
    ns = NodeStore(); fs = FrameStore()
    vm = NodeDetailViewModel(ns, fs)
    page = NodesPage()
    page.set_view_model(vm)
    page.show()

    page._explorer.add_node("game-pc", "游戏主机", "192.168.1.100")
    ns.add_node("game-pc", alias="游戏主机", ip="192.168.1.100")
    fs.push("game-pc", full_frame())

    # 模拟选中
    page.select_node("game-pc")
    check("current_node 设置", page.get_current_node() == "game-pc")
    check("DetailDashboard name 已更新", page._dashboard._name_lbl.text() != "未选择节点")


def test_node_switch():
    print("\n--- 4. 多节点切换 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = NodeDetailViewModel(ns, fs)
    page = NodesPage()
    page.set_view_model(vm)
    page.show()

    page._explorer.add_node("A", "节点A", "1.1.1.1")
    page._explorer.add_node("B", "节点B", "2.2.2.2")
    ns.add_node("A"); ns.add_node("B")

    f_a = full_frame(); f_a["cpu"]["total_usage"] = 20.0
    f_b = full_frame(); f_b["cpu"]["total_usage"] = 80.0
    fs.push("A", f_a); fs.push("B", f_b)

    page.select_node("A")
    check("选中 A", page.get_current_node() == "A")

    page.select_node("B")
    check("切换到 B", page.get_current_node() == "B")


def test_lifecycle():
    print("\n--- 5. 生命周期 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = NodeDetailViewModel(ns, fs)
    page = NodesPage()
    page.set_view_model(vm)

    # on_show 不崩溃
    page.on_show()
    check("on_show OK", True)

    # on_hide 不崩溃
    page.on_hide()
    check("on_hide OK", True)


def test_signals():
    print("\n--- 6. 信号 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = NodeDetailViewModel(ns, fs)
    page = NodesPage()
    page.set_view_model(vm)
    page.show()

    selected_ids = []
    page.node_selected.connect(lambda nid: selected_ids.append(nid))

    page._explorer.add_node("X", "节点X", "3.3.3.3")
    page.select_node("X")
    check("node_selected 触发", len(selected_ids) == 1)
    check("node_selected 携带 X", selected_ids[0] == "X")


def main():
    global PASS, FAIL
    print("=" * 50)
    print("  NodesPage 组装测试 (Phase 3-3B)")
    print("=" * 50)

    test_vm_injection()
    test_node_list_display()
    test_select_updates_detail()
    test_node_switch()
    test_lifecycle()
    test_signals()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
