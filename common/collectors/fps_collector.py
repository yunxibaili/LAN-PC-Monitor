# -*- coding: utf-8 -*-
"""
帧率采集器 —— PresentMon CLI 主方案 + DXGI 截帧降级（见《README.md》§11）。

方案选择（§11.1）：
1. collectors.fps == "presentmon"（默认）：检测 tools/PresentMon.exe 存在且管理员 → PresentMon
2. PresentMon.exe 不存在或非管理员 → 自动降级 DXGI
3. collectors.fps == "dxgi"：强制 DXGI
4. collectors.fps == false：不采集，返回 N/A（source: "none"）

前台窗口动态绑定（§11.2）：每秒检测前台进程名，变化时重启 PresentMon 会话。
1% Low（§11.6）：FrameStats 最近 100 帧取第 99 百分位。

降级日志提示（§11.1）：有管理员但 PresentMon.exe 未找到时打 INFO 日志，
让用户明确帧率精度受限（§20.11 统一由采集器打印）。
"""
import logging
import os
import subprocess
import threading
import time
from collections import deque

from common.collectors.base import BaseCollector

log = logging.getLogger("common.collectors.fps")

# dxcam 降级警告仅打印一次（进程级）
_DXCAM_WARNED = [False]

# PresentMon 工具路径（相对项目根）
PRESENTMON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "tools", "PresentMon.exe")


class FrameStats:
    """最近 100 帧滑动窗口统计（§11.6）。"""

    def __init__(self):
        self.frame_times = deque(maxlen=100)

    def push(self, ms: float) -> None:
        """压入一帧帧时间（毫秒）。"""
        self.frame_times.append(ms)

    def fps(self):
        """平均 FPS。"""
        if not self.frame_times:
            return "N/A"
        return round(1000 / (sum(self.frame_times) / len(self.frame_times)), 1)

    def low_1(self):
        """1% Low FPS（第 99 百分位帧时间的倒数）。"""
        if len(self.frame_times) < 10:
            return "N/A"
        import numpy as np
        p99 = np.percentile(list(self.frame_times), 99)
        if p99 <= 0:
            return "N/A"
        return round(1000 / p99, 1)


class PresentMonSession:
    """PresentMon 子进程管理（§11.4）。"""

    def __init__(self, stats: FrameStats):
        self.stats = stats
        self.proc = None
        self.read_thread = None
        self._running = False
        self._lock = threading.Lock()
        self._header = None   # CSV 表头列名 → 索引

    def start(self, process_name: str) -> bool:
        """启动 PresentMon 捕获指定前台进程。"""
        self.stop()
        try:
            self.proc = subprocess.Popen(
                [PRESENTMON_PATH, "-process_name", process_name,
                 "-output_stdout", "-no_top", "-stop_existing_session",
                 "-session_name", "PCMonitor"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            self._running = True
            self.read_thread = threading.Thread(target=self._read_loop,
                                                daemon=True)
            self.read_thread.start()
            return True
        except Exception as e:
            log.warning("PresentMon 启动失败: %s", e)
            self.proc = None
            return False

    def _read_loop(self) -> None:
        """读取 PresentMon 输出的 CSV 行并解析。"""
        try:
            for line in self.proc.stdout:
                if not self._running:
                    break
                self._parse_csv_line(line.decode("utf-8", errors="replace"))
        except Exception:
            pass

    def _parse_csv_line(self, line: str) -> None:
        """解析 CSV 行，提取 msBetweenPresents 等字段（§11.3）。"""
        try:
            parts = line.strip().split(",")
            if len(parts) < 3 or parts[0] == "Application":
                return  # 表头或无效行
            # 关键字段：msBetweenPresents（索引按 PresentMon 输出顺序）
            # 简化：遍历查找含 msBetweenPresents 的列
            if self._header is None:
                self._header = {name: i for i, name in enumerate(parts)}
                return
            ms_idx = self._header.get("msBetweenPresents")
            if ms_idx is None or ms_idx >= len(parts):
                return
            ms = float(parts[ms_idx])
            if ms > 0:
                self.stats.push(ms)
        except Exception:
            pass

    def stop(self) -> None:
        """停止 PresentMon 子进程。"""
        self._running = False
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            except Exception:
                pass
            self.proc = None


class DxFpsEstimator:
    """DXGI 截帧降级（§11.5）：dxcam 桌面帧差分估计。"""

    def __init__(self, stats: FrameStats, threshold: float = 0.02):
        self.stats = stats
        self.threshold = threshold
        self.camera = None
        self.prev = None
        self._last_frame_time = None
        try:
            import dxcam
            self.camera = dxcam.create(output_color="GRAY")
        except Exception as e:
            # 预期降级：dxcam 未安装属正常环境差异，用 INFO 一次性提示（不刷屏）
            if not _DXCAM_WARNED[0]:
                _DXCAM_WARNED[0] = True
                log.info("dxcam 未安装，帧率降级为 N/A（可 `pip install dxcam` 启用）: %s", e)
            self.camera = None

    def sample(self) -> None:
        """采样一帧，检测画面变化计入帧时间。"""
        if self.camera is None:
            return
        try:
            frame = self.camera.grab()
            if frame is None:
                return
            if self.prev is None:
                self.prev = frame
                return
            import numpy as np
            diff = np.mean(np.abs(frame.astype(int) - self.prev.astype(int)) > 8)
            now = time.perf_counter()
            if diff > self.threshold and self._last_frame_time is not None:
                ms = (now - self._last_frame_time) * 1000
                self.stats.push(ms)
            self._last_frame_time = now
            self.prev = frame
        except Exception:
            pass


class FpsCollector(BaseCollector):
    """帧率采集器。"""

    def __init__(self, interval: float = 1.0, mode: str = "presentmon"):
        super().__init__(interval)
        self.mode = mode          # "presentmon" / "dxgi" / "none"
        self.stats = FrameStats()
        self.presentmon = None
        self.dxgi = None
        self._current_proc = ""
        self._init_backend()

    def _init_backend(self) -> None:
        """按配置选择帧率后端（§11.1）。"""
        if self.mode == "none" or self.mode is False:
            self.mode = "none"
            return
        if self.mode == "dxgi":
            self._init_dxgi()
            return
        # 默认 presentmon：检测工具 + 管理员
        if os.path.exists(PRESENTMON_PATH):
            # 管理员检测（Windows 提权）
            is_admin = self._is_admin()
            if is_admin:
                self.mode = "presentmon"
                self.presentmon = PresentMonSession(self.stats)
                log.info("帧率后端: PresentMon")
                return
            log.info("非管理员权限，PresentMon 需管理员，降级 DXGI")
        else:
            # 有管理员期望但工具缺失 → 打降级提示日志（§11.1 / §20.11）
            log.info("PresentMon.exe 未找到，已自动降级为 DXGI 截帧模式，"
                     "如需更精准帧率请下载 PresentMon.exe 放入 tools/ 目录")
        self._init_dxgi()

    def _init_dxgi(self) -> None:
        """初始化 DXGI 降级。"""
        self.mode = "dxgi"
        self.dxgi = DxFpsEstimator(self.stats)
        log.info("帧率后端: DXGI 截帧（降级）")

    @staticmethod
    def _is_admin() -> bool:
        """检测当前进程是否管理员（Windows）。"""
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return True  # 非 Windows 环境视为有权限，便于测试

    @staticmethod
    def get_foreground_process_name():
        """获取前台进程名（§11.2）。"""
        try:
            import win32gui
            import win32process
            import psutil
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                return psutil.Process(pid).name()
            except Exception:
                return ""
        except Exception:
            return ""

    def stop(self) -> None:
        """停止帧率采集，清理子进程。"""
        super().stop()
        if self.presentmon:
            self.presentmon.stop()
        self.presentmon = None

    def collect(self) -> dict:
        """采集帧率快照。"""
        if self.mode == "none":
            return {"window_title": "N/A", "fps": "N/A",
                    "frame_time_ms": "N/A", "low_1_percent": "N/A",
                    "source": "none"}

        if self.mode == "presentmon" and self.presentmon:
            # 前台窗口动态绑定（§11.2）：进程变化时重启 PresentMon
            proc = self.get_foreground_process_name()
            if proc and proc != self._current_proc:
                self._current_proc = proc
                self.presentmon.start(proc)
        elif self.mode == "dxgi" and self.dxgi:
            self.dxgi.sample()

        fps = self.stats.fps()
        low1 = self.stats.low_1()
        frame_time = None
        if self.stats.frame_times:
            frame_time = round(sum(self.stats.frame_times)
                               / len(self.stats.frame_times), 2)
        return {
            "window_title": self._current_proc or "N/A",
            "fps": fps,
            "frame_time_ms": frame_time if frame_time is not None else "N/A",
            "low_1_percent": low1,
            "source": self.mode,
        }
