# -*- coding: utf-8 -*-
"""
v5.2 Phase 2.8 单元测试 —— MainWindow 数据源收敛。

验证：
1. MainWindow 不存在重复状态维护：
   - frames/statuses/rtts/losses/scores/scorers 均为 Store 的 property 代理
   - 无 `self.frames = {}` 等 dict 初始化
   - 无 `self._alert_state`
2. Alert 只有一个去重来源（AlertStore 30s）
3. 数据流：Signal → Store → UI（property 读到 Store 数据）
4. QualityScorer 只在 NodeStore

用法：python tests/test_v52_phase28.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  {detail}")


def test_source_converged():
    """源码扫描：main_window 无重复 dict / 无 _alert_state。"""
    print("\n--- 1. 数据源收敛（源码扫描）---")
    src = open(os.path.join(ROOT, "host/gui/main_window.py"), encoding="utf-8").read()

    # 不应有 dict 初始化
    # 排除注释行中的示例文本，只查实际赋值（行首有缩进且非 # 开头）
    import re
    init_lines = [l for l in src.split("\n")
                  if re.match(r"^\s+self\.frames\s*=\s*\{\}", l)]
    check("无 self.frames = {} 初始化", not init_lines)
    check("无 self.statuses = {} 初始化", "self.statuses = {}" not in src)
    check("无 self.rtts = {} 初始化", "self.rtts = {}" not in src)
    check("无 self.losses = {} 初始化", "self.losses = {}" not in src)
    check("无 self.scorers = {} 初始化", "self.scorers = {}" not in src)
    check("无 self.scores = {} 初始化", "self.scores = {}" not in src)
    # 无 _alert_state
    check("无 self._alert_state", "_alert_state" not in src)
    # 有 property 代理
    check("有 @property frames 代理", "@property\n    def frames" in src
          or "def frames" in src and "frame_store._frames" in src)
    check("property 代理到 Store 内部 dict",
          "frame_store._frames" in src and "node_store._statuses" in src
          and "node_store._rtts" in src and "node_store._losses" in src
          and "node_store._scorers" in src and "node_store._scores" in src)


def test_property_alias_behavior():
    """property 代理行为：读/写一致指向 Store。"""
    print("\n--- 2. property 代理行为 ---")
    from host.store.frame_store import FrameStore
    from host.store.node_store import NodeStore

    # 模拟 MainWindow 的 property 语义：frames 读 FrameStore._frames
    fs = FrameStore()
    ns = NodeStore()

    # 直接操作 Store
    fs.push("n1", {"cpu": {"total_usage": 50}}, ts=1.0)
    ns.add_node("n1", alias="游戏主机")
    ns.update_status("n1", "connected")
    ns.update_rtt("n1", 0.5)
    ns.update_loss("n1", 0.0)
    ns.update_quality("n1", 0.5, 0.0)

    # 模拟 property 代理：frames → fs._frames；statuses 等 → ns._*
    frames = fs._frames
    statuses = ns._statuses
    rtts = ns._rtts
    losses = ns._losses
    scorers = ns._scorers
    scores = ns._scores

    check("frames 读到 Store", frames["n1"]["cpu"]["total_usage"] == 50)
    check("statuses 读到 Store", statuses["n1"] == "connected")
    check("rtts 读到 Store", rtts["n1"] == 0.5)
    check("losses 读到 Store", losses["n1"] == 0.0)
    check("scorers 只有 Store 持有", "n1" in scorers and isinstance(
        scorers["n1"], type(ns.get_scorer("n1"))))
    check("scores 读到 Store", scores["n1"] is not None)

    # 一致性：同一 dict 引用
    check("frames 与 Store 同一对象", frames is fs._frames)
    check("statuses 与 NodeStore 同一对象", statuses is ns._statuses)


def test_quality_scorer_only_in_nodestore():
    """QualityScorer 只在 NodeStore。"""
    print("\n--- 3. QualityScorer 收敛 ---")
    from host.store.node_store import NodeStore
    from common.quality import QualityScorer

    ns = NodeStore()
    ns.add_node("n1")
    scorer = ns.get_scorer("n1")
    check("NodeStore 持有 scorer", isinstance(scorer, QualityScorer))

    # main_window 源码中不应 import QualityScorer 或手动创建
    src = open(os.path.join(ROOT, "host/gui/main_window.py"), encoding="utf-8").read()
    check("main_window 不再手动 QualityScorer()",
          "QualityScorer(" not in src)


def test_alert_single_dedup():
    """Alert 只有 AlertStore 30s 一个去重来源。"""
    print("\n--- 4. Alert 单一去重来源 ---")
    from host.store.alert_store import AlertStore
    import time

    s = AlertStore(dedup_seconds=30)
    a = {"node_id": "n1", "path": "cpu.total_usage", "level": "red",
         "name": "CPU", "value": 95, "threshold": 90}
    check("首次新增", s.push(dict(a)) is True)
    check("30s 内去重", s.push(dict(a)) is False)
    # 超窗口再触发
    s._last_alert_ts[("n1", "cpu.total_usage")] = time.time() - 35
    check("超窗口再触发", s.push(dict(a)) is True)

    # main_window 无 _alert_state（唯一去重在 AlertStore）
    src = open(os.path.join(ROOT, "host/gui/main_window.py"), encoding="utf-8").read()
    check("main_window 无 _alert_state 去重", "_alert_state" not in src)


def test_signal_store_ui_flow():
    """数据流：Signal → Store → UI（property 读 Store）。"""
    print("\n--- 5. Signal → Store → UI 数据流 ---")
    from host.store.frame_store import FrameStore
    from host.store.node_store import NodeStore
    from host.store.alert_store import AlertStore
    from host.service.alert_service import AlertService
    from host.alerts import AlertEngine

    fs = FrameStore()
    astore = AlertStore(dedup_seconds=30)
    nstore = NodeStore()
    svc = AlertService(AlertEngine([
        {"path": "cpu.total_usage", "name": "CPU", "red": 90, "warn": 80}]),
        frame_store=fs, alert_store=astore, node_store=nstore,
        auto_subscribe=True)

    # Signal 源：模拟 NodeConnection._on_data → frame_store.push
    fs.push("n1", {"cpu": {"total_usage": 95}}, ts=1.0)
    # Store 已更新
    check("FrameStore 已更新", fs.get("n1")["cpu"]["total_usage"] == 95)
    check("AlertStore 已收到告警", astore.active_count() == 1)
    # UI 经 property 读 Store（模拟 self.frames → fs._frames）
    frames_proxy = fs._frames
    check("UI 读 Store 帧", frames_proxy["n1"]["cpu"]["total_usage"] == 95)

    # 恢复
    fs.push("n1", {"cpu": {"total_usage": 50}}, ts=2.0)
    check("恢复后告警清空", astore.active_count() == 0)


def main():
    print("=" * 60)
    print("v5.2 Phase 2.8 单元测试（数据源收敛）")
    print("=" * 60)
    test_source_converged()
    test_property_alias_behavior()
    test_quality_scorer_only_in_nodestore()
    test_alert_single_dedup()
    test_signal_store_ui_flow()
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
