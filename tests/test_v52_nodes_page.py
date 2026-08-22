# -*- coding: utf-8 -*-
"""
test_v52_nodes_page.py —— DevicesPage 组装测试（v5.3.4 Devices）。

验证：
1. VM 注入成功
2. 节点增加 -> DeviceCard 出现
3. 数据更新 -> Card 刷新
4. 节点删除 -> Card 移除
5. 统计行正确
6. 页面生命周期
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
from host.viewmodels.devices_vm import DevicesViewModel
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


def make_frame(cpu=45.0, ram=50.0, gpu=62.0):
    return {
        "type": "monitor_data", "ts": time.time(), "hostname": "test",
        "cpu": {"total_usage": cpu, "package_temp_c": 65},
        "gpu": {"usage_percent": gpu, "core_temp_c": 71},
        "ram": {"usage_percent": ram, "total_gb": 32, "used_gb": 16},
        "net": {"upload_mb_s": 12.3, "download_mb_s": 45.6},
        "net_quality": {"quality_score": 90},
        "fps": {"fps": 0}, "disk": [], "processes": {"top_cpu": [], "top_gpu": []},
    }


def test_vm_injection():
    print("\n--- 1. VM 注入 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = DevicesViewModel(ns, fs)
    page = NodesPage()
    page.set_view_model(vm)
    check("vm 已注入", page._vm is vm)


def test_node_add_card():
    print("\n--- 2. 节点增加 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = DevicesViewModel(ns, fs)
    page = NodesPage()
    page.set_view_model(vm)
    page.show()

    ns.add_node("game-pc", alias="游戏主机", ip="192.168.1.100")
    fs.push("game-pc", make_frame())
    page._refresh()
    check("cards 数量 = 1", len(page._cards) == 1)
    check("game-pc card 存在", "game-pc" in page._cards)


def test_stats():
    print("\n--- 3. 统计行 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = DevicesViewModel(ns, fs)
    page = NodesPage()
    page.set_view_model(vm)
    page.show()

    ns.add_node("a", alias="A"); ns.add_node("b", alias="B")
    ns.update_status("a", "connected")
    ns.update_status("b", "offline")
    fs.push("a", make_frame(cpu=90))
    fs.push("b", make_frame())
    page._refresh()
    check("total=2", page._stat_total._value_lbl.text() == "2")
    check("online=1", page._stat_online._value_lbl.text() == "1")
    check("offline=1", page._stat_offline._value_lbl.text() == "1")


def test_node_remove():
    print("\n--- 4. 节点删除 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = DevicesViewModel(ns, fs)
    page = NodesPage()
    page.set_view_model(vm)
    page.show()

    ns.add_node("a", alias="A"); ns.add_node("b", alias="B")
    fs.push("a", make_frame()); fs.push("b", make_frame())
    page._refresh()
    check("初始 2 cards", len(page._cards) == 2)

    ns.remove_node("a")
    page._refresh()
    check("删除后 1 card", len(page._cards) == 1)
    check("a 已移除", "a" not in page._cards)


def test_empty_state():
    print("\n--- 5. 空状态 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = DevicesViewModel(ns, fs)
    page = NodesPage()
    page.set_view_model(vm)
    page.show()

    page._refresh()
    check("空状态提示可见", page._empty.isVisible())
    check("滚动区域隐藏", not page._scroll.isVisible())

    ns.add_node("a", alias="A")
    fs.push("a", make_frame())
    page._refresh()
    check("添加后提示隐藏", not page._empty.isVisible())
    check("滚动区域显示", page._scroll.isVisible())


def test_lifecycle():
    print("\n--- 6. 生命周期 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = DevicesViewModel(ns, fs)
    page = NodesPage()
    page.set_view_model(vm)
    page.on_show()
    check("on_show OK", True)
    page.on_hide()
    check("on_hide OK", True)


def main():
    global PASS, FAIL
    print("=" * 50)
    print("  DevicesPage 组装测试 (v5.3.4)")
    print("=" * 50)

    test_vm_injection()
    test_node_add_card()
    test_stats()
    test_node_remove()
    test_empty_state()
    test_lifecycle()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
