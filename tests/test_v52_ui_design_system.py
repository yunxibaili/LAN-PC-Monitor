# -*- coding: utf-8 -*-
"""
test_v52_ui_design_system.py —— Design System 验证测试（v5.2 Phase 4-1B）。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.theme.layout import ThemeLayout as L
from host.gui.theme.animation import ThemeAnimation as A
from host.gui.theme.typography import ThemeTypography
from host.gui.theme.components import remove_help_button
from host.gui.theme.icons import ThemeIcons

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


# ---------- 1. ThemeColors 完整性 ----------

def test_theme_colors():
    print("\n--- 1. ThemeColors 完整性 ---")
    required = [
        "BACKGROUND_PRIMARY", "BACKGROUND_SECONDARY", "BACKGROUND_CARD",
        "TEXT_PRIMARY", "TEXT_SECONDARY", "TEXT_DISABLED",
        "ACCENT_PRIMARY",
        "STATUS_ONLINE", "STATUS_OFFLINE", "STATUS_WARNING", "STATUS_ERROR",
        "ALERT_INFO", "ALERT_WARN", "ALERT_DANGER",
    ]
    for attr in required:
        check(f"{attr} defined", hasattr(TC, attr))
    check("bar_color()", callable(getattr(TC, 'bar_color', None)))
    check("score_color()", callable(getattr(TC, 'score_color', None)))
    check("status_color()", callable(getattr(TC, 'status_color', None)))
    check("alert_color()", callable(getattr(TC, 'alert_color', None)))


# ---------- 2. ThemeSpacing ----------

def test_spacing():
    print("\n--- 2. ThemeSpacing ---")
    check("XS=4", S.XS == 4)
    check("SM=8", S.SM == 8)
    check("MD=12", S.MD == 12)
    check("LG=16", S.LG == 16)
    check("XL=24", S.XL == 24)
    check("XXL=32", S.XXL == 32)


# ---------- 3. ThemeLayout ----------

def test_layout():
    print("\n--- 3. ThemeLayout ---")
    check("SIDEBAR_WIDTH=220", L.SIDEBAR_WIDTH == 220)
    check("PAGE_PADDING=24", L.PAGE_PADDING == 24)
    check("CARD_GAP=16", L.CARD_GAP == 16)
    check("HEADER_HEIGHT=64", L.HEADER_HEIGHT == 64)


# ---------- 4. ThemeAnimation ----------

def test_animation():
    print("\n--- 4. ThemeAnimation ---")
    check("FAST=120", A.FAST == 120)
    check("NORMAL=200", A.NORMAL == 200)
    check("SLOW=300", A.SLOW == 300)


# ---------- 5. ThemeTypography ----------

def test_typography():
    print("\n--- 5. ThemeTypography ---")
    check("TITLE_LARGE size", ThemeTypography.TITLE_LARGE["size"] == 24)
    check("BODY size", ThemeTypography.BODY["size"] == 14)
    check("CAPTION size", ThemeTypography.CAPTION["size"] == 11)
    css = ThemeTypography.css(ThemeTypography.TITLE_LARGE)
    check("css contains bold", "bold" in css)
    check("css contains 24px", "24px" in css)


# ---------- 6. Components ----------

def test_components():
    print("\n--- 6. Components ---")
    check("remove_help_button 可导入", callable(remove_help_button))


# ---------- 7. 无硬编码颜色 ----------

def test_no_hardcoded_colors():
    print("\n--- 7. 无硬编码颜色 ---")
    violations = []
    tc_colors = {}
    with open('host/gui/theme/colors.py', 'r', encoding='utf-8') as f:
        for line in f:
            m = re.match(r'\s+(\w+)\s*=\s*"([^"]+)"', line)
            if m:
                tc_colors[m.group(2)] = m.group(1)

    for root, _, fs in os.walk('host/gui'):
        if '__pycache__' in root or 'theme' in root:
            continue
        for f in fs:
            if not f.endswith('.py'):
                continue
            p = os.path.join(root, f)
            txt = open(p, 'r', encoding='utf-8', errors='ignore').read()
            for i, line in enumerate(txt.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('import') or stripped.startswith('from '):
                    continue
                for m in re.finditer(r'#[0-9a-fA-F]{3,8}', stripped):
                    c = m.group(0)
                    if 'ThemeColors' in stripped and c in stripped:
                        continue
                    violations.append(f"{os.path.basename(p)}:{i}")

    check("无硬编码颜色", len(violations) == 0, str(violations[:5]))


# ---------- 8. 无重复 QSS ----------

def test_no_inline_qss():
    print("\n--- 8. QSS 可控性 ---")
    # 统计 theme/ 外的 setStyleSheet 数量
    count = 0
    for root, _, fs in os.walk('host/gui'):
        if '__pycache__' in root:
            continue
        for f in fs:
            if not f.endswith('.py'):
                continue
            p = os.path.join(root, f)
            txt = open(p, 'r', encoding='utf-8', errors='ignore').read()
            for line in txt.splitlines():
                if 'setStyleSheet' in line and not line.strip().startswith('#'):
                    count += 1
    check("setStyleSheet 数量可控 (<220)", count < 220, f"{count} 处")


# ---------- 9. PageHeader 使用检查 ----------

def test_page_header_usage():
    print("\n--- 9. 页面标题结构 ---")
    pages = ['dashboard_page', 'nodes_page', 'monitor_page', 'alerts_page', 'settings_page']
    for page in pages:
        p = f'host/gui/pages/{page}.py'
        if os.path.isfile(p):
            txt = open(p, 'r', encoding='utf-8', errors='ignore').read()
            # 检查是否有标题组件（PageHeader / MonitorHeader / QLabel 标题）
            has_header = ('PageHeader' in txt or 'page_header' in txt
                          or 'MonitorHeader' in txt
                          or ('QLabel' in txt and ('font-size: 20px' in txt or 'TT.TITLE_MEDIUM' in txt or 'TT.TITLE_LARGE' in txt)))
            check(f"{page} has header", has_header)


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  Design System 验证测试 (Phase 4-1B)")
    print("=" * 55)

    test_theme_colors()
    test_spacing()
    test_layout()
    test_animation()
    test_typography()
    test_components()
    test_no_hardcoded_colors()
    test_no_inline_qss()
    test_page_header_usage()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
