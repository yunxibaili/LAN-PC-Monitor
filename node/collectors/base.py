# -*- coding: utf-8 -*-
"""
采集器基类 —— 独立线程、异常隔离、线程安全读取（见《README.md》§5.2）。

设计要点：
- 每个采集器一个独立 daemon 线程，异常被隔离在 collect() 内部，
  单采集器失败不影响其他采集器。
- 首次采集预热（部分指标如 cpu_percent 首次返回 0）。
- 结果写入 threading.Lock 保护的共享字典，get() 返回副本，线程安全。
- 停止用 threading.Event：stop() 后 wait() 立即返回，线程及时退出。
"""
import logging
import threading

log = logging.getLogger("node.collectors.base")


class BaseCollector:
    """采集器基类。"""

    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self._lock = threading.Lock()
        self._data = {}
        self._stop_event = threading.Event()

    # ---------- 生命周期 ----------

    def start(self) -> None:
        """启动采集线程（daemon，独立线程运行 _loop）。"""
        threading.Thread(target=self._loop, daemon=True,
                         name=self.__class__.__name__).start()

    def stop(self) -> None:
        """停止采集线程（立即唤醒，不再睡满一个周期）。"""
        self._stop_event.set()

    # ---------- 采集循环 ----------

    def _loop(self) -> None:
        """采集主循环：预热 + 周期采集。"""
        try:
            result = self.collect()
            with self._lock:
                self._data = result
        except Exception as e:
            log.warning("%s 首次采集失败: %s", self.__class__.__name__, e)

        while not self._stop_event.is_set():
            try:
                result = self.collect()
                with self._lock:
                    self._data = result
            except Exception as e:
                # 停机期间关闭资源触发的异常属预期，静默退出
                if self._stop_event.is_set():
                    break
                log.warning("%s 采集失败: %s", self.__class__.__name__, e)
            self._stop_event.wait(self.interval)

    # ---------- 接口 ----------

    def collect(self) -> dict:
        """采集一次数据，返回字典。子类必须实现。"""
        raise NotImplementedError

    def get(self) -> dict:
        """线程安全读取最近一次采集结果（副本）。"""
        with self._lock:
            return dict(self._data)
