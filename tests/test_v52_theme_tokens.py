# -*- coding: utf-8 -*-
"""
test_v52_theme_tokens.py —— Theme Token 一致性测试（v5.2 RC-7C）。

验证：
1. 单来源：colors.py 基础 token 不含独立 hex
2. 引用方向：common → host = 0
3. Token 完整性：必须存在的 key 全部存在
4. 值一致性：theme_tokens.XXX == colors.XXX
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

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


# ---------- 1. 单来源检查 ----------

def test_single_source():
    print("\n--- 1. 单来源检查 ---")
    # colors.py 基础 token 应引用 ThemeTokens，不应用独立 hex
    # 注意：colors.py 已迁移至 common/gui/theme/colors.py
    p = os.path.join(ROOT, "common", "gui", "theme", "colors.py")
    with open(p, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_base_section = False
    violations = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if "基础 token" in stripped:
            in_base_section = True
            continue
        if "语义 token" in stripped:
            in_base_section = False
            continue
        if in_base_section and stripped.startswith("#"):
            continue
        if in_base_section and "ThemeTokens." in stripped:
            continue
        if in_base_section and stripped and not stripped.startswith("class ") and not stripped.startswith('"""'):
            # 在基础 token 区域但不是 ThemeTokens 引用
            if "=" in stripped and "#" in stripped:
                violations.append(f"L{i}: {stripped[:60]}")

    check("基础 token 无独立 hex", len(violations) == 0, str(violations[:3]))

    # 语义 token 可以有 hex
    in_semantic = False
    semantic_count = 0
    for line in lines:
        stripped = line.strip()
        if "语义 token" in stripped:
            in_semantic = True
            continue
        if in_semantic and "=" in stripped and "#" in stripped:
            semantic_count += 1
    check("语义 token 保留 hex", semantic_count > 0, f"found {semantic_count}")


# ---------- 2. 引用方向 ----------

def test_import_direction():
    print("\n--- 2. 引用方向 ---")
    # common 不应 import host
    for root_dir, dirs, files in os.walk(os.path.join(ROOT, "common")):
        if "__pycache__" in root_dir:
            continue
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
                if "import host" in stripped or "from host" in stripped:
                    rel = p.replace(ROOT + os.sep, "")
                    check(f"common 无 host import", False, f"{rel}:{i}: {stripped[:60]}")
                    return
    check("common 无 host import", True)


# ---------- 3. Token 完整性 ----------

def test_token_completeness():
    print("\n--- 3. Token 完整性 ---")
    import common.theme_tokens as tt

    required_colors = [
        "COLOR_BG_DARK", "COLOR_BG_SURFACE", "COLOR_BG_CARD",
        "COLOR_TEXT_PRIMARY", "COLOR_TEXT_SECONDARY", "COLOR_TEXT_DISABLED",
        "COLOR_ACCENT", "COLOR_SUCCESS", "COLOR_WARNING", "COLOR_DANGER",
        "COLOR_INFO", "COLOR_BORDER",
    ]
    for name in required_colors:
        check(f"theme_tokens.{name}", hasattr(tt, name))

    required_spacing = ["SPACING_XS", "SPACING_SM", "SPACING_MD", "SPACING_LG", "SPACING_XL", "SPACING_XXL"]
    for name in required_spacing:
        check(f"theme_tokens.{name}", hasattr(tt, name))

    required_font = ["FONT_FAMILY", "FONT_SIZE_TITLE_LG", "FONT_SIZE_BODY"]
    for name in required_font:
        check(f"theme_tokens.{name}", hasattr(tt, name))


# ---------- 4. 值一致性 ----------

def test_value_consistency():
    print("\n--- 4. 值一致性 ---")
    import common.theme_tokens as tt
    from common.gui.theme.colors import ThemeColors as TC
    from host.gui.theme.spacing import ThemeSpacing as S

    pairs = [
        (tt.COLOR_BG_DARK, TC.BACKGROUND_PRIMARY, "BG_DARK → BACKGROUND_PRIMARY"),
        (tt.COLOR_BG_SURFACE, TC.BACKGROUND_SECONDARY, "BG_SURFACE → BACKGROUND_SECONDARY"),
        (tt.COLOR_BG_CARD, TC.BACKGROUND_CARD, "BG_CARD → BACKGROUND_CARD"),
        (tt.COLOR_TEXT_PRIMARY, TC.TEXT_PRIMARY, "TEXT_PRIMARY"),
        (tt.COLOR_TEXT_SECONDARY, TC.TEXT_SECONDARY, "TEXT_SECONDARY"),
        (tt.COLOR_TEXT_DISABLED, TC.TEXT_DISABLED, "TEXT_DISABLED"),
        (tt.COLOR_ACCENT, TC.ACCENT_PRIMARY, "ACCENT"),
        (tt.COLOR_SUCCESS, TC.STATUS_ONLINE, "SUCCESS → STATUS_ONLINE"),
        (tt.COLOR_WARNING, TC.STATUS_WARNING, "WARNING"),
        (tt.COLOR_DANGER, TC.STATUS_ERROR, "DANGER → STATUS_ERROR"),
        (tt.COLOR_INFO, TC.ALERT_INFO, "INFO → ALERT_INFO"),
        (tt.COLOR_BORDER, TC.BORDER_DEFAULT, "BORDER"),
    ]
    for token_val, tc_val, desc in pairs:
        check(f"值一致: {desc}", token_val == tc_val,
              f"theme_tokens={token_val} vs TC={tc_val}")

    # spacing
    check("SPACING_SM == S.SM", tt.SPACING_SM == S.SM)
    check("SPACING_LG == S.LG", tt.SPACING_LG == S.LG)


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  Theme Token 一致性测试 (RC-7C)")
    print("=" * 55)

    test_single_source()
    test_import_direction()
    test_token_completeness()
    test_value_consistency()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
