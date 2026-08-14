# -*- coding: utf-8 -*-
"""
test_v52_settings_flow.py —— Settings 保存流程测试（v5.2 Phase 4-6C）。

职责：
  只测 SettingsVM → FakeFacade → save() 行为。
  不测 UI，不测 ConfigManager，不测 JSON 写盘。

核心验证：
  1. set() 不写盘，save() 才提交
  2. 多次 save() 每次都写盘
  3. save 后 dirty 清除
  4. reset 不触发 save
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

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


class FakeSettingsFacade:
    """Fake Facade：记录 save 调用次数，不写盘。"""

    def __init__(self):
        self.save_count = 0
        self._data = {}
        self._alerts = []

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value

    def save(self):
        self.save_count += 1

    def get_alerts(self):
        return list(self._alerts)

    def set_alert(self, path, **kwargs):
        pass

    def get_hosts(self):
        return []

    def add_host(self, *a, **kw):
        pass

    def remove_host(self, *a):
        pass

    def reset(self, key=None):
        if key:
            self._data.pop(key, None)
        else:
            self._data.clear()


# ---------- Case 1: 批量修改后一次保存 ----------

def test_batch_save():
    print("\n--- 1. 批量修改后一次保存 ---")
    facade = FakeSettingsFacade()
    vm = SettingsViewModel(facade)

    vm.set("host", "value1")
    vm.set("port", 8080)
    vm.set("theme", "dark")

    check("set 不写盘", facade.save_count == 0)
    check("值已写入内存", vm.get("host") == "value1")
    check("port 内存", vm.get("port") == 8080)

    vm.save()
    check("save_count == 1", facade.save_count == 1)


# ---------- Case 2: 重复 save ----------

def test_double_save():
    print("\n--- 2. 重复 save ---")
    facade = FakeSettingsFacade()
    vm = SettingsViewModel(facade)

    vm.set("x", 1)
    vm.save()
    vm.save()

    check("save_count == 2", facade.save_count == 2)


# ---------- Case 3: save 后 dirty 清除 ----------

def test_dirty_lifecycle():
    print("\n--- 3. Dirty 生命周期 ---")
    facade = FakeSettingsFacade()
    vm = SettingsViewModel(facade)

    vm.set("a", 1)
    check("set 后 dirty", vm.is_dirty())

    vm.save()
    check("save 后 clean", not vm.is_dirty())

    vm.set("b", 2)
    check("再次 dirty", vm.is_dirty())
    vm.save()
    check("再次 clean", not vm.is_dirty())


# ---------- Case 4: reset 不触发 save ----------

def test_reset_no_save():
    print("\n--- 4. reset 不触发 save ---")
    facade = FakeSettingsFacade()
    vm = SettingsViewModel(facade)

    vm.set("theme", "light")
    vm.save()
    check("初始 save_count == 1", facade.save_count == 1)

    vm.reset("theme")
    check("reset 后 dirty", vm.is_dirty())
    check("reset 不写盘", facade.save_count == 1)
    check("reset 后值恢复", vm.get("theme") is None)


# ---------- Case 5: add_host / remove_host dirty ----------

def test_host_dirty():
    print("\n--- 5. add_host / remove_host dirty ---")
    facade = FakeSettingsFacade()
    vm = SettingsViewModel(facade)

    vm.save()
    check("初始 clean", not vm.is_dirty())

    vm.add_host("A", "1.2.3.4", 12345, "tok", "NodeA")
    check("add_host 后 dirty", vm.is_dirty())

    vm.save()
    check("save 后 clean", not vm.is_dirty())

    vm.remove_host("A")
    check("remove_host 后 dirty", vm.is_dirty())


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  Settings Flow Test (Phase 4-6C)")
    print("=" * 55)

    test_batch_save()
    test_double_save()
    test_dirty_lifecycle()
    test_reset_no_save()
    test_host_dirty()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
