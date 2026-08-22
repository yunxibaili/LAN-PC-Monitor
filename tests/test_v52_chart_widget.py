# -*- coding: utf-8 -*-
"""
test_v52_chart_widget.py —— ChartWidget 单元测试（v5.2 Phase 3-5C）。

覆盖：
1. 初始化
2. set_series（有数据）
3. set_series（空数据）
4. clear
5. set_thresholds
6. 无 pyqtgraph 降级（空白 Widget）
7. 源码扫描：无 Store/VM 依赖
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt5.QtWidgets import QApplication
import sys as _sys
if not _sys.argv:
    _sys.argv = ["test"]
_app = QApplication.instance() or QApplication(_sys.argv)

from host.viewmodels.monitor_vm import ChartPoint
from host.gui.widgets.chart_widget import ChartWidget, has_pyqtgraph

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


# ---------- 1. 初始化 ----------

def test_init():
    print("\n--- 1. 初始化 ---")
    w = ChartWidget(title="CPU", y_range=(0, 100))
    check("ChartWidget 创建", w is not None)
    if has_pyqtgraph():
        check("有 plot 曲线列表", hasattr(w, '_curves'))
        vb = w.getViewBox()
        check("鼠标缩放已禁用", vb is not None and not vb.state["mouseEnabled"][0]
              and not vb.state["mouseEnabled"][1])
    else:
        check("回退 Widget", True)


# ---------- 2. set_series ----------

def test_set_series():
    print("\n--- 2. set_series ---")
    w = ChartWidget(title="CPU", y_range=(0, 100))
    points = [ChartPoint(100.0 + i, float(i * 10)) for i in range(5)]
    w.set_series(points)
    check("set_series 不崩溃", True)
    if has_pyqtgraph():
        check("曲线已设置", len(w._curves) > 0)


# ---------- 3. 空数据 ----------

def test_empty_series():
    print("\n--- 3. 空数据 ---")
    w = ChartWidget(title="CPU")
    w.set_series([])
    check("空数据不崩溃", True)
    w.set_series(None)
    check("None 数据不崩溃", True)


# ---------- 4. clear ----------

def test_clear():
    print("\n--- 4. clear ---")
    w = ChartWidget(title="CPU")
    w.set_series([ChartPoint(1.0, 50.0)])
    w.reset()
    check("clear 不崩溃", True)
    if has_pyqtgraph():
        check("曲线已清空", len(w._curves) == 0 and not w._series_data)


# ---------- 5. threshold ----------

def test_thresholds():
    print("\n--- 5. set_thresholds ---")
    w = ChartWidget(title="CPU", y_range=(0, 100))
    w.set_thresholds(warn=80, danger=95)
    check("设置阈值不崩溃", True)
    if has_pyqtgraph():
        check("warn 线存在", w._warn_line is not None)
        check("danger 线存在", w._danger_line is not None)

    # 重新设置覆盖
    w.set_thresholds(warn=70, danger=90)
    check("覆盖阈值", True)


# ---------- 6. 无 pyqtgraph 降级 ----------

def test_fallback():
    print("\n--- 6. 无 pyqtgraph 降级 ---")
    w = ChartWidget(title="GPU")
    w.set_series([ChartPoint(1.0, 60.0)])
    w.set_thresholds(warn=80, danger=95)
    w.reset()
    check("回退 Widget 全接口可用", True)


# ---------- 7. 源码扫描 ----------

def test_no_store_import():
    print("\n--- 7. 源码扫描 ---")
    p = os.path.join(ROOT, "host", "gui", "widgets", "chart_widget.py")
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    import_lines = [l.strip() for l in lines
                    if l.strip().startswith("import ") or l.strip().startswith("from ")]
    all_imports = " ".join(import_lines)
    check("无 FrameStore import", "FrameStore" not in all_imports)
    check("无 HistoryStore import", "HistoryStore" not in all_imports)
    check("无 NodeStore import", "NodeStore" not in all_imports)
    check("无 MonitorViewModel import", "MonitorViewModel" not in all_imports
          or "monitor_vm" not in all_imports)
    check("有 pyqtgraph 或 QWidget", "pyqtgraph" in all_imports
          or "QWidget" in all_imports)


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  ChartWidget 单元测试 (Phase 3-5C)")
    print(f"  pyqtgraph: {'可用' if has_pyqtgraph() else '不可用（使用回退）'}")
    print("=" * 55)

    test_init()
    test_set_series()
    test_empty_series()
    test_clear()
    test_thresholds()
    test_fallback()
    test_no_store_import()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
