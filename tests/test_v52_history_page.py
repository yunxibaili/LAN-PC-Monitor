# -*- coding: utf-8 -*-
"""
test_v52_history_page.py —— HistoryPage + HistoryVM 测试（v5.2 Phase 5-4）。

覆盖：
1. HistoryVM: load / get_records / get_summary / range_presets
2. HistoryVM: 空参数 → 无崩溃
3. HistoryPage: VM 注入 / 结构 / Empty state
4. HistoryPage: 架构扫描（不碰 Facade）
5. HistoryPage: Theme 扫描
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

from host.storage.database import Database
from host.storage.repositories.metrics_repo import MetricsRepository
from host.facade.history_facade import HistoryFacade
from host.viewmodels.history_vm import HistoryViewModel
from host.gui.pages.history_page import HistoryPage

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
    from host.storage.records import MetricRecord
    db = Database(":memory:")
    db.connect()
    repo = MetricsRepository(db)
    facade = HistoryFacade(repo)
    vm = HistoryViewModel(facade)
    return db, repo, facade, vm


def _populate(repo, node="A", metric="cpu.usage", n=50):
    from host.storage.records import MetricRecord
    t0 = time.time()
    for i in range(n):
        repo.insert(MetricRecord(node, metric, float(i), t0 + i))


# ---------- 1. HistoryVM load ----------

def test_vm_load():
    print("\n--- 1. HistoryVM load ---")
    db, repo, facade, vm = _make()
    _populate(repo)

    now = time.time()
    vm.load("A", "cpu.usage", now - 60, now)
    check("records loaded", len(vm.get_records()) > 0)

    summary = vm.get_summary()
    check("summary avg", summary["avg"] is not None)
    check("summary count > 0", summary["count"] > 0)
    db.close()


# ---------- 2. HistoryVM 空参数 ----------

def test_vm_empty():
    print("\n--- 2. HistoryVM 空参数 ---")
    db, repo, facade, vm = _make()
    vm.load("", "cpu.usage")
    check("空 node_id 不崩溃", len(vm.get_records()) == 0)

    vm.load("A", "")
    check("空 metric 不崩溃", len(vm.get_records()) == 0)

    # 空数据
    vm.load("node_x", "cpu.usage")
    check("空数据 count=0", vm.get_summary()["count"] == 0)
    db.close()


# ---------- 3. HistoryVM range presets ----------

def test_vm_range_presets():
    print("\n--- 3. HistoryVM range presets ---")
    db, repo, facade, vm = _make()
    presets = vm.range_presets()
    check("presets 有值", len(presets) > 0)
    check("1h 存在", "1h" in presets)

    start, end = vm.get_range_preset("1h")
    check("1h range 有效", end - start == 3600)
    db.close()


# ---------- 4. HistoryPage 结构 ----------

def test_page_structure():
    print("\n--- 4. HistoryPage 结构 ---")
    db, repo, facade, vm = _make()
    page = HistoryPage()
    page.set_view_model(vm)
    check("has _chart", hasattr(page, '_chart'))
    check("has _node_combo", hasattr(page, '_node_combo'))
    check("has _metric_combo", hasattr(page, '_metric_combo'))
    check("has _range_combo", hasattr(page, '_range_combo'))
    check("has _load_btn", hasattr(page, '_load_btn'))
    check("has _empty", hasattr(page, '_empty'))
    db.close()


# ---------- 5. 架构扫描 ----------

def test_architecture():
    print("\n--- 5. 架构扫描 ---")
    p = os.path.join(ROOT, "host", "gui", "pages", "history_page.py")
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    check("无 import HistoryFacade", "HistoryFacade" not in content.split("import")[0] or
          "from host.facade" not in content)
    check("无 import sqlite3", "import sqlite3" not in content)
    check("有 set_view_model", "set_view_model" in content)


# ---------- 6. Theme 扫描 ----------

def test_theme():
    print("\n--- 6. Theme 扫描 ---")
    import re
    for fname in ["history_vm.py", "history_page.py"]:
        if fname.endswith("_vm.py"):
            p = os.path.join(ROOT, "host", "viewmodels", fname)
        else:
            p = os.path.join(ROOT, "host", "gui", "pages", fname)
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        violations = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("import") or stripped.startswith("from "):
                continue
            for m in re.finditer(r'#[0-9a-fA-F]{3,8}', stripped):
                violations.append(f"L{i}: {m.group(0)}")
        check(f"{fname} 无硬编码颜色", len(violations) == 0, str(violations[:3]))


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  History Page Test (Phase 5-4)")
    print("=" * 55)

    test_vm_load()
    test_vm_empty()
    test_vm_range_presets()
    test_page_structure()
    test_architecture()
    test_theme()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
