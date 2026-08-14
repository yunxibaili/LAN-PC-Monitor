# -*- coding: utf-8 -*-
"""
test_v52_history_query.py —— History Query API 测试（v5.2 Phase 5-3）。

覆盖：
1. range query（时间区间）
2. latest（最近 N 条，倒序）
3. aggregation（avg/min/max/count）
4. node isolation（不串数据）
5. empty result（返回 []）
6. 错误语义（非法参数 ValueError）
7. 架构边界（Facade 不 import UI）
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from host.storage.database import Database
from host.storage.repositories.metrics_repo import MetricsRepository
from host.storage.records import MetricRecord
from host.facade.history_facade import HistoryFacade

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
    facade = HistoryFacade(repo)
    return db, repo, facade


# ---------- 1. Range Query ----------

def test_range_query():
    print("\n--- 1. Range Query ---")
    db, repo, facade = _make()
    t0 = 1000.0
    for i in range(5):
        repo.insert(MetricRecord("A", "cpu", 10.0 + i, t0 + i))

    # 查询 t0+1 ~ t0+3（含边界）
    results = facade.query_range("A", "cpu", t0 + 1, t0 + 3)
    check("range 返回 3 条", len(results) == 3, f"got {len(results)}")
    check("range 升序", results[0].timestamp < results[-1].timestamp)

    # 无重叠区间
    empty = facade.query_range("A", "cpu", t0 + 100, t0 + 200)
    check("无重叠返回空", len(empty) == 0)
    db.close()


# ---------- 2. Latest Query ----------

def test_latest():
    print("\n--- 2. Latest Query ---")
    db, repo, facade = _make()
    t0 = 2000.0
    for i in range(100):
        repo.insert(MetricRecord("A", "cpu", float(i), t0 + i))

    results = facade.latest("A", "cpu", limit=10)
    check("latest 返回 10 条", len(results) == 10)
    check("latest 倒序 (newest first)", results[0].timestamp > results[-1].timestamp)
    check("latest 首条是最新值", results[0].value == 99.0)
    db.close()


# ---------- 3. Aggregation ----------

def test_aggregation():
    print("\n--- 3. Aggregation ---")
    db, repo, facade = _make()
    t0 = 3000.0
    values = [10.0, 20.0, 30.0, 40.0]
    for i, v in enumerate(values):
        repo.insert(MetricRecord("A", "cpu", v, t0 + i))

    agg = facade.aggregate("A", "cpu")
    check("avg", agg["avg"] == 25.0, f"got {agg['avg']}")
    check("min", agg["min"] == 10.0)
    check("max", agg["max"] == 40.0)
    check("count", agg["count"] == 4)
    db.close()


# ---------- 4. Node Isolation ----------

def test_node_isolation():
    print("\n--- 4. Node Isolation ---")
    db, repo, facade = _make()
    t0 = 4000.0
    for i in range(3):
        repo.insert(MetricRecord("A", "cpu", 10.0, t0 + i))
        repo.insert(MetricRecord("B", "cpu", 90.0, t0 + i))

    a_results = facade.latest("A", "cpu", limit=10)
    b_results = facade.latest("B", "cpu", limit=10)
    check("A 只含 A", all(r.node_id == "A" for r in a_results))
    check("B 只含 B", all(r.node_id == "B" for r in b_results))
    check("A 值域正确", all(r.value == 10.0 for r in a_results))
    check("B 值域正确", all(r.value == 90.0 for r in b_results))
    db.close()


# ---------- 5. Empty Result ----------

def test_empty_result():
    print("\n--- 5. Empty Result ---")
    db, repo, facade = _make()

    r = facade.latest("node_x", "cpu")
    check("latest 空返回 []", r == [])

    r2 = facade.query_range("node_x", "cpu")
    check("range 空返回 []", r2 == [])

    agg = facade.aggregate("node_x", "cpu")
    check("aggregate 空 count=0", agg["count"] == 0)
    db.close()


# ---------- 6. 错误语义 ----------

def test_error_semantics():
    print("\n--- 6. 错误语义 ---")
    db, repo, facade = _make()

    try:
        facade.latest("", "cpu")
        check("空 node_id 抛 ValueError", False)
    except ValueError:
        check("空 node_id 抛 ValueError", True)

    try:
        facade.query_range("A", "")
        check("空 metric 抛 ValueError", False)
    except ValueError:
        check("空 metric 抛 ValueError", True)

    try:
        facade.aggregate("", "")
        check("空参数 aggregate 抛 ValueError", False)
    except ValueError:
        check("空参数 aggregate 抛 ValueError", True)
    db.close()


# ---------- 7. 架构边界 ----------

def test_architecture():
    print("\n--- 7. 架构边界 ---")
    p = os.path.join(ROOT, "host", "facade", "history_facade.py")
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    check("无 import host.gui", "import host.gui" not in content and "from host.gui" not in content)
    check("无 import sqlite3", "import sqlite3" not in content)
    check("无 import PyQt5", "import PyQt5" not in content)


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  History Query API Test (Phase 5-3)")
    print("=" * 55)

    test_range_query()
    test_latest()
    test_aggregation()
    test_node_isolation()
    test_empty_result()
    test_error_semantics()
    test_architecture()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
