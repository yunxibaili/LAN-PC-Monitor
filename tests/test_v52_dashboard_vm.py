# -*- coding: utf-8 -*-
"""
test_v52_dashboard_vm.py —— DashboardViewModel 单元测试（v5.2 Phase 3-2A）。

验证：
1. 节点新增 → DashboardNodeData 生成
2. 帧更新 → 指标字段填充
3. 状态变更 → status 字段更新
4. 评分更新 → quality_score/grade 更新
5. 节点移除 → DashboardNodeData 清理
6. Signal 触发
"""
import os
import sys
import time

# 确保项目根目录在 sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from host.store.frame_store import FrameStore
from host.store.node_store import NodeStore
from host.viewmodels.dashboard_vm import DashboardViewModel, DashboardNodeData


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


def make_test_frame(cpu=45.0, gpu=62.0, ram=50.0, net_up=12.0, net_down=45.0):
    """构造测试用 monitor_data 帧。"""
    return {
        "type": "monitor_data",
        "ts": time.time(),
        "hostname": "test-host",
        "cpu": {"total_usage": cpu, "package_temp_c": 65.0},
        "gpu": {"usage_percent": gpu, "core_temp_c": 71.0},
        "ram": {"usage_percent": ram, "total_gb": 32.0, "used_gb": 16.0},
        "net": {"upload_mb_s": net_up, "download_mb_s": net_down},
        "net_quality": {"quality_score": 95, "quality_grade": "优秀"},
        "fps": {"fps": 142, "frame_time_ms": 7.0},
        "disk": [],
        "processes": {"top_cpu": [], "top_gpu": []},
    }


def test_node_added():
    """测试：节点新增 → DashboardNodeData 生成。"""
    print("\n--- 1. 节点新增 ---")
    ns = NodeStore()
    fs = FrameStore()
    vm = DashboardViewModel(ns, fs)

    # 触发节点新增
    ns.add_node("game-pc", alias="游戏主机", ip="192.168.1.100", port=12345)

    check("节点数量 = 1", vm.count() == 1, f"got {vm.count()}")
    data = vm.get_node("game-pc")
    check("DashboardNodeData 存在", data is not None)
    check("node_id 正确", data.node_id == "game-pc")
    check("alias 正确", data.alias == "游戏主机")
    check("status = connecting", data.status == "connecting")
    check("指标初始为 0", data.cpu_usage == 0.0 and data.gpu_usage == 0.0)

    # 幂等：再次 add_node 不重复
    ns.add_node("game-pc", alias="游戏主机")
    check("幂等：数量仍为 1", vm.count() == 1)


def test_frame_update():
    """测试：帧更新 → 指标字段填充。"""
    print("\n--- 2. 帧更新 ---")
    ns = NodeStore()
    fs = FrameStore()
    vm = DashboardViewModel(ns, fs)

    ns.add_node("game-pc", alias="游戏主机")
    frame = make_test_frame(cpu=45.2, gpu=62.1, ram=49.8, net_up=12.3, net_down=45.6)
    fs.push("game-pc", frame)

    data = vm.get_node("game-pc")
    check("cpu_usage = 45.2", data.cpu_usage == 45.2, f"got {data.cpu_usage}")
    check("gpu_usage = 62.1", data.gpu_usage == 62.1, f"got {data.gpu_usage}")
    check("memory_usage = 49.8", data.memory_usage == 49.8, f"got {data.memory_usage}")
    check("network_rx = 45.6", data.network_rx == 45.6, f"got {data.network_rx}")
    check("network_tx = 12.3", data.network_tx == 12.3, f"got {data.network_tx}")


def test_status_change():
    """测试：状态变更 → status 字段更新。"""
    print("\n--- 3. 状态变更 ---")
    ns = NodeStore()
    fs = FrameStore()
    vm = DashboardViewModel(ns, fs)

    ns.add_node("game-pc")
    ns.update_status("game-pc", "connected")

    data = vm.get_node("game-pc")
    check("status = connected", data.status == "connected", f"got {data.status}")

    ns.update_status("game-pc", "offline")
    check("status = offline", data.status == "offline", f"got {data.status}")


def test_quality_update():
    """测试：评分更新 → quality_score/grade 更新。"""
    print("\n--- 4. 评分更新 ---")
    ns = NodeStore()
    fs = FrameStore()
    vm = DashboardViewModel(ns, fs)

    ns.add_node("game-pc")
    score, grade = ns.update_quality("game-pc", rtt_ms=5.0, loss_percent=0.0)

    data = vm.get_node("game-pc")
    check("quality_score = " + str(score), data.quality_score == score, f"got {data.quality_score}")
    check("quality_grade = " + grade, data.quality_grade == grade, f"got {data.quality_grade}")


def test_node_removed():
    """测试：节点移除 → DashboardNodeData 清理。"""
    print("\n--- 5. 节点移除 ---")
    ns = NodeStore()
    fs = FrameStore()
    vm = DashboardViewModel(ns, fs)

    ns.add_node("game-pc")
    ns.add_node("office-pc")
    check("初始数量 = 2", vm.count() == 2)

    ns.remove_node("game-pc")
    check("移除后数量 = 1", vm.count() == 1)
    check("game-pc 已移除", vm.get_node("game-pc") is None)
    check("office-pc 仍在", vm.get_node("office-pc") is not None)

    # 幂等
    ns.remove_node("game-pc")
    check("幂等移除", vm.count() == 1)


def test_signals():
    """测试：Signal 触发。"""
    print("\n--- 6. Signal 触发 ---")
    ns = NodeStore()
    fs = FrameStore()
    vm = DashboardViewModel(ns, fs)

    nodes_changed_count = [0]
    data_changed_ids = []

    def on_nodes_changed():
        nodes_changed_count[0] += 1

    def on_data_changed(node_id):
        data_changed_ids.append(node_id)

    vm.nodes_changed.connect(on_nodes_changed)
    vm.data_changed.connect(on_data_changed)

    ns.add_node("game-pc")
    check("nodes_changed 触发 1 次", nodes_changed_count[0] == 1)

    frame = make_test_frame()
    fs.push("game-pc", frame)
    check("data_changed 触发 1 次", len(data_changed_ids) == 1)
    check("data_changed 携带 node_id", data_changed_ids[0] == "game-pc")

    ns.remove_node("game-pc")
    check("nodes_changed 累计 2 次", nodes_changed_count[0] == 2)


def test_to_dict():
    """测试：DashboardNodeData.to_dict() 序列化。"""
    print("\n--- 7. to_dict ---")
    data = DashboardNodeData(node_id="test", alias="测试")
    data.cpu_usage = 50.0
    data.status = "connected"
    d = data.to_dict()
    check("to_dict 包含所有字段", len(d) == 10, f"got {len(d)} keys")
    check("cpu_usage in dict", d["cpu_usage"] == 50.0)
    check("node_id in dict", d["node_id"] == "test")


def test_safe_float():
    """测试：_safe_float 容错。"""
    print("\n--- 8. _safe_float ---")
    from host.viewmodels.dashboard_vm import _safe_float
    check("float", _safe_float(42.5) == 42.5)
    check("int -> float", _safe_float(10) == 10.0)
    check("string -> float", _safe_float("33.3") == 33.3)
    check("N/A -> 0", _safe_float("N/A") == 0.0)
    check("None -> 0", _safe_float(None) == 0.0)
    check("invalid -> 0", _safe_float("abc") == 0.0)
    check("custom default", _safe_float(None, -1) == -1.0)


def main():
    global PASS, FAIL
    print("=" * 50)
    print("  DashboardViewModel 单元测试 (Phase 3-2A)")
    print("=" * 50)

    test_node_added()
    test_frame_update()
    test_status_change()
    test_quality_update()
    test_node_removed()
    test_signals()
    test_to_dict()
    test_safe_float()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
