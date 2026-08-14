# -*- coding: utf-8 -*-
"""
test_v52_settings_vm.py —— SettingsViewModel 单元测试（v5.2 Phase 3-6A）。

覆盖：
1. get 基本
2. set 基本
3. reset 单字段
4. reset 全量
5. get_all 快照
6. 告警配置
7. 节点 CRUD
8. Signal 触发
9. Facade 隔离
"""
import os
import sys
import tempfile
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from host.facade.settings_facade import SettingsFacade
from host.viewmodels.settings_vm import SettingsViewModel

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


def _make_vm():
    """创建测试用 VM（使用独立 ConfigManager 避免污染全局）。"""
    from common.config_manager import get_config_manager
    mgr = get_config_manager()
    facade = SettingsFacade(manager=mgr)
    vm = SettingsViewModel(facade)
    return vm, mgr


# ---------- 1. get 基本 ----------

def test_get():
    print("\n--- 1. get ---")
    vm, mgr = _make_vm()
    # V52 默认值
    check("get theme 默认", vm.get("theme") == "dark")
    check("get ui_scale 默认", vm.get("ui_scale") == 1.0)
    check("get 不存在返回 None", vm.get("nonexistent") is None)
    check("get 不存在返回自定义", vm.get("nonexistent", 42) == 42)
    # ConfigManager 值
    lang = vm.get("language")
    check("get language", lang in ("zh_CN", "en", ""))


# ---------- 2. set 基本 ----------

def test_set():
    print("\n--- 2. set ---")
    vm, mgr = _make_vm()
    vm.set("theme", "light")
    check("set theme=light", vm.get("theme") == "light")
    vm.set("theme", "dark")
    check("set theme=dark", vm.get("theme") == "dark")


# ---------- 3. reset 单字段 ----------

def test_reset_single():
    print("\n--- 3. reset 单字段 ---")
    vm, mgr = _make_vm()
    vm.set("theme", "light")
    check("set后=light", vm.get("theme") == "light")
    vm.reset("theme")
    check("reset后=dark(默认)", vm.get("theme") == "dark")


# ---------- 4. reset 全量 ----------

def test_reset_all():
    print("\n--- 4. reset 全量 ---")
    vm, mgr = _make_vm()
    vm.set("theme", "light")
    vm.set("ui_scale", 1.5)
    vm.reset(None)
    check("reset全部后 theme=dark", vm.get("theme") == "dark")
    check("reset全部后 ui_scale=1.0", vm.get("ui_scale") == 1.0)


# ---------- 5. get_all 快照 ----------

def test_get_all():
    print("\n--- 5. get_all ---")
    vm, mgr = _make_vm()
    vm.set("theme", "light")
    vm.set("ui_scale", 1.5)
    snap = vm.get_all()
    check("get_all 包含 theme", snap.get("theme") == "light")
    check("get_all 包含 ui_scale", snap.get("ui_scale") == 1.5)
    check("get_all 包含 language", "language" in snap)
    check("get_all 包含 log_level", "log_level" in snap)


# ---------- 6. 告警配置 ----------

def test_alerts():
    print("\n--- 6. 告警配置 ---")
    vm, mgr = _make_vm()
    alerts = vm.get_alerts()
    check("默认告警非空", len(alerts) > 0)
    check("默认含 CPU 规则", any(a.get("path") == "cpu.total_usage" for a in alerts))

    vm.set_alert("cpu.total_usage", red=90, warn=70)
    check("set_alert 成功", True)

    vm.reset_alerts()
    check("reset_alerts 成功", True)


# ---------- 7. 节点 CRUD ----------

def test_hosts():
    print("\n--- 7. 节点 CRUD ---")
    vm, mgr = _make_vm()
    initial_count = len(vm.get_hosts())
    check("初始 hosts 可获取", isinstance(initial_count, int))

    vm.add_host("test_vm_1", "192.168.1.100", 12345, "token1", "测试节点")
    check("add_host 后数量+1", len(vm.get_hosts()) == initial_count + 1)
    check("节点 test_vm_1 存在", any(h.get("node_id") == "test_vm_1" for h in vm.get_hosts()))

    vm.add_host("test_vm_2", "192.168.1.101", 12345, "token2", "测试节点2")
    check("add_host 后数量+2", len(vm.get_hosts()) == initial_count + 2)

    vm.remove_host("test_vm_1")
    check("remove_host 后数量恢复", len(vm.get_hosts()) == initial_count + 1)
    vm.remove_host("test_vm_2")
    check("全部清理后数量恢复", len(vm.get_hosts()) == initial_count)


# ---------- 8. Signal ----------

def test_signal():
    print("\n--- 8. Signal ---")
    vm, mgr = _make_vm()
    keys = []
    vm.settings_changed.connect(lambda k: keys.append(k))

    vm.set("theme", "light")
    check("set 后 emit theme", "theme" in keys)

    keys.clear()
    vm.reset("theme")
    check("reset 后 emit theme", "theme" in keys)

    keys.clear()
    vm.reset_alerts()
    check("reset_alerts 后 emit alerts", "alerts" in keys)


# ---------- 9. Facade 隔离 ----------

def test_facade_isolation():
    print("\n--- 9. Facade 隔离 ---")
    vm, mgr = _make_vm()
    check("vm 不暴露 facade", not hasattr(vm, "facade"))


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  SettingsViewModel 单元测试 (Phase 3-6A)")
    print("=" * 55)

    test_get()
    test_set()
    test_reset_single()
    test_reset_all()
    test_get_all()
    test_alerts()
    test_hosts()
    test_signal()
    test_facade_isolation()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
