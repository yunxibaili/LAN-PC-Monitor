# -*- coding: utf-8 -*-
"""
test_v52_storage_service.py —— StorageService 测试（v5.2 Phase 5-5B）。

覆盖：
1. StorageService 组装（Database + 3 repo + facade + retention）
2. history_facade() 返回可用的 HistoryFacade
3. retention_service() / run_retention() 正常
4. 架构边界（service 不 import gui / PyQt5）
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from host.service.storage_service import StorageService
from host.facade.history_facade import HistoryFacade
from host.storage.retention import RetentionPolicy, RetentionService
from host.storage.records import MetricRecord

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


# ---------- 1. StorageService 组装 ----------

def test_assemble():
    print("\n--- 1. StorageService 组装 ---")
    svc = StorageService(":memory:")
    check("metrics_repo 存在", svc.metrics_repo is not None)
    check("alerts_repo 存在", svc.alerts_repo is not None)
    check("sessions_repo 存在", svc.sessions_repo is not None)
    svc.close()


# ---------- 2. history_facade ----------

def test_history_facade():
    print("\n--- 2. history_facade ---")
    svc = StorageService(":memory:")
    facade = svc.history_facade()
    check("返回 HistoryFacade", isinstance(facade, HistoryFacade))

    # 写入 + 查询
    svc.metrics_repo.insert(MetricRecord("A", "cpu", 42.0, time.time()))
    results = facade.latest("A", "cpu")
    check("facade 可用", len(results) == 1)
    svc.close()


# ---------- 3. retention ----------

def test_retention():
    print("\n--- 3. retention ---")
    svc = StorageService(":memory:")
    svc.metrics_repo.insert(MetricRecord("A", "cpu", 1.0, time.time() - 100 * 86400))
    result = svc.run_retention()
    check("run_retention 返回 dict", isinstance(result, dict))
    check("metrics 有删除", result["metrics"] == 1)
    svc.close()


# ---------- 4. 架构边界 ----------

def test_architecture():
    print("\n--- 4. 架构边界 ---")
    p = os.path.join(ROOT, "host", "service", "storage_service.py")
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    check("无 import host.gui", "import host.gui" not in content and "from host.gui" not in content)
    check("无 import PyQt5", "import PyQt5" not in content)


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  StorageService Test (Phase 5-5B)")
    print("=" * 55)

    test_assemble()
    test_history_facade()
    test_retention()
    test_architecture()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
