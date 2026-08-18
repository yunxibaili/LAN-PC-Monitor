# -*- coding: utf-8 -*-
"""
test_v52_settings_page.py —— SettingsPage v5.2 Phase 4-6B 测试。

验证：
1. 页面结构（Sidebar + 5 sections）
2. VM 注入
3. 数据加载/保存
4. Dirty state
5. Save feedback
6. 架构扫描（无 ConfigManager / Facade import）
7. Theme 扫描
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

from host.facade.settings_facade import SettingsFacade
from host.viewmodels.settings_vm import SettingsViewModel
from host.gui.pages.settings_page import SettingsPage

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
    from common.config_manager import get_config_manager
    mgr = get_config_manager()
    facade = SettingsFacade(manager=mgr)
    vm = SettingsViewModel(facade)
    page = SettingsPage()
    page.set_view_model(vm)
    return vm, page


# ---------- 1. 页面结构 ----------

def test_structure():
    print("\n--- 1. 页面结构 ---")
    vm, page = _make()
    check("has sidebar", hasattr(page, '_sidebar_items'))
    check("5 sections", len(page._sidebar_items) == 5)
    check("has stack", hasattr(page, '_stack'))
    check("has save_btn", hasattr(page, '_save_btn'))
    check("save 初始禁用", not page._save_btn.isEnabled())


# ---------- 2. VM 注入 ----------

def test_vm_injection():
    print("\n--- 2. VM 注入 ---")
    vm, page = _make()
    check("vm 已注入", page._vm is vm)
    check("无 facade 属性", not hasattr(page, 'facade'))


# ---------- 3. 数据加载 ----------

def test_load():
    print("\n--- 3. 数据加载 ---")
    vm, page = _make()
    page.on_show()
    check("加载后 scale 有值", page._scale_spin.value() > 0)
    check("加载后 udp 有值", page._udp_spin.value() > 0)
    check("加载后 log_level 有值", page._log_combo.currentIndex() >= 0)


# ---------- 4. Dirty state ----------

def test_dirty():
    print("\n--- 4. Dirty state ---")
    vm, page = _make()
    page.on_show()
    check("初始 clean", not vm.is_dirty())
    check("save 禁用", not page._save_btn.isEnabled())

    page._scale_spin.setValue(1.5)
    check("修改后 dirty", vm.is_dirty())
    check("save 启用", page._save_btn.isEnabled())
    check("dirty 提示", "Unsaved" in page._dirty_lbl.text())


# ---------- 5. 保存 ----------

def test_save():
    print("\n--- 5. 保存 ---")
    vm, page = _make()
    page.on_show()

    page._scale_spin.setValue(1.5)
    page._on_save()
    check("保存后 clean", not vm.is_dirty())
    check("save 禁用", not page._save_btn.isEnabled())
    check("值已持久化", vm.get("ui_scale") == 1.5)

    # 恢复
    page._scale_spin.setValue(1.0)
    page._on_save()


# ---------- 6. Section 切换 ----------

def test_section_switch():
    print("\n--- 6. Section 切换 ---")
    vm, page = _make()
    page.on_show()

    page._switch_section("Alerts")
    check("切换到 Alerts", page._stack.currentWidget() == page._section_widgets["Alerts"])

    page._switch_section("General")
    check("切换到 General", page._stack.currentWidget() == page._section_widgets["General"])


# ---------- 7. 架构扫描 ----------

def test_no_store_import():
    print("\n--- 7. 架构扫描 ---")
    p = os.path.join(ROOT, "host", "gui", "pages", "settings_page.py")
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    import_lines = [l.strip() for l in lines
                    if l.strip().startswith("import ") or l.strip().startswith("from ")]
    all_imports = " ".join(import_lines)
    check("无 import ConfigManager", "ConfigManager" not in all_imports)
    check("无 import SettingsFacade", "SettingsFacade" not in all_imports)
    check("无 import FrameStore", "FrameStore" not in all_imports)
    check("有 set_view_model", hasattr(SettingsPage, 'set_view_model'))


# ---------- 8. Theme 扫描 ----------

def test_no_hardcoded_colors():
    print("\n--- 8. Theme 扫描 ---")
    import re
    p = os.path.join(ROOT, "host", "gui", "pages", "settings_page.py")
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    violations = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("import") or stripped.startswith("from "):
            continue
        for m in re.finditer(r'#[0-9a-fA-F]{3,8}', stripped):
            violations.append(f"L{i}: {m.group(0)}")
    check("无硬编码颜色", len(violations) == 0, str(violations[:3]))


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  SettingsPage v5.2 Phase 4-6B 测试")
    print("=" * 55)

    test_structure()
    test_vm_injection()
    test_load()
    test_dirty()
    test_save()
    test_section_switch()
    test_no_store_import()
    test_no_hardcoded_colors()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
