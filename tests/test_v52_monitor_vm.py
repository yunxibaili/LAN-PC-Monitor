# -*- coding: utf-8 -*-
"""
test_v52_monitor_vm.py —— MonitorViewModel 单元测试（v5.2 Phase 3-5B）。

覆盖：
1. ChartPoint 创建
2. MetricSeries 创建
3. push 后 get_history
4. limit 生效
5. 空数据
6. 多节点隔离
7. get_available_metrics
8. get_node_ids
9. get_summary
10. refresh signal
11. 源码扫描：无 FrameStore/Connection/QTimer
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from host.store.history_store import HistoryStore
from host.store.node_store import NodeStore
from host.viewmodels.monitor_vm import (
    MonitorViewModel, ChartPoint, MetricSeries, METRIC_DEFS,
)

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


# ---------- 1. ChartPoint ----------

def test_chart_point():
    print("\n--- 1. ChartPoint ---")
    p = ChartPoint(timestamp=100.0, value=42.5)
    check("timestamp", p.timestamp == 100.0)
    check("value", p.value == 42.5)
    d = p.to_dict()
    check("to_dict", d["timestamp"] == 100.0 and d["value"] == 42.5)


# ---------- 2. MetricSeries ----------

def test_metric_series():
    print("\n--- 2. MetricSeries ---")
    pts = [ChartPoint(1.0, 10), ChartPoint(2.0, 20)]
    ms = MetricSeries(node_id="A", metric="cpu", points=pts)
    check("node_id", ms.node_id == "A")
    check("metric", ms.metric == "cpu")
    check("points len", len(ms.points) == 2)


# ---------- 3. push 后 get_history ----------

def test_push_get_history():
    print("\n--- 3. push 后 get_history ---")
    hs = HistoryStore(maxlen=60)
    ns = NodeStore()
    vm = MonitorViewModel(hs, ns)

    now = time.time()
    hs.push("A", "cpu", 45.0, now)
    hs.push("A", "cpu", 55.0, now + 1)
    hs.push("A", "gpu", 62.0, now + 2)

    pts = vm.get_history("A", "cpu")
    check("cpu 2 个点", len(pts) == 2)
    check("值正确", pts[-1].value == 55.0)  # 最新在最后

    pts_gpu = vm.get_history("A", "gpu")
    check("gpu 1 个点", len(pts_gpu) == 1)


# ---------- 4. limit 生效 ----------

def test_limit():
    print("\n--- 4. limit 生效 ---")
    hs = HistoryStore(maxlen=60)
    ns = NodeStore()
    vm = MonitorViewModel(hs, ns)

    for i in range(10):
        hs.push("A", "cpu", float(i))
    pts = vm.get_history("A", "cpu", limit=3)
    check("limit=3 返回 3 个点", len(pts) == 3)
    check("最新值在列表中", any(p.value == 9.0 for p in pts))


# ---------- 5. 空数据 ----------

def test_empty():
    print("\n--- 5. 空数据 ---")
    hs = HistoryStore()
    ns = NodeStore()
    vm = MonitorViewModel(hs, ns)

    check("空节点 history", vm.get_history("X", "cpu") == [])
    check("空节点 metrics", vm.get_available_metrics("X") == [])
    check("空节点 summary", vm.get_summary("X") == {
        "node_id": "X", "alias": "X", "metrics": [], "points": 0})


# ---------- 6. 多节点隔离 ----------

def test_multi_node():
    print("\n--- 6. 多节点隔离 ---")
    hs = HistoryStore(maxlen=60)
    ns = NodeStore()
    vm = MonitorViewModel(hs, ns)

    hs.push("A", "cpu", 20.0)
    hs.push("B", "cpu", 80.0)

    check("A.cpu=20", vm.get_history("A", "cpu")[0].value == 20.0)
    check("B.cpu=80", vm.get_history("B", "cpu")[0].value == 80.0)

    # 更新 A 不影响 B
    hs.push("A", "cpu", 55.0)
    check("A 更新后", vm.get_history("A", "cpu", limit=1)[0].value == 55.0)
    check("B 不变", vm.get_history("B", "cpu")[0].value == 80.0)


# ---------- 7. get_available_metrics ----------

def test_available_metrics():
    print("\n--- 7. get_available_metrics ---")
    hs = HistoryStore(maxlen=60)
    ns = NodeStore()
    vm = MonitorViewModel(hs, ns)

    hs.push("A", "cpu", 1.0)
    hs.push("A", "gpu", 2.0)
    hs.push("A", "ram", 3.0)
    hs.push("A", "net_up", 4.0)

    m = vm.get_available_metrics("A")
    check("4 个指标", len(m) == 4)
    check("含 cpu", "cpu" in m)
    check("含 gpu", "gpu" in m)
    check("含 net_up", "net_up" in m)

    # 无数据节点
    check("空节点", vm.get_available_metrics("X") == [])


# ---------- 8. get_node_ids ----------

def test_node_ids():
    print("\n--- 8. get_node_ids ---")
    hs = HistoryStore(maxlen=60)
    ns = NodeStore()
    vm = MonitorViewModel(hs, ns)

    ns.add_node("A")
    ns.add_node("B")
    ns.add_node("C")

    hs.push("A", "cpu", 1.0)
    hs.push("B", "cpu", 2.0)
    # C 无历史数据

    ids = vm.get_node_ids()
    check("有数据的节点", set(ids) == {"A", "B"})
    check("C 不在列表", "C" not in ids)


# ---------- 9. get_summary ----------

def test_summary():
    print("\n--- 9. get_summary ---")
    hs = HistoryStore(maxlen=60)
    ns = NodeStore()
    vm = MonitorViewModel(hs, ns)

    ns.add_node("A", alias="游戏主机")
    hs.push("A", "cpu", 1.0)
    hs.push("A", "gpu", 2.0)
    hs.push("A", "ram", 3.0)

    s = vm.get_summary("A")
    check("node_id", s["node_id"] == "A")
    check("alias", s["alias"] == "游戏主机")
    check("metrics", set(s["metrics"]) == {"cpu", "gpu", "ram"})
    check("points", s["points"] == 3)

    # 空节点
    s2 = vm.get_summary("X")
    check("空节点 points=0", s2["points"] == 0)
    check("空节点 metrics=[]", s2["metrics"] == [])


# ---------- 10. refresh signal ----------

def test_refresh_signal():
    print("\n--- 10. refresh signal ---")
    hs = HistoryStore(maxlen=60)
    ns = NodeStore()
    vm = MonitorViewModel(hs, ns)

    ns.add_node("A")
    hs.push("A", "cpu", 1.0)

    emitted = []
    vm.data_changed.connect(lambda nid: emitted.append(nid))

    vm.refresh("A")
    check("refresh A 发射", emitted == ["A"])

    emitted.clear()
    vm.refresh()  # 全部
    check("refresh all 发射", emitted == ["A"])


# ---------- 11. point_added signal ----------

def test_point_added_signal():
    print("\n--- 11. point_added signal ---")
    hs = HistoryStore(maxlen=60)
    ns = NodeStore()
    vm = MonitorViewModel(hs, ns)

    emitted = []
    vm.data_changed.connect(lambda nid: emitted.append(nid))

    hs.push("A", "cpu", 1.0)
    check("push 触发 data_changed", emitted == ["A"])

    hs.push("A", "gpu", 2.0)
    check("再次 push", emitted == ["A", "A"])


# ---------- 12. node_removed signal ----------

def test_node_removed_signal():
    print("\n--- 12. node_removed signal ---")
    hs = HistoryStore(maxlen=60)
    ns = NodeStore()
    vm = MonitorViewModel(hs, ns)

    hs.push("A", "cpu", 1.0)
    emitted = []
    vm.data_changed.connect(lambda nid: emitted.append(nid))

    hs.remove_node("A")
    check("remove 触发 data_changed", emitted == ["A"])


# ---------- 13. 源码扫描 ----------

def test_no_forbidden_imports():
    print("\n--- 13. 源码扫描 ---")
    p = os.path.join(ROOT, "host", "viewmodels", "monitor_vm.py")
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    import_lines = [l.strip() for l in lines
                    if l.strip().startswith("import ") or l.strip().startswith("from ")]
    all_imports = " ".join(import_lines)
    check("无 FrameStore import", "FrameStore" not in all_imports)
    check("无 NodeConnection import", "NodeConnection" not in all_imports)
    check("无 QTimer import", "QTimer" not in all_imports)
    check("有 Signal import", "Signal" in all_imports)
    # HistoryStore/NodeStore 通过构造函数注入，检查全文件
    full = open(p, "r", encoding="utf-8", errors="ignore").read()
    check("引用 HistoryStore", "history_store" in full)
    check("引用 NodeStore", "node_store" in full)


# ---------- 14. METRIC_DEFS ----------

def test_metric_defs():
    print("\n--- 14. METRIC_DEFS ---")
    check("6 个指标定义", len(METRIC_DEFS) == 6)
    check("cpu 有 label", "label" in METRIC_DEFS["cpu"])
    check("cpu y_range", METRIC_DEFS["cpu"]["y_range"] == (0, 100))
    check("net_up 无 y_range", METRIC_DEFS["net_up"]["y_range"] is None)


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  MonitorViewModel 单元测试 (Phase 3-5B)")
    print("=" * 55)

    test_chart_point()
    test_metric_series()
    test_push_get_history()
    test_limit()
    test_empty()
    test_multi_node()
    test_available_metrics()
    test_node_ids()
    test_summary()
    test_refresh_signal()
    test_point_added_signal()
    test_node_removed_signal()
    test_no_forbidden_imports()
    test_metric_defs()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
