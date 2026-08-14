# -*- coding: utf-8 -*-
"""
test_metric_persistence.py —— MetricPersistenceService 测试（v5.2 Phase 5-2）。

覆盖：
1. frame → records 转换
2. batch insert 验证
3. 多节点聚合
4. 空 frame 处理
5. 字段映射正确性
6. 写入失败不崩溃
7. 架构边界
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from host.storage.database import Database
from host.storage.repositories.metrics_repo import MetricsRepository
from host.services.metric_persistence import MetricPersistenceService

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


def _make():
    db = Database(":memory:")
    db.connect()
    repo = MetricsRepository(db)
    svc = MetricPersistenceService(repo)
    return db, repo, svc


def _full_frame():
    return {
        "ts": 1000.0,
        "cpu": {"total_usage": 45.2, "package_temp_c": 65.0, "power_w": 85.0},
        "gpu": {"usage_percent": 62.0, "core_temp_c": 71.0, "power_w": 120.0},
        "ram": {"usage_percent": 50.0},
        "net": {"upload_mb_s": 12.3, "download_mb_s": 45.6},
        "net_quality": {"quality_score": 95.0},
        "fps": {"fps": 142.0, "frame_time_ms": 7.0},
    }


# ---------- 1. 单 frame 写入 ----------

def test_persist_frame():
    print("\n--- 1. 单 frame 写入 ---")
    db, repo, svc = _make()
    count = svc.persist_frame("A", _full_frame())
    check("写入记录数 > 0", count > 0, f"count={count}")
    check("repo.count == count", repo.count() == count)
    db.close()


# ---------- 2. batch 验证 ----------

def test_batch_insert():
    print("\n--- 2. batch 验证 ---")
    db, repo, svc = _make()

    class FakeRepo:
        def __init__(self):
            self.insert_batch_calls = 0
            self.insert_calls = 0
            self.last_batch = []
        def insert_batch(self, records):
            self.insert_batch_calls += 1
            self.last_batch = records
        def insert(self, record):
            self.insert_calls += 1

    fake = FakeRepo()
    svc2 = MetricPersistenceService(fake)
    svc2.persist_frame("A", _full_frame())

    check("insert_batch 调用 1 次", fake.insert_batch_calls == 1)
    check("insert 未调用", fake.insert_calls == 0)
    check("batch 有记录", len(fake.last_batch) > 0)


# ---------- 3. 多节点 ----------

def test_multi_node():
    print("\n--- 3. 多节点 ---")
    db, repo, svc = _make()
    svc.persist_frame("A", _full_frame())
    svc.persist_frame("B", _full_frame())
    check("total count", repo.count() > 0)
    check("nodes = 2", set(repo.nodes()) == {"A", "B"})


# ---------- 4. 空 frame ----------

def test_empty_frame():
    print("\n--- 4. 空 frame ---")
    db, repo, svc = _make()
    count = svc.persist_frame("A", {})
    check("空 frame count=0", count == 0)
    check("repo 无记录", repo.count() == 0)

    count2 = svc.persist_frame("A", None)
    check("None frame count=0", count2 == 0)
    db.close()


# ---------- 5. 字段映射 ----------

def test_field_mapping():
    print("\n--- 5. 字段映射 ---")
    db, repo, svc = _make()
    svc.persist_frame("A", _full_frame())

    # 验证特定 metric 存在
    cpu_records = repo.query_range("A", "cpu.usage")
    check("cpu.usage 存在", len(cpu_records) > 0)
    check("cpu.usage 值正确", cpu_records[0].value == 45.2)

    gpu_records = repo.query_range("A", "gpu.temp")
    check("gpu.temp 存在", len(gpu_records) > 0)
    check("gpu.temp 值正确", gpu_records[0].value == 71.0)

    fps_records = repo.query_range("A", "fps.value")
    check("fps.value 存在", len(fps_records) > 0)
    check("fps.value 值正确", fps_records[0].value == 142.0)
    db.close()


# ---------- 6. 写入失败不崩溃 ----------

def test_failure_resilience():
    print("\n--- 6. 写入失败不崩溃 ---")
    db, repo, svc = _make()

    class FailRepo:
        def insert_batch(self, records):
            raise RuntimeError("DB error")
    svc2 = MetricPersistenceService(FailRepo())
    count = svc2.persist_frame("A", _full_frame())
    check("失败返回 0", count == 0)
    check("不崩溃", True)


# ---------- 7. 架构边界 ----------

def test_architecture():
    print("\n--- 7. 架构边界 ---")
    p = os.path.join(ROOT, "host", "services", "metric_persistence.py")
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    check("无 import host.gui", "import host.gui" not in content and "from host.gui" not in content)
    check("无 import sqlite3", "import sqlite3" not in content)
    check("无 import HistoryStore", "HistoryStore" not in content)
    check("使用 insert_batch", "insert_batch" in content)


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  MetricPersistenceService Test (Phase 5-2)")
    print("=" * 55)

    test_persist_frame()
    test_batch_insert()
    test_multi_node()
    test_empty_frame()
    test_field_mapping()
    test_failure_resilience()
    test_architecture()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
