# -*- coding: utf-8 -*-
"""
性能兜底机制（见《README.md》§15）

v5.0：SelfMonitor 从 host/ 提升到 common/，供 Agent 与 Host 本机节点共用，消除反向依赖。

自监控：检测本程序 CPU 占用，超限自动降级（节点端/主机本机端共用）。
- CPU > 5% 触发降级（采集频率 1s→2s + 关闭帧率）
- CPU < 3% 恢复采集频率（帧率不自动恢复，避免抖动）
- 每 10 秒检查一次

健壮性（本次修复）：
1. **cpu_percent 首次调用返回自进程启动以来的平均值，可能虚高**，
   先预热一次建立基准（discard 首次结果），再评估即时占用。
2. **连续多次超阈值才降级**（默认连续 2 次 >5%），避免单次瞬时抖动误关帧率。
"""
import logging
import threading

import psutil

log = logging.getLogger("common.self_monitor")

# 降级/恢复阈值（§16.1）
DEGRADE_CPU = 5.0    # CPU > 5% 触发降级
RECOVER_CPU = 3.0    # CPU < 3% 恢复采集频率
# 连续超阈值次数达到才降级（防单次抖动）
DEGRADE_STREAK = 2


class SelfMonitor:
    """自监控：检测本程序 CPU 占用，超限自动降级。"""

    def __init__(self, aggregator, collectors: dict, interval: float = 10.0):
        """
        :param aggregator: 有 interval 属性（DataAggregator 或 LocalCollectorPack）
        :param collectors: 采集器字典（含 fps）
        :param interval:   自监控频率（秒）
        """
        self.aggregator = aggregator
        self.collectors = collectors
        self.interval = interval
        self.proc = psutil.Process()
        self._stop_event = threading.Event()
        self._prewarmed = False   # cpu_percent 是否已预热（首次采样虚高）
        self._streak = 0          # 连续超阈值次数

    def start(self) -> None:
        """启动自监控线程。"""
        threading.Thread(target=self._loop, daemon=True,
                         name="self-monitor").start()

    def stop(self) -> None:
        """停止自监控。"""
        self._stop_event.set()

    def check(self) -> None:
        """执行一次 CPU 占用检查并降级/恢复。"""
        try:
            cpu = self.proc.cpu_percent(interval=1.0)
        except Exception:
            return

        # 预热：首次调用返回自启动以来平均值（虚高），丢弃不评估
        if not self._prewarmed:
            self._prewarmed = True
            log.debug("自监控预热完成（首次 CPU 采样丢弃）")
            return

        if cpu > DEGRADE_CPU:
            self._streak += 1
            if self._streak >= DEGRADE_STREAK:
                log.warning("监控程序 CPU 占用 %.1f%% 连续超阈值，启动降级", cpu)
                if hasattr(self.aggregator, "interval"):
                    self.aggregator.interval = 2.0   # 1s → 2s
                if "fps" in self.collectors:
                    try:
                        self.collectors["fps"].stop()
                        log.warning("已关闭帧率采集器以降低占用")
                    except Exception:
                        pass
                self._streak = 0   # 降级后重置计数
        elif cpu < RECOVER_CPU:
            self._streak = 0
            if hasattr(self.aggregator, "interval") \
                    and getattr(self.aggregator, "interval", 1.0) > 1.0:
                self.aggregator.interval = 1.0
                log.info("监控程序 CPU 占用恢复，采集频率恢复 1s")
        else:
            # 中间区间（3~5%）：不降级不恢复，重置连续计数
            self._streak = 0

    def _loop(self) -> None:
        """周期性检查。"""
        while not self._stop_event.is_set():
            try:
                self.check()
            except Exception as e:
                log.debug("自监控检查失败: %s", e)
            self._stop_event.wait(self.interval)
