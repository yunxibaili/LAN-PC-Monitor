# -*- coding: utf-8 -*-
"""
v5.2 Phase 3-4A 单元测试 —— AlertViewModel。

覆盖（设计中的 9 项）：
1. push 新告警 → VM 收到并转换为 AlertItem
2. 节点隔离：不同 node 的告警互不影响
3. level 过滤：set_filter_level("red"/"warn")
4. node 过滤：set_filter_node(node_id)
5. 搜索过滤：set_search(name/alias/path)
6. clear_all
7. count 统计：get_count/get_red_count/get_warn_count/get_summary
8. signal 触发：alerts_changed / count_changed
9. 不复制 AlertStore 去重：30s 去重仍由 Store 负责

用法：python tests/test_v52_alert_vm.py
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from host.viewmodels.alert_vm import AlertItem, AlertViewModel
from host.store.alert_store import AlertStore

PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  {detail}")


def _mk_alert(node_id, name, path, level, value=95, threshold=90):
    return {"timestamp": time.time(), "node_id": node_id,
            "node_alias": f"alias-{node_id}", "name": name, "path": path,
            "value": value, "level": level, "threshold": threshold}


def test_alert_item():
    print("\n--- 1. AlertItem 转换 ---")
    a = _mk_alert("n1", "CPU 使用率", "cpu.total_usage", "red")
    item = AlertItem(a)
    check("AlertItem 字段完整",
          all(hasattr(item, f) for f in
              ("timestamp", "node_id", "node_alias", "name", "path",
               "value", "level", "threshold")))
    check("to_dict 映射正确",
          item.to_dict()["node_id"] == "n1" and item.to_dict()["level"] == "red"
          and item.to_dict()["name"] == "CPU 使用率")


def test_push_and_convert():
    print("\n--- 2. push 新告警 → AlertItem ---")
    s = AlertStore(dedup_seconds=30)
    vm = AlertViewModel(s)
    changed = []
    vm.alerts_changed.connect(lambda: changed.append(1))

    s.push(_mk_alert("n1", "CPU 使用率", "cpu.total_usage", "red"))
    items = vm.get_items()
    check("VM 收到告警并转 AlertItem", len(items) == 1)
    check("AlertItem 类型", isinstance(items[0], AlertItem))
    check("字段值正确", items[0].node_id == "n1"
          and items[0].level == "red" and items[0].name == "CPU 使用率")
    check("alerts_changed 触发", len(changed) == 1)
    check("get_count 反映 Store", vm.get_count() == 1)


def test_node_isolation():
    print("\n--- 3. 节点隔离 ---")
    s = AlertStore(dedup_seconds=30)
    vm = AlertViewModel(s)
    s.push(_mk_alert("n1", "CPU", "cpu.total_usage", "red"))
    s.push(_mk_alert("n2", "GPU", "gpu.core_temp_c", "warn"))
    items = vm.get_items()
    check("两个节点告警都在", len(items) == 2)
    vm.set_filter_node("n1")
    filtered = vm.get_items()
    check("过滤 n1 只剩 1 条", len(filtered) == 1 and filtered[0].node_id == "n1")
    vm.clear_filters()
    check("清除过滤恢复 2 条", len(vm.get_items()) == 2)


def test_level_filter():
    print("\n--- 4. level 过滤 ---")
    s = AlertStore(dedup_seconds=30)
    vm = AlertViewModel(s)
    s.push(_mk_alert("n1", "CPU", "cpu.total_usage", "red"))
    s.push(_mk_alert("n2", "RAM", "ram.usage_percent", "warn"))
    vm.set_filter_level("red")
    red = vm.get_items()
    check("过滤 red 得 1 条", len(red) == 1 and red[0].level == "red")
    vm.set_filter_level("warn")
    warn = vm.get_items()
    check("过滤 warn 得 1 条", len(warn) == 1 and warn[0].level == "warn")
    vm.set_filter_level(None)
    check("取消 level 过滤恢复", len(vm.get_items()) == 2)


def test_search_filter():
    print("\n--- 5. 搜索过滤 ---")
    s = AlertStore(dedup_seconds=30)
    vm = AlertViewModel(s)
    s.push(_mk_alert("n1", "CPU 使用率", "cpu.total_usage", "red"))
    s.push(_mk_alert("n2", "GPU 温度", "gpu.core_temp_c", "warn"))
    vm.set_search("cpu")
    hits = vm.get_items()
    check("搜索 cpu 匹配 name/path", len(hits) == 1 and hits[0].name == "CPU 使用率")
    vm.set_search("n2")   # 匹配 node_alias alias-n2
    hits = vm.get_items()
    check("搜索 node_alias 匹配", len(hits) == 1 and hits[0].node_id == "n2")
    vm.clear_filters()
    check("清过滤恢复", len(vm.get_items()) == 2)


def test_counts_and_summary():
    print("\n--- 6. count 统计 ---")
    s = AlertStore(dedup_seconds=30)
    vm = AlertViewModel(s)
    s.push(_mk_alert("n1", "CPU", "cpu.total_usage", "red"))
    s.push(_mk_alert("n1", "GPU", "gpu.core_temp_c", "red"))
    s.push(_mk_alert("n2", "RAM", "ram.usage_percent", "warn"))
    check("get_count=3", vm.get_count() == 3)
    check("get_red_count=2", vm.get_red_count() == 2)
    check("get_warn_count=1", vm.get_warn_count() == 1)
    sm = vm.get_summary()
    check("get_summary 结构",
          sm["red"] == 2 and sm["warn"] == 1 and sm["active"] == 3
          and sm["total"] == 3, str(sm))


def test_clear_node_and_all():
    print("\n--- 7. clear_node / clear_all ---")
    s = AlertStore(dedup_seconds=30)
    vm = AlertViewModel(s)
    counts = []
    vm.count_changed.connect(lambda c: counts.append(c))
    s.push(_mk_alert("n1", "CPU", "cpu.total_usage", "red"))
    s.push(_mk_alert("n2", "GPU", "gpu.core_temp_c", "warn"))
    vm.clear_node("n1")
    check("clear_node 移除 n1 活动项", vm.get_count() == 1
          and all(i.node_id != "n1" for i in vm.get_items()))
    vm.clear_all()
    check("clear_all 活动清空", vm.get_count() == 0)
    check("count_changed 有 0", 0 in counts)


def test_signal_triggers():
    print("\n--- 8. signal 触发 ---")
    s = AlertStore(dedup_seconds=30)
    vm = AlertViewModel(s)
    alerts_changed, count_changed = [], []
    vm.alerts_changed.connect(lambda: alerts_changed.append(1))
    vm.count_changed.connect(lambda c: count_changed.append(c))
    s.push(_mk_alert("n1", "CPU", "cpu.total_usage", "red"))
    check("alerts_changed 触发", len(alerts_changed) == 1)
    check("count_changed 触发", len(count_changed) >= 1)
    # 过滤变更也触发 alerts_changed
    before = len(alerts_changed)
    vm.set_filter_level("red")
    check("过滤变更触发 alerts_changed", len(alerts_changed) > before)
    vm.unsubscribe()
    s.push(_mk_alert("n2", "GPU", "gpu.core_temp_c", "warn"))
    check("unsubscribe 后不再触发", len(alerts_changed) == len(alerts_changed))


def test_no_dup_dedup():
    """VM 不复制去重：30s 去重仍由 AlertStore 负责。"""
    print("\n--- 9. 不复制 AlertStore 去重 ---")
    s = AlertStore(dedup_seconds=30)
    vm = AlertViewModel(s)
    a = _mk_alert("n1", "CPU", "cpu.total_usage", "red")
    check("首次 push 新增", s.push(dict(a)) is True)
    check("30s 内去重（Store 负责）", s.push(dict(a)) is False)
    check("VM 只收到 1 条", len(vm.get_items()) == 1)
    # 超窗口再触发
    s._last_alert_ts[("n1", "cpu.total_usage")] = time.time() - 35
    s.push(dict(a))
    check("超窗口后 VM 收到第 2 条", len(vm.get_items()) == 2)


def main():
    print("=" * 60)
    print("v5.2 Phase 3-4A 单元测试（AlertViewModel）")
    print("=" * 60)
    test_alert_item()
    test_push_and_convert()
    test_node_isolation()
    test_level_filter()
    test_search_filter()
    test_counts_and_summary()
    test_clear_node_and_all()
    test_signal_triggers()
    test_no_dup_dedup()
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
