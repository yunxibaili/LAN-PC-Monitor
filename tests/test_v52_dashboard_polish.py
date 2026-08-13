# -*- coding: utf-8 -*-
"""
test_v52_dashboard_polish.py —— Dashboard Visual Polish 验证测试（v5.2 Phase 4-2C）。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt5.QtWidgets import QApplication
import sys as _sys
if not _sys.argv:
    _sys.argv = ["test"]
_app = QApplication.instance() or QApplication(_sys.argv)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.widgets.node_card import NodeCard
from host.gui.pages.dashboard_page import DashboardPage

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


# ---------- 1. NodeCard hover ----------

def test_node_card_hover():
    print("\n--- 1. NodeCard hover 样式 ---")
    card = NodeCard("test", alias="Test")
    style = card.styleSheet()
    check("hover 样式存在", "NodeCard:hover" in style)
    check("圆角 12px", "12px" in style)
    check("使用 ThemeColors", "BORDER_DEFAULT" in style or TC.BORDER_DEFAULT in style)


# ---------- 2. NodeCard 环形进度 ----------

def test_node_card_rings():
    print("\n--- 2. NodeCard 环形进度 ---")
    card = NodeCard("test", alias="Test")
    check("有 3 个环形", len(card._ring_labels) == 3)
    check("有 CPU 环形", "cpu" in card._ring_labels)
    check("有 GPU 环形", "gpu" in card._ring_labels)
    check("有 RAM 环形", "ram" in card._ring_labels)


# ---------- 3. NodeCard 底部指标 ----------

def test_node_card_bottom():
    print("\n--- 3. NodeCard 底部指标 ---")
    card = NodeCard("test", alias="Test")
    check("有 FPS 标签", hasattr(card, '_fps_lbl'))
    check("有 Temp 标签", hasattr(card, '_temp_lbl'))
    check("有 Net 标签", hasattr(card, '_net_lbl'))
    check("有 Score 标签", hasattr(card, '_score_lbl'))


# ---------- 4. Theme 引用 ----------

def test_theme_refs():
    print("\n--- 4. Theme 引用 ---")
    p = os.path.join(ROOT, "host", "gui", "widgets", "node_card.py")
    with open(p, "r", encoding="utf-8") as f:
        lines = f.readlines()
    violations = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("import") or stripped.startswith("from "):
            continue
        for m in re.finditer(r'"(#[0-9a-fA-F]{6})"', stripped):
            violations.append(f"L{i}: {m.group(1)}")
    check("NodeCard 无硬编码颜色", len(violations) == 0, str(violations[:3]))


# ---------- 5. DashboardPage theme ----------

def test_dashboard_theme():
    print("\n--- 5. DashboardPage theme ---")
    p = os.path.join(ROOT, "host", "gui", "pages", "dashboard_page.py")
    with open(p, "r", encoding="utf-8") as f:
        lines = f.readlines()
    violations = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("import") or stripped.startswith("from "):
            continue
        for m in re.finditer(r'"(#[0-9a-fA-F]{6})"', stripped):
            violations.append(f"L{i}: {m.group(1)}")
    check("DashboardPage 无硬编码颜色", len(violations) == 0, str(violations[:3]))


# ---------- 6. 无业务依赖 ----------

def test_no_business_deps():
    print("\n--- 6. 无业务依赖 ---")
    p = os.path.join(ROOT, "host", "gui", "widgets", "node_card.py")
    with open(p, "r", encoding="utf-8") as f:
        source = f.read()
    check("无 import FrameStore", "FrameStore" not in source)
    check("无 import NodeStore", "NodeStore" not in source)
    check("无 import NodeConnection", "NodeConnection" not in source)


# ---------- 7. Widget 结构 ----------

def test_widget_structure():
    print("\n--- 7. Widget 结构 ---")
    card = NodeCard("A", alias="NodeA")
    check("NodeCard 创建", card is not None)
    check("setFixedSize", hasattr(card, 'setFixedSize'))
    check("clicked signal", hasattr(card, 'clicked'))
    check("update_data", hasattr(card, 'update_data'))


def main():
    global PASS, FAIL
    print("=" * 50)
    print("  Dashboard Visual Polish (Phase 4-2C)")
    print("=" * 50)

    test_node_card_hover()
    test_node_card_rings()
    test_node_card_bottom()
    test_theme_refs()
    test_dashboard_theme()
    test_no_business_deps()
    test_widget_structure()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
