# -*- coding: utf-8 -*-
"""
NodeDetailViewModel —— 单节点详情数据转换层（v5.2 Phase 3-3A）。

职责：
  - 从 NodeStore + FrameStore 提取单节点完整指标
  - 转换为 NodeDetailData（内部分组 + to_dict 扁平化）
  - 每节点缓存 NodeDetailData，只更新变化节点
  - 不持有 UI 状态（current_node 由 NodesPage 管理）

审查修订（Phase 3-3A 审核）：
  ✅ _build_detail_data() 独立方法（可直接测试，不依赖 Signal）
  ✅ schema_version 字段（v5.3 兼容）
  ✅ to_dict() 使用 PREFIX_MAP 前缀映射
  ✅ 删除信号由 NodeStore 驱动（非 MainWindow）
  ✅ refresh_all() 供 on_show/语言切换/主题变化使用
"""
import logging

from host.store.signals import Signal

log = logging.getLogger("host.viewmodels.node_detail_vm")


# ---------- 内部分组数据类 ----------

class IdentityData:
    __slots__ = ("node_id", "alias", "status", "ip", "port")
    def __init__(self):
        self.node_id = ""
        self.alias = ""
        self.status = "unknown"
        self.ip = ""
        self.port = 0

class SystemData:
    __slots__ = ("hostname", "local_ip", "uptime")
    def __init__(self):
        self.hostname = "N/A"
        self.local_ip = "N/A"
        self.uptime = "N/A"

class CpuData:
    __slots__ = ("name", "usage", "cores_phys", "cores_logic",
                 "freq_mhz", "temp_c", "power_w")
    def __init__(self):
        self.name = "N/A"
        self.usage = None
        self.cores_phys = None
        self.cores_logic = None
        self.freq_mhz = None
        self.temp_c = None
        self.power_w = None

class MemoryData:
    __slots__ = ("total_gb", "used_gb", "avail_gb", "usage", "swap_mb")
    def __init__(self):
        self.total_gb = None
        self.used_gb = None
        self.avail_gb = None
        self.usage = None
        self.swap_mb = None

class GpuData:
    __slots__ = ("name", "usage", "vram_used", "vram_total",
                 "core_temp", "hotspot_temp", "freq_mhz", "power_w")
    def __init__(self):
        self.name = "N/A"
        self.usage = None
        self.vram_used = None
        self.vram_total = None
        self.core_temp = None
        self.hotspot_temp = None
        self.freq_mhz = None
        self.power_w = None

class DiskData:
    __slots__ = ("drive", "read_mb_s", "write_mb_s", "usage", "free_gb", "all_disks")
    def __init__(self):
        self.drive = "N/A"
        self.read_mb_s = None
        self.write_mb_s = None
        self.usage = None
        self.free_gb = None
        self.all_disks = []

class NetworkData:
    __slots__ = ("iface", "up_mb_s", "down_mb_s", "link_speed")
    def __init__(self):
        self.iface = "N/A"
        self.up_mb_s = None
        self.down_mb_s = None
        self.link_speed = None

class QualityData:
    __slots__ = ("rtt", "gw_rtt", "loss", "score", "grade")
    def __init__(self):
        self.rtt = None
        self.gw_rtt = None
        self.loss = None
        self.score = None
        self.grade = "N/A"

class FpsData:
    __slots__ = ("window", "value", "frame_time", "low1", "source")
    def __init__(self):
        self.window = "N/A"
        self.value = None
        self.frame_time = None
        self.low1 = None
        self.source = "N/A"

class ProcessData:
    __slots__ = ("cpu_text", "gpu_text")
    def __init__(self):
        self.cpu_text = "N/A"
        self.gpu_text = "N/A"


# ---------- to_dict 前缀映射 ----------

PREFIX_MAP = {
    "identity": "",       # 无前缀：node_id, alias, status, ip, port
    "system": "system",   # system_hostname, system_uptime, ...
    "cpu": "cpu",
    "memory": "memory",
    "gpu": "gpu",
    "disk": "disk",
    "network": "network",
    "quality": "quality",
    "fps": "fps",
    "processes": "proc",
}

# 组名 -> 实例属性名
_GROUP_MAP = {
    "identity": "identity",
    "system": "system",
    "cpu": "cpu",
    "memory": "memory",
    "gpu": "gpu",
    "disk": "disk",
    "network": "network",
    "quality": "quality",
    "fps": "fps",
    "processes": "processes",
}


class NodeDetailData:
    """单节点完整详情数据（内部分组 + to_dict 扁平化）。"""

    schema_version = 1

    def __init__(self):
        self.identity = IdentityData()
        self.system = SystemData()
        self.cpu = CpuData()
        self.memory = MemoryData()
        self.gpu = GpuData()
        self.disk = DiskData()
        self.network = NetworkData()
        self.quality = QualityData()
        self.fps = FpsData()
        self.processes = ProcessData()

    def to_dict(self) -> dict:
        """扁平化输出，供 UI 消费。前缀映射见 PREFIX_MAP。"""
        d = {"schema_version": self.schema_version}
        for group_name, attr_name in _GROUP_MAP.items():
            group = getattr(self, attr_name)
            prefix = PREFIX_MAP.get(group_name, group_name)
            for k in group.__slots__:
                v = getattr(group, k)
                key = f"{prefix}_{k}" if prefix else k
                d[key] = v
        return d


# ---------- ViewModel ----------

class NodeDetailViewModel:
    """
    单节点详情数据转换层。

    数据仓库模式：只负责从 Store 提取 + 转换，不持有 UI 状态。
    current_node 由 NodesPage 管理，VM 通过 get_data(node_id) 按需查询。
    """

    data_updated = Signal(str)   # 某节点数据变化 (node_id)
    data_removed = Signal(str)   # 某节点缓存清理 (node_id)

    def __init__(self, node_store, frame_store):
        self._node_store = node_store
        self._frame_store = frame_store
        self._cache = {}  # node_id -> NodeDetailData

        # 监听 Store 信号
        self._frame_store.frame_updated.connect(self._on_frame_updated)
        self._node_store.node_removed.connect(self._on_node_removed)
        self._node_store.status_changed.connect(self._on_status_changed)
        self._node_store.metrics_updated.connect(self._on_metrics_updated)

    # ---------- 信号处理 ----------

    def _on_frame_updated(self, node_id: str, frame: dict) -> None:
        """帧更新 -> 构建/更新缓存 -> emit。"""
        data = self._build_detail_data(node_id, frame)
        self._cache[node_id] = data
        self.data_updated.emit(node_id)

    def _on_node_removed(self, node_id: str) -> None:
        """节点删除 -> 清缓存 -> emit。"""
        if node_id in self._cache:
            del self._cache[node_id]
            self.data_removed.emit(node_id)

    def _on_status_changed(self, node_id: str, status: str) -> None:
        """状态变更 -> 更新缓存 identity.status。"""
        data = self._cache.get(node_id)
        if data:
            data.identity.status = status
            self.data_updated.emit(node_id)

    def _on_metrics_updated(self, node_id: str) -> None:
        """评分更新 -> 更新缓存 quality。"""
        data = self._cache.get(node_id)
        if data:
            score_info = self._node_store.get_score(node_id)
            if score_info:
                data.quality.score = score_info[0]
                data.quality.grade = score_info[1]
            self.data_updated.emit(node_id)

    # ---------- 数据构建（独立方法，可直接测试） ----------

    def _build_detail_data(self, node_id: str, frame: dict) -> "NodeDetailData":
        """从 monitor_data 帧构建 NodeDetailData（纯转换，无副作用）。"""
        data = NodeDetailData()

        # Identity（从 NodeStore 读取）
        node_info = self._node_store.get(node_id)
        if node_info:
            data.identity.node_id = node_id
            data.identity.alias = node_info.get("alias", node_id)
            data.identity.ip = node_info.get("ip", "")
            data.identity.port = node_info.get("port", 0)
        else:
            data.identity.node_id = node_id
            data.identity.alias = node_id
        data.identity.status = self._node_store.get_status(node_id) or "unknown"
        score_info = self._node_store.get_score(node_id)
        if score_info:
            data.quality.score = score_info[0]
            data.quality.grade = score_info[1]

        # System
        sys_info = frame.get("system", {})
        data.system.hostname = sys_info.get("hostname", "N/A")
        data.system.local_ip = sys_info.get("local_ip", "N/A")
        from common.utils import format_uptime
        data.system.uptime = format_uptime(sys_info.get("uptime_seconds", 0))

        # CPU
        cpu = frame.get("cpu", {})
        data.cpu.name = cpu.get("name", "N/A")
        data.cpu.usage = _safe_float(cpu.get("total_usage"))
        data.cpu.cores_phys = _safe_int(cpu.get("physical_cores"))
        data.cpu.cores_logic = _safe_int(cpu.get("logical_cores"))
        data.cpu.freq_mhz = _safe_float(cpu.get("core_freq_mhz"))
        data.cpu.temp_c = _safe_float(cpu.get("package_temp_c"))
        data.cpu.power_w = _safe_float(cpu.get("power_w"))

        # Memory
        ram = frame.get("ram", {})
        data.memory.total_gb = _safe_float(ram.get("total_gb"))
        data.memory.used_gb = _safe_float(ram.get("used_gb"))
        data.memory.avail_gb = _safe_float(ram.get("available_gb"))
        data.memory.usage = _safe_float(ram.get("usage_percent"))
        data.memory.swap_mb = _safe_float(ram.get("swap_used_mb"))

        # GPU
        gpu = frame.get("gpu", {})
        data.gpu.name = gpu.get("name", "N/A")
        data.gpu.usage = _safe_float(gpu.get("usage_percent"))
        data.gpu.vram_used = _safe_float(gpu.get("vram_used_mb"))
        data.gpu.vram_total = _safe_float(gpu.get("vram_total_mb"))
        data.gpu.core_temp = _safe_float(gpu.get("core_temp_c"))
        data.gpu.hotspot_temp = _safe_float(gpu.get("hotspot_temp_c"))
        data.gpu.freq_mhz = _safe_float(gpu.get("core_freq_mhz"))
        data.gpu.power_w = _safe_float(gpu.get("power_w"))

        # Disk（取 disk[0]，保留全量）
        disks = frame.get("disk", [])
        data.disk.all_disks = disks if isinstance(disks, list) else []
        if data.disk.all_disks:
            d0 = data.disk.all_disks[0]
            data.disk.drive = d0.get("drive", "N/A")
            data.disk.read_mb_s = _safe_float(d0.get("read_mb_s"))
            data.disk.write_mb_s = _safe_float(d0.get("write_mb_s"))
            data.disk.usage = _safe_float(d0.get("usage_percent"))
            data.disk.free_gb = _safe_float(d0.get("free_gb"))

        # Network
        net = frame.get("net", {})
        data.network.iface = net.get("interface", "N/A")
        data.network.up_mb_s = _safe_float(net.get("upload_mb_s"))
        data.network.down_mb_s = _safe_float(net.get("download_mb_s"))
        data.network.link_speed = _safe_float(net.get("link_speed_mbps"))

        # Network Quality
        nq = frame.get("net_quality", {})
        data.quality.rtt = _safe_float(nq.get("latency_to_client_ms"))
        data.quality.gw_rtt = _safe_float(nq.get("latency_to_gateway_ms"))
        data.quality.loss = _safe_float(nq.get("packet_loss_percent"))
        # score/grade 在 _on_metrics_updated 中由 NodeStore 更新

        # FPS
        fps = frame.get("fps", {})
        data.fps.window = fps.get("window_title", "N/A")
        data.fps.value = _safe_float(fps.get("fps"))
        data.fps.frame_time = _safe_float(fps.get("frame_time_ms"))
        data.fps.low1 = _safe_float(fps.get("low_1_percent"))
        data.fps.source = fps.get("source", "N/A")

        # Processes
        proc = frame.get("processes", {})
        top_cpu = proc.get("top_cpu", [])
        top_gpu = proc.get("top_gpu", [])
        data.processes.cpu_text = "  ".join(
            f"{p.get('name','?')} {p.get('usage_percent',0)}%"
            for p in top_cpu) or "N/A"
        data.processes.gpu_text = "  ".join(
            f"{p.get('name','?')} {p.get('usage_percent',0)}%"
            for p in top_gpu) or "N/A"

        return data

    # ---------- 查询接口 ----------

    def get_data(self, node_id: str):
        """返回 NodeDetailData；不存在返回 None。"""
        return self._cache.get(node_id)

    def get_summary(self, node_id: str) -> dict:
        """兼容旧 get_summary()：返回扁平摘要字典。"""
        data = self._cache.get(node_id)
        if not data:
            return {}
        return {
            "cpu_usage": data.cpu.usage,
            "gpu_usage": data.gpu.usage,
            "ram_usage": data.memory.usage,
            "cpu_temp": data.cpu.temp_c,
            "gpu_temp": data.gpu.core_temp,
            "fps": data.fps.value,
            "rtt": data.quality.rtt,
            "score": data.quality.score,
            "grade": data.quality.grade,
        }

    def node_ids(self) -> list:
        return list(self._cache.keys())

    # ---------- 刷新 ----------

    def refresh_all(self) -> None:
        """主动刷新所有缓存节点（供 on_show/语言切换/主题变化）。"""
        for node_id in list(self._cache.keys()):
            frame = self._frame_store.get(node_id)
            if frame:
                data = self._build_detail_data(node_id, frame)
                self._cache[node_id] = data
                self.data_updated.emit(node_id)


# ---------- 工具函数 ----------

def _safe_float(val, default=None):
    if val is None or val == "N/A":
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default

def _safe_int(val, default=None):
    if val is None or val == "N/A":
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default
