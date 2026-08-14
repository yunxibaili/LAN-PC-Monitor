# -*- coding: utf-8 -*-
"""
test_v52_storage.py —— Storage Foundation 测试（v5.2 Phase 5-1）。

覆盖：
1. Database: create / schema / version
2. MetricsRepository: insert / query / aggregate / count
3. AlertsRepository: insert / query / count
4. SessionsRepository: create / query / count
5. Architecture: gui → storage = 0, vm → sqlite3 = 0
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from host.storage.database import Database
from host.storage.schema import SCHEMA_VERSION
from host.storage.records import MetricRecord, AlertHistoryRecord, SessionRecord
from host.storage.repositories.metrics_repo import MetricsRepository
from host.storage.repositories.alerts_repo import AlertsRepository
from host.storage.repositories.sessions_repo import SessionsRepository

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


def _make_db():
    db = Database(":memory:")
    db.connect()
    return db


# ---------- 1. Database ----------

def test_database():
    print("\n--- 1. Database ---")
    db = _make_db()
    check("connected", db._conn is not None)
    check("schema version", db.version == SCHEMA_VERSION)
    db.close()
    check("closed", db._conn is None)

    # Context manager
    with Database(":memory:") as db2:
        check("context manager connect", db2._conn is not None)
    check("context manager close", db2._conn is None)


# ---------- 2. MetricsRepository ----------

def test_metrics_repo():
    print("\n--- 2. MetricsRepository ---")
    db = _make_db()
    repo = MetricsRepository(db)

    now = time.time()
    repo.insert(MetricRecord("A", "cpu", 45.0, now))
    repo.insert(MetricRecord("A", "cpu", 50.0, now + 1))
    repo.insert(MetricRecord("A", "gpu", 62.0, now))
    repo.insert(MetricRecord("B", "cpu", 30.0, now))

    check("count all", repo.count() == 4)
    check("count node A", repo.count(node_id="A") == 3)
    check("count metric cpu", repo.count(metric="cpu") == 3)
    check("count A+cpu", repo.count(node_id="A", metric="cpu") == 2)

    # query_range
    results = repo.query_range("A", "cpu")
    check("query A/cpu", len(results) == 2)
    check("query ordered ASC", results[0].value == 45.0)

    # aggregate
    agg = repo.aggregate("A", "cpu")
    check("agg avg", agg["avg"] == 47.5)
    check("agg count", agg["count"] == 2)

    # nodes / metrics
    check("nodes", set(repo.nodes()) == {"A", "B"})
    check("metrics A", set(repo.metrics("A")) == {"cpu", "gpu"})

    # empty query
    empty = repo.query_range("Z", "nonexistent")
    check("empty query", len(empty) == 0)

    db.close()


# ---------- 3. AlertsRepository ----------

def test_alerts_repo():
    print("\n--- 3. AlertsRepository ---")
    db = _make_db()
    repo = AlertsRepository(db)

    now = time.time()
    repo.insert(AlertHistoryRecord("A", "NodeA", "CPU high", "cpu", 95.0, 90.0, "red", now))
    repo.insert(AlertHistoryRecord("B", "NodeB", "MEM high", "ram", 85.0, 80.0, "warn", now + 1))
    repo.insert(AlertHistoryRecord("A", "NodeA", "GPU high", "gpu", 92.0, 85.0, "red", now + 2))

    check("count all", repo.count() == 3)
    check("count red", repo.count(level="red") == 2)
    check("count warn", repo.count(level="warn") == 1)

    recent = repo.query_recent(2)
    check("recent limit 2", len(recent) == 2)
    check("recent ordered desc", recent[0].timestamp >= recent[1].timestamp)

    by_level = repo.query_by_level("red")
    check("by_level red", len(by_level) == 2)

    by_node = repo.query_by_node("A")
    check("by_node A", len(by_node) == 2)

    db.close()


# ---------- 4. SessionsRepository ----------

def test_sessions_repo():
    print("\n--- 4. SessionsRepository ---")
    db = _make_db()
    repo = SessionsRepository(db)

    now = time.time()
    repo.create(SessionRecord("A", '{"cpu": 45}', now))
    repo.create(SessionRecord("A", '{"cpu": 50}', now + 1))
    repo.create(SessionRecord("B", '{"cpu": 30}', now))

    check("count all", repo.count() == 3)
    check("count A", repo.count(node_id="A") == 2)

    recent = repo.query_recent("A", 1)
    check("recent A limit 1", len(recent) == 1)
    check("recent A desc", recent[0].snapshot == '{"cpu": 50}')

    recent_all = repo.query_recent(limit=2)
    check("recent all limit 2", len(recent_all) == 2)

    db.close()


# ---------- 5. Records ----------

def test_records():
    print("\n--- 5. Records ---")
    m = MetricRecord("A", "cpu", 45.0, 1.0)
    check("MetricRecord to_dict", m.to_dict()["value"] == 45.0)

    a = AlertHistoryRecord("A", "N1", "high", "cpu", 95.0, 90.0, "red", 1.0)
    check("AlertHistoryRecord to_dict", a.to_dict()["level"] == "red")

    s = SessionRecord("A", '{"x":1}', 1.0)
    check("SessionRecord to_dict", s.to_dict()["snapshot"] == '{"x":1}')


# ---------- 6. Architecture ----------

def test_architecture():
    print("\n--- 6. Architecture ---")
    # storage 不 import gui
    storage_dir = os.path.join(ROOT, "host", "storage")
    for root_dir, dirs, files in os.walk(storage_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(root_dir, f)
            with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "import host.gui" in stripped or "from host.gui" in stripped:
                    rel = p.replace(ROOT + os.sep, "")
                    check("storage 无 gui import", False, f"{rel}:{i}")
                    return
    check("storage 无 gui import", True)

    # viewmodels 不 import sqlite3
    vm_dir = os.path.join(ROOT, "host", "viewmodels")
    for root_dir, dirs, files in os.walk(vm_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(root_dir, f)
            with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
            if "sqlite3" in content:
                rel = p.replace(ROOT + os.sep, "")
                check("viewmodels 无 sqlite3", False, f"{rel}")
                return
    check("viewmodels 无 sqlite3", True)


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  Storage Foundation Test (Phase 5-1)")
    print("=" * 55)

    test_database()
    test_metrics_repo()
    test_alerts_repo()
    test_sessions_repo()
    test_records()
    test_architecture()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
