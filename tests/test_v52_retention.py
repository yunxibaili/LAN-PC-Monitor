# -*- coding: utf-8 -*-
"""
test_v52_retention.py —— Retention 测试（v5.2 Phase 5-5A）。

覆盖：
1. delete_before（插入 100 → 删除 before T → remaining 50）
2. 临界时间（timestamp == cutoff 保留，仅 < cutoff 删除）
3. RetentionService.run（返回各表计数）
4. 空表（返回 0）
5. 架构边界（RetentionService 不 import sqlite3）
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from host.storage.database import Database
from host.storage.records import MetricRecord, AlertHistoryRecord, SessionRecord
from host.storage.repositories.metrics_repo import MetricsRepository
from host.storage.repositories.alerts_repo import AlertsRepository
from host.storage.repositories.sessions_repo import SessionsRepository
from host.storage.retention import RetentionPolicy, RetentionService

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
    metrics = MetricsRepository(db)
    alerts = AlertsRepository(db)
    sessions = SessionsRepository(db)
    policy = RetentionPolicy(metrics_days=30, alerts_days=90, sessions_days=90)
    svc = RetentionService(policy, metrics, alerts, sessions)
    return db, metrics, alerts, sessions, svc


# ---------- 1. delete_before 基本 ----------

def test_delete_before():
    print("\n--- 1. delete_before ---")
    db, metrics, alerts, sessions, svc = _make()

    t0 = time.time()
    # 插入 100 条，时间从 t0 递增
    for i in range(100):
        metrics.insert(MetricRecord("A", "cpu", float(i), t0 + i))

    check("插入 100 条", metrics.count() == 100)

    # 删除 t0+50 之前的（即前 50 条）
    deleted = metrics.delete_before(t0 + 50)
    check("删除 50 条", deleted == 50)
    check("剩余 50 条", metrics.count() == 50)
    db.close()


# ---------- 2. 临界时间（仅 < cutoff） ----------

def test_boundary():
    print("\n--- 2. 临界时间 ---")
    db, metrics, alerts, sessions, svc = _make()

    t0 = time.time()
    metrics.insert(MetricRecord("A", "cpu", 1.0, t0))        # == cutoff
    metrics.insert(MetricRecord("A", "cpu", 2.0, t0 - 1))    # < cutoff
    metrics.insert(MetricRecord("A", "cpu", 3.0, t0 + 1))    # > cutoff

    deleted = metrics.delete_before(t0)
    check("仅删除 < cutoff 的 1 条", deleted == 1)
    check("剩余 2 条", metrics.count() == 2)
    db.close()


# ---------- 3. RetentionService.run ----------

def test_service_run():
    print("\n--- 3. RetentionService.run ---")
    db, metrics, alerts, sessions, svc = _make()

    now = time.time()
    # 旧数据（91 天前，早于所有 cutoff）
    old = now - 91 * 86400
    # 新数据
    recent = now

    metrics.insert(MetricRecord("A", "cpu", 1.0, old))
    metrics.insert(MetricRecord("A", "cpu", 2.0, recent))
    alerts.insert(AlertHistoryRecord("A", "N1", "x", "cpu", 1.0, 1.0, "red", old))
    alerts.insert(AlertHistoryRecord("A", "N1", "y", "cpu", 1.0, 1.0, "red", recent))
    sessions.create(SessionRecord("A", '{"x":1}', old))
    sessions.create(SessionRecord("A", '{"x":2}', recent))

    result = svc.run(now=now)
    check("metrics 删除 1", result["metrics"] == 1)
    check("alerts 删除 1", result["alerts"] == 1)
    check("sessions 删除 1", result["sessions"] == 1)
    check("metrics 剩余 1", metrics.count() == 1)
    db.close()


# ---------- 4. 空表 ----------

def test_empty():
    print("\n--- 4. 空表 ---")
    db, metrics, alerts, sessions, svc = _make()
    deleted = metrics.delete_before(time.time())
    check("空表删除 0", deleted == 0)

    result = svc.run()
    check("空表 run 全 0", result == {"metrics": 0, "alerts": 0, "sessions": 0})
    db.close()


# ---------- 5. 架构边界 ----------

def test_architecture():
    print("\n--- 5. 架构边界 ---")
    p = os.path.join(ROOT, "host", "storage", "retention.py")
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    check("无 import sqlite3", "import sqlite3" not in content)
    check("无 import host.gui", "import host.gui" not in content and "from host.gui" not in content)
    check("无 import PyQt5", "import PyQt5" not in content)


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  Retention Test (Phase 5-5A)")
    print("=" * 55)

    test_delete_before()
    test_boundary()
    test_service_run()
    test_empty()
    test_architecture()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
