# -*- coding: utf-8 -*-
"""
性能兜底机制（见《技术文档.md》§18.7）。

自监控：检测本程序 CPU 占用，超限自动降级（节点端/主机本机端共用）。
- CPU > 5% 触发降级（采集频率 1s→2s + 关闭帧率）
- CPU < 3% 恢复采集频率（帧率不自动恢复，避免抖动）
- 每 10 秒检查一次
"""
import logging
import threading

import psutil

log = logging.getLogger("host.self_monitor")


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
        if cpu > 5.0:
            log.warning("监控程序 CPU 占用 %.1f%% 超阈值，启动降级", cpu)
            if hasattr(self.aggregator, "interval"):
                self.aggregator.interval = 2.0   # 1s → 2s
            if "fps" in self.collectors:
                try:
                    self.collectors["fps"].stop()
                    log.warning("已关闭帧率采集器以降低占用")
                except Exception:
                    pass
        elif cpu < 3.0 and hasattr(self.aggregator, "interval") \
                and getattr(self.aggregator, "interval", 1.0) > 1.0:
            self.aggregator.interval = 1.0
            log.info("监控程序 CPU 占用恢复，采集频率恢复 1s")

    def _loop(self) -> None:
        """周期性检查。"""
        while not self._stop_event.is_set():
            try:
                self.check()
            except Exception as e:
                log.debug("自监控检查失败: %s", e)
            self._stop_event.wait(self.interval)
