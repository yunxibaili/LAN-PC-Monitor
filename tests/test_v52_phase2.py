# -*- coding: utf-8 -*-
"""
v5.2 Phase 2 单元测试 —— Alert/Tray/Discovery 解耦。

验证（不依赖 PyQt5 真机，用 stub 信号后端）：
- AlertService：FrameStore → AlertEngine → AlertStore 全链路（告警解耦）
- AlertService 重建（设置变更后）：新引擎生效
- TrayManager：init/shutdown/show_message 降级安全
- DiscoveryService：get_hosts/后台发现回调
- main_window 不再直接调用 AlertEngine.check / 构造 QSystemTrayIcon
  （通过源码扫描验证解耦）

用法：python tests/test_v52_phase2.py
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from host.store.frame_store import FrameStore
from host.store.alert_store import AlertStore
from host.store.node_store import NodeStore
from host.service.alert_service import AlertService
from host.facade.settings_facade import SettingsFacade

PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  {detail}")


def test_alert_decoupled():
    """告警解耦：AlertService 全链路，main_window 不再直接调用 AlertEngine.check。"""
    print("\n--- 1. 告警解耦（AlertService 全链路）---")
    from host.alerts import AlertEngine

    fs = FrameStore()
    astore = AlertStore(dedup_seconds=30)
    nstore = NodeStore()
    svc = AlertService(AlertEngine([
        {"path": "cpu.total_usage", "name": "CPU", "red": 90, "warn": 80}]),
        frame_store=fs, alert_store=astore, node_store=nstore,
        auto_subscribe=True)

    # 帧推送 → AlertService 自动评估
    fs.push("n1", {"cpu": {"total_usage": 95}}, ts=100.0)
    check("FrameStore→AlertService→AlertStore 自动入告警", astore.active_count() == 1)
    a = astore.active()[0]
    check("告警统一格式", all(k in a for k in
          ("node_id", "node_alias", "timestamp", "name", "path",
           "value", "level", "threshold")))
    check("node_alias 来自 NodeStore", a["node_alias"] == "n1")

    # 恢复
    fs.push("n1", {"cpu": {"total_usage": 50}}, ts=102.0)
    check("恢复后活动告警清空", astore.active_count() == 0)

    # 设置变更后重建 AlertService → 新规则生效
    svc2 = AlertService(AlertEngine([
        {"path": "ram.usage_percent", "name": "RAM", "red": 95, "warn": 80}]),
        frame_store=fs, alert_store=astore, node_store=nstore,
        auto_subscribe=True)
    fs.push("n1", {"cpu": {"total_usage": 99}, "ram": {"usage_percent": 90}}, ts=103.0)
    # cpu 99 但新规则只查 ram（warn 80）→ ram 90 触发 warn
    check("重建后新规则生效（ram warn）", astore.active_count() >= 1)
    check("cpu 99 不再告警（旧规则已换）",
          not any(x["path"] == "cpu.total_usage" for x in astore.active()))


def test_mainwindow_decoupled_source():
    """源码扫描：main_window 不再直接调用 AlertEngine.check / 构造 QSystemTrayIcon。"""
    print("\n--- 2. main_window 解耦源码检查 ---")
    src = open(os.path.join(ROOT, "host/gui/main_window.py"), encoding="utf-8").read()

    # AlertEngine.check 直接调用应消失
    check("无 alert_engine.check 直接调用",
          "alert_engine.check(" not in src)
    # QSystemTrayIcon 直接构造应消失
    check("无 QSystemTrayIcon( 直接构造", "QSystemTrayIcon(" not in src)
    # 无 DiscoveryListener/MdnsDiscovery 直接 import
    check("无 DiscoveryListener/MdnsDiscovery import",
          "DiscoveryListener" not in src and "MdnsDiscovery" not in src)
    # 有 DiscoveryService / TrayManager / AlertService 引用
    check("引入 DiscoveryService", "DiscoveryService" in src)
    check("引入 TrayManager", "TrayManager" in src)
    check("引入 AlertService", "AlertService" in src)


def test_tray_manager():
    """TrayManager 降级安全。"""
    print("\n--- 3. TrayManager ---")
    from host.manager.tray_manager import TrayManager
    tray = TrayManager(on_show=lambda: None, on_quit=lambda: None)
    ok = tray.init(tooltip="test")
    check("init 返回 bool", isinstance(ok, bool))
    # show_message 在不可用/无 PyQt5 时静默
    try:
        tray.show_message("t", "m", icon="warning", timeout_ms=100)
        check("show_message 不抛异常", True)
    except Exception as e:
        check("show_message 不抛异常", False, str(e))
    try:
        tray.shutdown()
        check("shutdown 不抛异常", True)
    except Exception as e:
        check("shutdown 不抛异常", False, str(e))


def test_discovery_service():
    """DiscoveryService 后台发现回调。"""
    print("\n--- 4. DiscoveryService ---")
    from host.service.discovery_service import DiscoveryService
    svc = DiscoveryService(udp_port=12346, auto_start=False)
    check("创建成功", True)
    hosts = svc.get_hosts()
    check("get_hosts 返回 dict", isinstance(hosts, dict))
    svc.start()
    check("start 后 running", svc._running)

    # 后台发现回调（短延迟）
    called = []
    svc._discover_delay = 0.1
    svc.auto_discover_background(on_found=lambda h: called.append(h))
    import time as _t
    _t.sleep(0.5)
    check("后台发现回调触发", len(called) >= 1)
    svc.stop()
    check("stop 后 running False", not svc._running)


def test_settings_facade_reuse():
    """SettingsFacade 复用（Phase 2 仍经 ConfigManager，不重复实现）。"""
    print("\n--- 5. SettingsFacade 复用 ---")
    from common.config_manager import ConfigManager, SettingsManager
    from host.facade.settings_facade import SettingsFacade
    check("SettingsManager 是 ConfigManager 别名", SettingsManager is ConfigManager)
    mgr = ConfigManager(); mgr.load()
    fac = SettingsFacade(mgr)
    check("get/set/reset 接口存在",
          hasattr(fac, "get") and hasattr(fac, "set") and hasattr(fac, "reset"))
    fac.set("theme", "light")
    check("set 生效", fac.get("theme") == "light")
    fac.reset("theme")
    check("reset 恢复默认", fac.get("theme") == "dark")


def main():
    print("=" * 60)
    print("v5.2 Phase 2 单元测试（告警/托盘/发现解耦）")
    print("=" * 60)
    test_alert_decoupled()
    test_mainwindow_decoupled_source()
    test_tray_manager()
    test_discovery_service()
    test_settings_facade_reuse()
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
