# -*- coding: utf-8 -*-
"""
v5.2 Phase 0 单元测试 —— host/store/ + facade/ + manager/ 基础架构。

验证：
- store/signals.py 统一 Signal 规范（Qt 回退后端 connect/emit/disconnect）
- NodeStore：增删/状态/RTT/丢包/评分/汇总 + 异常（重复节点、移除不存在）
- FrameStore：push/get/指标提取/stale + 异常（空帧、节点删除、重复节点）
- HistoryStore：push/query/maxlen/50 节点压力 + 异常（非数值跳过）
- AlertStore：push/30s 去重/计数/clear + 异常（缺字段、重复）
- SettingsFacade：包装 ConfigManager、默认值兜底、get/set
- AlertAdapter：AlertEngine → AlertStore 桥接
- TrayManager/DiscoveryService：降级安全 + 接口可用

不依赖 PyQt5（沙箱用回退信号后端）。
用法：python tests/test_v52_phase0.py
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from host.store.node_store import NodeStore
from host.store.frame_store import FrameStore
from host.store.history_store import HistoryStore
from host.store.alert_store import AlertStore
from host.store.signals import Signal, has_qt_signal

PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  {detail}")


# ---------- 1. signals ----------

def test_signals():
    print("\n--- 1. signals（统一 Signal 规范）---")
    print(f"  [INFO] Qt backend: {has_qt_signal()}")

    class Demo:
        updated = Signal(object, str)
        changed = Signal(str)
        removed = Signal(str)
        reset = Signal()

    d = Demo()
    got = []
    d.updated.connect(lambda f, n: got.append(("u", f, n)))
    d.changed.connect(lambda x: got.append(("c", x)))
    d.updated.emit({"cpu": 1}, "n1")
    d.changed.emit("ok")
    check("connect + emit 触发", got == [("u", {"cpu": 1}, "n1"), ("c", "ok")], str(got))

    d.updated.disconnect()
    d.updated.emit({}, "n2")
    check("disconnect 后不再触发",
          not any(x[0] == "u" and x[2] == "n2" for x in got))

    d.changed.disconnect()
    before = len(got)
    d.changed.emit("x")
    check("disconnect(slot) 生效", len(got) == before)


# ---------- 2. NodeStore ----------

def test_node_store():
    print("\n--- 2. NodeStore ---")
    s = NodeStore()
    added, removed, updated = [], [], []
    status_changed, metrics_updated = [], []
    s.node_added.connect(lambda n: added.append(n))
    s.node_removed.connect(lambda n: removed.append(n))
    s.node_updated.connect(lambda n: updated.append(n))
    s.status_changed.connect(lambda n, st: status_changed.append((n, st)))
    s.metrics_updated.connect(lambda n: metrics_updated.append(n))

    s.add_node("n1", alias="游戏主机", ip="192.168.1.10", port=12345)
    s.add_node("n2", alias="直播机")
    check("添加 2 节点", s.count() == 2)
    check("node_added 触发 2 次", added == ["n1", "n2"])
    check("get_alias", s.get_alias("n1") == "游戏主机")

    s.add_node("n1", alias="游戏主机改")   # 重复添加 → 更新不重复触发 add
    check("重复添加幂等（count 不变）", s.count() == 2)
    check("重复添加更新 alias", s.get_alias("n1") == "游戏主机改")

    s.update_status("n1", "connected")
    s.update_rtt("n1", 0.37)
    s.update_loss("n1", 0.0)
    sc = s.update_quality("n1", 0.37, 0.0)
    check("status_changed 触发 (n1, connected)", ("n1", "connected") in status_changed)
    check("metrics_updated 触发 ≥3 次", len(metrics_updated) >= 3, str(metrics_updated))
    check("update_quality 返回 (score, grade)", isinstance(sc, tuple) and len(sc) == 2)
    check("get_score", s.get_score("n1") is not None)
    check("get_status", s.get_status("n1") == "connected")

    s.remove_node("n1")
    check("remove 后 count=1", s.count() == 1)
    check("node_removed 触发", removed == ["n1"])
    s.remove_node("n1")   # 移除不存在 → 幂等
    check("重复移除幂等", s.count() == 1)

    # 移除不存在节点不抛异常
    s.remove_node("nonexist")
    check("移除不存在节点无异常", True)

    # summary
    s.add_node("n3")
    s.update_status("n2", "connected")
    s.update_status("n3", "offline")
    s.update_quality("n2", 1.0, 0.0)
    sm = s.summary()
    check("summary 统计", sm["total"] == 2 and sm["online"] == 1
          and sm["offline"] == 1, str(sm))


# ---------- 3. FrameStore ----------

def test_frame_store():
    print("\n--- 3. FrameStore ---")
    s = FrameStore()
    got = []
    s.frame_updated.connect(lambda n, f: got.append((n, f.get("cpu", {}).get("total_usage"))))

    frame1 = {"type": "monitor_data", "cpu": {"total_usage": 45.0},
              "ram": {"usage_percent": 50}, "system": {"uptime_seconds": 100}}
    s.push("n1", frame1, ts=100.0)
    check("push 触发 frame_updated", got == [("n1", 45.0)], str(got))
    check("get 返回帧", s.get("n1")["cpu"]["total_usage"] == 45.0)

    # 覆盖
    frame2 = {"type": "monitor_data", "cpu": {"total_usage": 60.0}}
    s.push("n1", frame2, ts=101.0)
    check("覆盖最新帧", s.get("n1")["cpu"]["total_usage"] == 60.0)
    check("count 仍 1", s.count() == 1)

    # 空帧
    s.push("n2", {})
    check("空帧接受（调用方决定跳过）", s.has("n2"))
    s.push("n3", None)   # 非 dict → 忽略
    check("非 dict 帧忽略", not s.has("n3"))

    # 指标提取
    check("get_metric cpu.total_usage", s.get_metric("n1", "cpu.total_usage") == 60.0)
    check("get_metric 缺失路径默认值", s.get_metric("n1", "gpu.usage_percent", -1) == -1)
    disk_frame = {"disk": [{"usage_percent": 80}]}
    s.push("n4", disk_frame)
    check("get_metric disk[0].usage_percent", s.get_metric("n4", "disk[0].usage_percent") == 80)

    # stale
    check("无帧节点 stale", s.is_stale("ghost", now=200.0))
    check("有新帧未超时不 stale", not s.is_stale("n1", timeout=30, now=102.0))
    check("超过 timeout stale", s.is_stale("n1", timeout=30, now=200.0))

    # 节点删除
    s.remove_node("n1")
    check("remove_node 清理帧", not s.has("n1"))


# ---------- 4. HistoryStore ----------

def test_history_store():
    print("\n--- 4. HistoryStore ---")
    s = HistoryStore(maxlen=10)
    got = []
    s.point_added.connect(lambda n, m, v: got.append((n, m, v)))

    for i in range(15):
        s.push("n1", "cpu", float(i))
    check("maxlen 限制点数", len(s.query("n1", "cpu")) == 10)
    check("保留最近 10 点", s.query("n1", "cpu")[-1][1] == 14.0)
    check("point_added 触发 15 次", len(got) == 15)

    # 非数值跳过
    s.push("n1", "cpu", "N/A")
    s.push("n1", "cpu", None)
    check("非数值点跳过", len(s.query("n1", "cpu")) == 10)

    # push_frame 批量提取
    s2 = HistoryStore(maxlen=10)
    frame = {"cpu": {"total_usage": 30}, "gpu": {"usage_percent": 50},
             "ram": {"usage_percent": 40}, "fps": {"fps": 120},
             "net_quality": {"quality_score": 95},
             "net": {"upload_mb_s": 1.0, "download_mb_s": 5.0}}
    s2.push_frame("n1", frame)
    check("push_frame 提取 7 指标", len(s2.metrics("n1")) == 7, str(s2.metrics("n1")))
    check("last cpu", s2.last("n1", "cpu") == 30.0)

    # 50 节点压力
    s3 = HistoryStore(maxlen=100)
    t0 = time.time()
    for n in range(50):
        for i in range(60):
            s3.push(f"node{n}", "cpu", float(i))
    elapsed = time.time() - t0
    check("50 节点×60 点 压力写入", s3.node_count() == 50
          and s3.point_count() == 50 * 60)
    print(f"  [INFO] 50 节点压力耗时 {elapsed*1000:.1f} ms")

    # 节点删除
    s.remove_node("n1")
    check("remove_node 清历史", s.node_count() == 0)


# ---------- 5. AlertStore ----------

def test_alert_store():
    print("\n--- 5. AlertStore（30s 去重）---")
    s = AlertStore(dedup_seconds=30)
    added, counts = [], []
    s.alert_added.connect(lambda a: added.append(a))
    s.count_changed.connect(lambda c: counts.append(c))

    a1 = {"node_id": "n1", "path": "cpu.total_usage", "name": "CPU 使用率",
          "value": 96, "threshold": 95, "level": "red"}
    ok1 = s.push(a1)
    check("首次 push 新增", ok1)
    ok2 = s.push(dict(a1))   # 30s 内重复
    check("30s 内重复去重", not ok2)
    check("active_count=1", s.active_count() == 1)
    check("red_count=1", s.red_count() == 1)

    # 不同 path 可新增
    a2 = dict(a1)
    a2["path"] = "gpu.core_temp_c"
    a2["value"] = 92
    ok3 = s.push(a2)
    check("不同 path 新增", ok3)
    check("active_count=2", s.active_count() == 2)

    # 缺字段
    check("缺 node_id/path 拒绝", not s.push({"level": "red"}))
    check("缺字段不影响计数", s.active_count() == 2)

    # clear_node
    s.clear_node("n1")
    check("clear_node 清空 n1", s.active_count() == 0)
    check("count_changed 有 0", 0 in counts)

    # 时间窗口越过：直接改内部时间戳模拟（不 sleep 30s）
    s2 = AlertStore(dedup_seconds=1)
    s2.push(dict(a1))
    s2._last_alert_ts[("n1", "cpu.total_usage")] = time.time() - 5
    ok = s2.push(dict(a1))
    check("超过去重窗口后再次新增", ok)

    # summary
    sm = s2.summary()
    check("summary 结构", set(sm.keys()) == {"red", "warn", "active", "total"})


# ---------- 6. SettingsFacade ----------

def test_settings_facade():
    print("\n--- 6. SettingsFacade（包装 ConfigManager）---")
    from common.config_manager import ConfigManager, SettingsManager
    from host.facade.settings_facade import SettingsFacade

    # 用独立临时 manager，避免污染真实配置
    mgr = ConfigManager()
    mgr.load()
    fac = SettingsFacade(mgr)

    # 默认值兜底（v5.2 新字段未写入配置）
    check("theme 默认 dark", fac.get("theme") == "dark")
    check("chart_refresh_ms 默认 500", fac.get("chart_refresh_ms") == 500)
    check("history_minutes 默认 5", fac.get("history_minutes") == 5)
    check("alert_dedup_seconds 默认 30", fac.get("alert_dedup_seconds") == 30)
    check("ws_read_timeout 默认 30", fac.get("ws_read_timeout") == 30)
    check("reconnect_interval 默认 60", fac.get("reconnect_interval") == 60)

    # 写读
    changed = []
    fac.settings_changed.connect(lambda k: changed.append(k))
    fac.set("theme", "light")
    check("set 后 get", fac.get("theme") == "light")
    check("settings_changed 触发", "theme" in changed)

    fac.set("log_level", "DEBUG")
    check("log_level 写读", fac.get("log_level") == "DEBUG")

    # 别名一致
    check("SettingsManager 是 ConfigManager 别名", SettingsManager is ConfigManager)


# ---------- 7. AlertAdapter ----------

def test_alert_adapter():
    print("\n--- 7. AlertAdapter（AlertEngine → AlertStore）---")
    from host.alerts import AlertEngine
    from host.facade.alert_adapter import AlertAdapter
    from host.store.alert_store import AlertStore

    # 单条规则
    engine = AlertEngine([{"path": "cpu.total_usage", "name": "CPU",
                           "red": 90, "warn": 80}])
    store = AlertStore(dedup_seconds=30)
    adapter = AlertAdapter(engine, store)

    frame_ok = {"cpu": {"total_usage": 50}}
    added = adapter.evaluate("n1", frame_ok, alias="游戏主机")
    check("正常帧无告警", added == [] and store.active_count() == 0)

    frame_red = {"cpu": {"total_usage": 95}}
    added = adapter.evaluate("n1", frame_red, alias="游戏主机")
    check("超红线新增告警", len(added) == 1)
    check("告警带 node_id/alias", added[0]["node_id"] == "n1"
          and added[0]["node_alias"] == "游戏主机")
    check("告警 level=red", added[0]["level"] == "red")

    # 30s 去重
    added2 = adapter.evaluate("n1", frame_red, alias="游戏主机")
    check("30s 内重复检测去重", added2 == [])

    # 恢复 → 清空活动告警
    adapter.evaluate("n1", frame_ok, alias="游戏主机")
    check("恢复后活动告警清空", store.active_count() == 0)


# ---------- 8. TrayManager / DiscoveryService ----------

def test_managers():
    print("\n--- 8. TrayManager / DiscoveryService ---")
    from host.manager.tray_manager import TrayManager

    # TrayManager：无 PyQt5 环境降级安全
    tray = TrayManager(on_show=lambda: None, on_quit=lambda: None)
    ok = tray.init(tooltip="test")
    check("TrayManager.init 不抛异常", True)
    check("TrayManager 降级安全（返回值 bool）", isinstance(ok, bool))
    tray.shutdown()
    check("TrayManager.shutdown 无异常", True)


# ---------- 9. Service 层 ----------

def test_service_alert():
    print("\n--- 9. AlertService（FrameStore→AlertEngine→AlertStore）---")
    from host.alerts import AlertEngine
    from host.store.frame_store import FrameStore
    from host.store.alert_store import AlertStore
    from host.service.alert_service import AlertService

    engine = AlertEngine([{"path": "cpu.total_usage", "name": "CPU",
                           "red": 90, "warn": 80}])
    fs = FrameStore()
    astore = AlertStore(dedup_seconds=30)
    svc = AlertService(engine, frame_store=fs, alert_store=astore,
                       auto_subscribe=True)
    check("订阅已建立", svc._subscribed)

    # 通过 FrameStore 推帧 → AlertService 自动评估
    fs.push("n1", {"cpu": {"total_usage": 95}}, ts=100.0)
    check("超红线自动入 AlertStore", astore.active_count() == 1)
    alert = astore.active()[0]
    check("告警字段完整", all(k in alert for k in
          ("node_id", "node_alias", "timestamp", "name", "path",
           "value", "level", "threshold")))

    # 30s 去重（通过 FrameStore 再推同值）
    fs.push("n1", {"cpu": {"total_usage": 95}}, ts=101.0)
    check("30s 内去重（active 仍 1）", astore.active_count() == 1)

    # 恢复
    fs.push("n1", {"cpu": {"total_usage": 50}}, ts=102.0)
    check("恢复后活动告警清空", astore.active_count() == 0)

    # shutdown
    svc.shutdown()
    check("shutdown 断开订阅", not svc._subscribed)


def test_service_discovery():
    print("\n--- 10. DiscoveryService（service 层）---")
    from host.service.discovery_service import DiscoveryService
    svc = DiscoveryService(udp_port=12346, auto_start=False)
    check("创建成功", True)
    hosts = svc.get_hosts()
    check("get_hosts 返回 dict", isinstance(hosts, dict))
    svc.start()
    check("start 后 running", svc._running)
    svc.stop()
    check("stop 后 running False", not svc._running)


# ---------- 11. Store 规格别名 ----------

def test_store_aliases():
    print("\n--- 11. Store 规格别名（append/get_history/remove）---")
    from host.store.history_store import HistoryStore
    from host.store.alert_store import AlertStore

    h = HistoryStore(maxlen=5)
    h.append("n1", "cpu", 1.0)
    h.append("n1", "cpu", 2.0)
    check("append 等价 push", len(h.get_history("n1", "cpu")) == 2)
    check("get_history 最近优先", h.get_history("n1", "cpu")[-1][1] == 2.0)

    a = AlertStore()
    a.push({"node_id": "n1", "path": "cpu.total_usage", "level": "red",
            "name": "CPU", "value": 95, "threshold": 90})
    a.remove("n1")
    check("remove 等价 clear_node", a.active_count() == 0)


def main():
    print("=" * 60)
    print("v5.2 Phase 0 单元测试（store/facade/manager/service）")
    print("=" * 60)
    test_signals()
    test_node_store()
    test_frame_store()
    test_history_store()
    test_alert_store()
    test_settings_facade()
    test_alert_adapter()
    test_managers()
    test_service_alert()
    test_service_discovery()
    test_store_aliases()
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
