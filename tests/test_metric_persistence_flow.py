# -*- coding: utf-8 -*-
"""
test_metric_persistence_flow.py —— MetricPersistence 数据流集成测试（v5.2 Cleanup）。

验证：DataController._on_data 调用 MetricPersistenceService.persist_frame，
数据真正写入 SQLite。

覆盖：
1. frame → DataController → PersistenceService → Repository → record
2. 无 persistence 注入时 DataController 不崩溃
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from host.gui.controllers.data_controller import DataController
from host.service.metric_persistence import MetricPersistenceService
from host.storage.database import Database
from host.storage.repositories.metrics_repo import MetricsRepository
from host.store.frame_store import FrameStore
from host.store.node_store import NodeStore
from host.store.history_store import HistoryStore

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


def _frame():
    return {
        "type": "monitor_data", "ts": time.time(), "hostname": "test",
        "cpu": {"total_usage": 45.2, "package_temp_c": 65.0},
        "gpu": {"usage_percent": 62.0, "core_temp_c": 71.0},
        "ram": {"usage_percent": 50.0},
        "net": {"upload_mb_s": 12.3, "download_mb_s": 45.6},
        "net_quality": {"quality_score": None},
        "fps": {"fps": 142.0},
    }


class _FakeDiscovery:
    def auto_discover_background(self, on_found=None):
        pass


# ---------- 1. 完整数据流 ----------

def test_persistence_flow():
    print("\n--- 1. frame → DataController → SQLite ---")
    db = Database(":memory:")
    db.connect()
    repo = MetricsRepository(db)
    persistence = MetricPersistenceService(repo)

    frame_store = FrameStore()
    node_store = NodeStore()
    history_store = HistoryStore(maxlen=300)

    dc = DataController(
        cfg={}, frame_store=frame_store, node_store=node_store,
        history_store=history_store, discovery=_FakeDiscovery(),
        persistence=persistence)

    dc._on_data(_frame(), "A")
    persistence.flush()  # 批合并：flush 落库

    check("metrics 表有数据", repo.count() > 0)
    check("cpu.usage 记录存在", len(repo.query_range("A", "cpu.usage")) == 1)
    check("gpu.usage 记录存在", len(repo.query_range("A", "gpu.usage")) == 1)
    db.close()


# ---------- 2. 无 persistence 不崩溃 ----------

def test_no_persistence():
    print("\n--- 2. 无 persistence 注入不崩溃 ---")
    frame_store = FrameStore()
    node_store = NodeStore()
    history_store = HistoryStore(maxlen=300)

    dc = DataController(
        cfg={}, frame_store=frame_store, node_store=node_store,
        history_store=history_store, discovery=_FakeDiscovery(),
        persistence=None)

    dc._on_data(_frame(), "A")
    check("无 persistence 不崩溃", True)
    check("frame_store 仍写入", frame_store.get("A") is not None)


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  MetricPersistence Flow Test (Cleanup)")
    print("=" * 55)

    test_persistence_flow()
    test_no_persistence()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
