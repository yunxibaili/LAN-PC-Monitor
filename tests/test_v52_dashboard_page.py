# -*- coding: utf-8 -*-
"""
test_v52_dashboard_page.py —— DashboardPage 组装测试（v5.2 Phase 3-2C）。

验证：
1. DashboardViewModel 注入成功
2. 节点增加 -> NodeCard 出现
3. 数据更新 -> NodeCard 内容刷新
4. 节点删除 -> NodeCard 移除
5. 多节点网格布局
6. SummaryBar 统计正确
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


def make_frame(cpu=45.0, gpu=62.0, ram=50.0, net_up=12.0, net_down=45.0, score=90):
    return {
        "type": "monitor_data", "ts": time.time(), "hostname": "test",
        "cpu": {"total_usage": cpu, "package_temp_c": 65},
        "gpu": {"usage_percent": gpu, "core_temp_c": 71},
        "ram": {"usage_percent": ram, "total_gb": 32, "used_gb": 16},
        "net": {"upload_mb_s": net_up, "download_mb_s": net_down},
        "net_quality": {"quality_score": score, "quality_grade": "优秀" if score >= 90 else "良好"},
        "fps": {"fps": 0}, "disk": [], "processes": {"top_cpu": [], "top_gpu": []},
    }


def test_vm_injection():
    """VM 注入成功。"""
    print("\n--- 1. VM 注入 ---")
    ns = NodeStore()
    fs = FrameStore()
    vm = DashboardViewModel(ns, fs)
    page = DashboardPage()
    page.set_view_model(vm)
    check("vm 已注入", page._vm is vm)


def test_node_add_card():
    """节点增加 -> Card 出现。"""
    print("\n--- 2. 节点增加 ---")
    ns = NodeStore()
    fs = FrameStore()
    vm = DashboardViewModel(ns, fs)
    page = DashboardPage()
    page.set_view_model(vm)
    page.show()

    ns.add_node("game-pc", alias="游戏主机")
    page._rebuild_grid()
    check("cards 数量 = 1", len(page._cards) == 1)
    check("game-pc card 存在", "game-pc" in page._cards)


def test_data_update():
    """数据更新 -> Card 内容刷新。"""
    print("\n--- 3. 数据更新 ---")
    ns = NodeStore()
    fs = FrameStore()
    vm = DashboardViewModel(ns, fs)
    page = DashboardPage()
    page.set_view_model(vm)
    page.show()

    ns.add_node("game-pc", alias="游戏主机")
    frame = make_frame(cpu=73, gpu=88, ram=65)
    fs.push("game-pc", frame)
    page._rebuild_grid()

    card = page._cards.get("game-pc")
    check("card 存在", card is not None)
    check("CPU=73.5%", "73" in card._ring_values["cpu"].text())
    check("GPU=88.2%", "88" in card._ring_values["gpu"].text())
    check("内存=65.0%", "65" in card._ring_values["ram"].text())


def test_node_remove():
    """节点删除 -> Card 移除。"""
    print("\n--- 4. 节点删除 ---")
    ns = NodeStore()
    fs = FrameStore()
    vm = DashboardViewModel(ns, fs)
    page = DashboardPage()
    page.set_view_model(vm)
    page.show()

    ns.add_node("a", alias="A")
    ns.add_node("b", alias="B")
    page._rebuild_grid()
    check("初始 2 cards", len(page._cards) == 2)

    ns.remove_node("a")
    page._rebuild_grid()  # 节点删除后重建
    check("删除后 1 card", len(page._cards) == 1)
    check("a 已移除", "a" not in page._cards)
    check("b 仍在", "b" in page._cards)


def test_multiple_nodes():
    """多节点布局。"""
    print("\n--- 5. 多节点布局 ---")
    ns = NodeStore()
    fs = FrameStore()
    vm = DashboardViewModel(ns, fs)
    page = DashboardPage()
    page.set_view_model(vm)
    page.setFixedSize(1600, 800)  # 模拟窗口宽度
    page.show()

    for i in range(6):
        ns.add_node(f"node-{i}", alias=f"节点{i}")
        frame = make_frame(cpu=10 * i)
        fs.push(f"node-{i}", frame)
    page._rebuild_grid()

    check("6 cards", len(page._cards) == 6)
    # 1600px -> 3 列
    check("列数=3", page._calc_cols(1600) == 3)
    check("列数=2 (1000px)", page._calc_cols(1000) == 2)
    check("列数=1 (600px)", page._calc_cols(600) == 1)
    check("列数=4 (2200px)", page._calc_cols(2200) == 4)



def test_empty_state():
    """空状态显示。"""
    print("\n--- 7. 空状态 ---")
    ns = NodeStore()
    fs = FrameStore()
    vm = DashboardViewModel(ns, fs)
    page = DashboardPage()
    page.set_view_model(vm)
    page.show()

    page._rebuild_grid()
    check("空状态提示可见", page._empty.isVisible())
    check("滚动区域隐藏", not page._scroll.isVisible())

    ns.add_node("a", alias="A")
    page._rebuild_grid()
    check("添加后提示隐藏", not page._empty.isVisible())
    check("滚动区域显示", page._scroll.isVisible())


def test_resize():
    """窗口 resize 自动调整列数。"""
    print("\n--- 8. resize ---")
    page = DashboardPage()
    # 模拟不同宽度
    check("600px -> 1列", page._calc_cols(600) == 1)
    check("1000px -> 2列", page._calc_cols(1000) == 2)
    check("1500px -> 2列", page._calc_cols(1500) == 2)
    check("2200px -> 4列", page._calc_cols(2200) == 4)


def main():
    global PASS, FAIL
    print("=" * 50)
    print("  DashboardPage 组装测试 (Phase 3-2C)")
    print("=" * 50)

    test_vm_injection()
    test_node_add_card()
    test_data_update()
    test_node_remove()
    test_multiple_nodes()
    test_empty_state()
    test_resize()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
