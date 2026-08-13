# -*- coding: utf-8 -*-
"""
test_v52_node_widgets.py —— Dashboard UI 组件单元测试（v5.2 Phase 3-2B）。

验证：
1. DashboardNodeData 更新后 UI 刷新
2. StatusBadge 状态切换
3. MetricBar 数值更新
4. QualityBadge 评分更新
5. 多个 NodeCard 独立工作
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt5.QtWidgets import QApplication

# 确保 QApplication 存在（Qt 组件需要）
import sys as _sys
if not _sys.argv:
    _sys.argv = ["test"]
_app = QApplication.instance() or QApplication(_sys.argv)

from host.gui.widgets.status_badge import StatusBadge
from host.gui.widgets.metric_bar import MetricBar
from host.gui.widgets.quality_badge import QualityBadge
from host.gui.widgets.node_card import NodeCard
from host.viewmodels.dashboard_vm import DashboardNodeData

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


def test_status_badge():
    """StatusBadge 状态切换。"""
    print("\n--- 1. StatusBadge ---")
    badge = StatusBadge()
    badge.set_status("connected")
    check("connected 文字", badge.get_status() == "ONLINE")

    badge.set_status("offline")
    check("offline 文字", badge.get_status() == "OFFLINE")

    badge.set_status("connecting")
    check("connecting 文字", badge.get_status() == "CONNECTING")

    badge.set_status("unknown")
    check("unknown 文字", badge.get_status() == "UNKNOWN")

    badge.set_status("auth_failed")
    check("auth_failed 文字", badge.get_status() == "AUTH FAILED")

    badge.set_status("bogus_status")
    check("未知状态 fallback", badge.get_status() == "UNKNOWN")


def test_metric_bar():
    """MetricBar 数值更新。"""
    print("\n--- 2. MetricBar ---")
    bar = MetricBar("CPU", "%")

    bar.set_metric("CPU", 45.2, "%")
    check("CPU 45.2%", "45.2%" in bar._value_label.text())

    bar.set_metric("GPU", 62.1, "%")
    check("GPU 62.1%", "62.1%" in bar._value_label.text())
    check("进度条值=62", bar._bar.value() == 62)

    bar.set_metric("内存", 50.0, "%")
    check("内存 50.0%", "50.0%" in bar._value_label.text())

    bar.set_metric("网络", 12.3, "MB/s")
    check("网络 12.3 MB/s", "12.3 MB/s" in bar._value_label.text())

    # 边界
    bar.set_metric("X", -5, "%")
    check("负值 clamp=0", bar._bar.value() == 0)
    bar.set_metric("X", 150, "%")
    check("超限 clamp=100", bar._bar.value() == 100)


def test_quality_badge():
    """QualityBadge 评分更新。"""
    print("\n--- 3. QualityBadge ---")
    badge = QualityBadge()

    badge.set_score(95, "优秀")
    check("score=95", "95" in badge._score_label.text())
    check("grade=优秀", "优秀" in badge._grade_label.text())

    badge.set_score(70, "良好")
    check("score=70", badge._score_label.text() == "70")
    check("grade=良好", badge._grade_label.text() == "良好")

    badge.set_score(40, "较差")
    check("score=40", badge._score_label.text() == "40")


def test_node_card():
    """NodeCard 从 DashboardNodeData 更新。"""
    print("\n--- 4. NodeCard ---")
    card = NodeCard("game-pc", alias="游戏主机")

    data = DashboardNodeData(node_id="game-pc", alias="游戏主机")
    data.status = "connected"
    data.cpu_usage = 45.2
    data.gpu_usage = 62.1
    data.memory_usage = 49.8
    data.network_rx = 45.6
    data.network_tx = 12.3
    data.quality_score = 95
    data.quality_grade = "优秀"

    card.update_data(data)

    check("alias 正确", card._alias_lbl.text() == "游戏主机")
    check("状态=在线", card._status_badge.text() == "ONLINE")
    check("CPU=45%", "45" in card._ring_values["cpu"].text())
    check("GPU=62%", "62" in card._ring_values["gpu"].text())
    check("内存=50%", "50" in card._ring_values["ram"].text())
    check("网络显示", "45.6" in card._net_lbl.text())
    check("评分=95", card._score_lbl.text() is not None and "95" in card._score_lbl.text())
    check("等级=优秀", card._score_lbl.text() is not None and "优秀" in card._score_lbl.text())


def test_node_card_independent():
    """多个 NodeCard 独立更新，互不影响。"""
    print("\n--- 5. 多卡片独立 ---")
    card_a = NodeCard("a", alias="节点A")
    card_b = NodeCard("b", alias="节点B")

    data_a = DashboardNodeData("a", "节点A")
    data_a.cpu_usage = 30.0
    data_a.status = "connected"
    data_a.quality_score = 90

    data_b = DashboardNodeData("b", "节点B")
    data_b.cpu_usage = 80.0
    data_b.status = "offline"
    data_b.quality_score = 50

    card_a.update_data(data_a)
    card_b.update_data(data_b)

    check("A CPU=30%", "30" in card_a._ring_values["cpu"].text())
    check("B CPU=80%", "80" in card_b._ring_values["cpu"].text())
    check("A status=在线", card_a._status_badge.text() == "ONLINE")
    check("B status=离线", card_b._status_badge.text() == "OFFLINE")
    check("A score=90", "90" in (card_a._score_lbl.text() or ""))
    check("B score=50", "50" in (card_b._score_lbl.text() or ""))


def test_node_card_update():
    """NodeCard 数据更新后覆盖旧值。"""
    print("\n--- 6. 卡片更新覆盖 ---")
    card = NodeCard("x", alias="X")
    d1 = DashboardNodeData("x", "X")
    d1.cpu_usage = 10.0
    d1.status = "connecting"
    card.update_data(d1)
    check("初始 CPU=10", "10" in card._ring_values["cpu"].text())

    d2 = DashboardNodeData("x", "X")
    d2.cpu_usage = 90.0
    d2.status = "connected"
    card.update_data(d2)
    check("更新后 CPU=90", "90" in card._ring_values["cpu"].text())
    check("更新后 status=在线", card._status_badge.text() == "ONLINE")


def main():
    global PASS, FAIL
    print("=" * 50)
    print("  NodeCard/StatusBadge/MetricBar/QualityBadge 测试")
    print("  (Phase 3-2B)")
    print("=" * 50)

    test_status_badge()
    test_metric_bar()
    test_quality_badge()
    test_node_card()
    test_node_card_independent()
    test_node_card_update()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
