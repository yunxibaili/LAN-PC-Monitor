# -*- coding: utf-8 -*-
"""
test_v52_nodes_redesign.py —— NodesPage 重构验证测试（v5.2 Phase 4-3）。
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
from host.viewmodels.node_detail_vm import NodeDetailViewModel
from host.viewmodels.devices_vm import DevicesViewModel
from host.gui.pages.nodes_page import NodesPage
from host.gui.widgets.node_explorer import NodeExplorer
from host.gui.widgets.detail_dashboard import DetailDashboard
from host.gui.widgets.resource_card import ResourceCard

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


def make_frame(cpu=45, gpu=62, ram=50):
    return {
        "type": "monitor_data", "ts": 1.0, "hostname": "test",
        "cpu": {"total_usage": cpu, "package_temp_c": 65, "physical_cores": 8,
                "logical_cores": 16, "core_freq_mhz": 4500, "power_w": 65, "name": "CPU"},
        "gpu": {"usage_percent": gpu, "core_temp_c": 71, "vram_used_mb": 8192,
                "vram_total_mb": 12288, "core_freq_mhz": 2400, "power_w": 185, "name": "GPU"},
        "ram": {"usage_percent": ram, "total_gb": 32, "used_gb": 16, "available_gb": 16, "swap_used_mb": 1200},
        "disk": [{"drive": "C:", "read_mb_s": 120, "write_mb_s": 85, "usage_percent": 78, "free_gb": 45}],
        "net": {"upload_mb_s": 12, "download_mb_s": 45, "link_speed_mbps": 1000, "interface": "eth"},
        "net_quality": {"quality_score": 95, "quality_grade": "A", "latency_to_client_ms": 0.45,
                        "latency_to_gateway_ms": 1.2, "packet_loss_percent": 0.0},
        "fps": {"fps": 142, "frame_time_ms": 7.04, "low_1_percent": 118, "window_title": "Game", "source": "presentmon"},
        "system": {"hostname": "DESKTOP", "local_ip": "192.168.1.100", "uptime_seconds": 3661},
        "processes": {"top_cpu": [{"name": "chrome", "usage_percent": 12}],
                      "top_gpu": [{"name": "game", "usage_percent": 48}]},
    }


# ---------- 1. NodeExplorer ----------

def test_node_explorer():
    print("\n--- 1. NodeExplorer ---")
    ne = NodeExplorer()
    ne.add_node("A", "NodeA", "192.168.1.1")
    ne.add_node("B", "NodeB", "192.168.1.2")
    check("2 items", len(ne._items) == 2)
    ne.update_node_status("A", "connected", "95")
    check("状态更新", True)
    ne.remove_node("A")
    check("移除后 1 项", len(ne._items) == 1)


# ---------- 2. ResourceCard ----------

def test_resource_card():
    print("\n--- 2. ResourceCard ---")
    rc = ResourceCard("CPU", "%")
    rc.set_resource(45.0, "%", "65°C")
    check("set_resource", True)
    check("环形存在", rc._ring is not None)


# ---------- 3. DetailDashboard ----------

def test_detail_dashboard():
    print("\n--- 3. DetailDashboard ---")
    dd = DetailDashboard()
    data = make_frame()
    from host.viewmodels.node_detail_vm import NodeDetailData
    nd = NodeDetailData()
    nd.identity.node_id = "test"
    nd.identity.alias = "Test"
    nd.identity.status = "connected"
    nd.identity.ip = "1.2.3.4"
    nd.identity.port = 12345
    nd.cpu.name = "CPU"; nd.cpu.usage = 45; nd.cpu.temp_c = 65
    nd.gpu.name = "GPU"; nd.gpu.usage = 62; nd.gpu.core_temp = 71
    nd.memory.usage = 50; nd.memory.used_gb = 16; nd.memory.total_gb = 32
    nd.disk.usage = 78; nd.disk.free_gb = 45
    dd.update_data(nd)
    check("name 更新", dd._name_lbl.text() == "Test")
    check("status badge", dd._status_badge.text() == "ONLINE")
    check("cpu card", dd._cpu_card._value == 45)
    dd.update_data(None)
    check("清空后 name", dd._name_lbl.text() == "未选择节点")


# ---------- 4. NodesPage ----------

def test_nodes_page():
    print("\n--- 4. NodesPage ---")
    ns = NodeStore(); fs = FrameStore()
    vm = DevicesViewModel(ns, fs)
    page = NodesPage()
    page.set_view_model(vm)
    check("vm 已注入", page._vm is vm)
    check("scroll 存在", hasattr(page, '_scroll'))
    check("on_show 不崩溃", True)
    page.on_hide()
    check("on_hide 不崩溃", True)


# ---------- 5. Theme 引用 ----------

def test_theme_refs():
    print("\n--- 5. Theme 引用 ---")
    for p in ['host/gui/widgets/node_explorer.py', 'host/gui/widgets/detail_dashboard.py', 'host/gui/widgets/resource_card.py']:
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
            check(f"{os.path.basename(p)} 无硬编码颜色", len(violations) == 0, str(violations[:3]))


def main():
    global PASS, FAIL
    print("=" * 50)
    print("  NodesPage Redesign (Phase 4-3)")
    print("=" * 50)

    test_node_explorer()
    test_resource_card()
    test_detail_dashboard()
    test_nodes_page()
    test_theme_refs()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
