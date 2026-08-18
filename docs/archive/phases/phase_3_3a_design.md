# Phase 3-3A：NodeDetailViewModel 设计文档（修订版）

> **Status**: COMPLETE
> **Date**: 2026-08-11
> **Result**: NodeDetailViewModel 实现完成，89 项测试全通过
> **Implementation**: `host/viewmodels/node_detail_vm.py`
> **Tests**: `test_v52_node_detail_vm.py`

审查要点落实：
- 内部分组 + 外部扁平（to_dict）
- VM 不持有 current_node（由 NodesPage 管理）
- VM 是数据仓库，不是页面状态
- 每节点缓存 NodeDetailData
- HistoryStore 分离（不进 DetailVM）
- 测试重点：字段映射/节点隔离/空数据/删除

---

## 一、现有 DetailPanel 分析

### 1.1 数据来源

DetailPanel 直接接收 monitor_data 帧：
```python
panel.update_all(frame)  # MainWindow._on_data 每秒调用
```

### 1.2 8 个 Panel 分组（43 字段）

| Panel | 字段数 | 关键字段 |
|-------|--------|----------|
| cpu.group | 7 | name, total_usage, physical_cores, logical_cores, core_freq_mhz, package_temp_c, power_w |
| ram.group | 5 | total_gb, used_gb, available_gb, usage_percent, swap_used_mb |
| gpu.group | 8 | name, usage_percent, vram_used_mb, vram_total_mb, core_temp_c, hotspot_temp_c, core_freq_mhz, power_w |
| disk.group | 5 | drive, read_mb_s, write_mb_s, usage_percent, free_gb |
| net.group | 4 | interface, upload_mb_s, download_mb_s, link_speed_mbps |
| netq.group | 5 | latency_to_client_ms, latency_to_gateway_ms, packet_loss_percent, quality_score, quality_grade |
| fps.group | 5 | window_title, fps, frame_time_ms, low_1_percent, source |
| proc.group | 1 | proc_summary (复合文本) |

### 1.3 问题

1. 数据与 UI 混合：update_all() 同时做数据提取 + QLabel 渲染
2. 无独立数据层：页面直接读 frame dict
3. 未来 Dashboard/Nodes/Monitor 三处会重复字段解析

---

## 二、NodeDetailViewModel 设计

### 2.1 核心原则

- **数据仓库**：VM 只负责从 Store 提取 + 转换数据
- **不持有 UI 状态**：current_node 由 NodesPage 管理
- **每节点缓存**：只更新变化的节点，不重复构造
- **HistoryStore 分离**：VM 只管实时状态，趋势数据由 MonitorPage 直接读 HistoryStore

### 2.2 信号设计

```python
class NodeDetailViewModel:
    data_updated = Signal(str)   # 某节点数据变化 (node_id)
    data_removed = Signal(str)   # 某节点缓存清理 (node_id)
```

**不包含** `selected_node_changed` —— 由 NodesPage 自行管理。

### 2.3 内部分组 + 外部扁平

```python
@dataclass
class IdentityData:
    node_id: str = ""
    alias: str = ""
    status: str = "unknown"
    ip: str = ""
    port: int = 0

@dataclass
class SystemData:
    hostname: str = "N/A"
    local_ip: str = "N/A"
    uptime: str = "N/A"

@dataclass
class CpuData:
    name: str = "N/A"
    usage: float = None          # None = 无数据（非 0）
    cores_phys: int = None
    cores_logic: int = None
    freq_mhz: float = None
    temp_c: float = None
    power_w: float = None

@dataclass
class MemoryData:
    total_gb: float = None
    used_gb: float = None
    avail_gb: float = None
    usage: float = None
    swap_mb: float = None

@dataclass
class GpuData:
    name: str = "N/A"
    usage: float = None
    vram_used: float = None
    vram_total: float = None
    core_temp: float = None
    hotspot_temp: float = None
    freq_mhz: float = None
    power_w: float = None

@dataclass
class DiskData:
    drive: str = "N/A"
    read_mb_s: float = None
    write_mb_s: float = None
    usage: float = None
    free_gb: float = None
    all_disks: list = field(default_factory=list)

@dataclass
class NetworkData:
    iface: str = "N/A"
    up_mb_s: float = None
    down_mb_s: float = None
    link_speed: float = None

@dataclass
class QualityData:
    rtt: float = None
    gw_rtt: float = None
    loss: float = None
    score: int = None
    grade: str = "N/A"

@dataclass
class FpsData:
    window: str = "N/A"
    value: float = None
    frame_time: float = None
    low1: float = None
    source: str = "N/A"

@dataclass
class ProcessData:
    cpu_text: str = "N/A"
    gpu_text: str = "N/A"

@dataclass
class NodeDetailData:
    identity: IdentityData
    system: SystemData
    cpu: CpuData
    memory: MemoryData
    gpu: GpuData
    disk: DiskData
    network: NetworkData
    quality: QualityData
    fps: FpsData
    processes: ProcessData

    def to_dict(self) -> dict:
        """扁平化输出，供 UI 消费。"""
        d = {}
        for group in (self.identity, self.system, self.cpu, self.memory,
                      self.gpu, self.disk, self.network, self.quality,
                      self.fps, self.processes):
            prefix = group.__class__.__name__.lower().replace("data", "")
            for k, v in group.__dict__.items():
                d[f"{prefix}_{k}" if prefix else k] = v
        return d
```

### 2.4 VM 方法

```python
class NodeDetailViewModel:
    def __init__(self, node_store, frame_store):
        self._node_store = node_store
        self._frame_store = frame_store
        self._cache: dict[str, NodeDetailData] = {}  # 每节点缓存

    # 查询（NodesPage 调用）
    def get_data(self, node_id: str) -> NodeDetailData | None
    def get_summary(self, node_id: str) -> dict  # 兼容旧 get_summary()

    # 信号
    data_updated = Signal(str)   # node_id
    data_removed = Signal(str)   # node_id
```

**关键**：`get_data(node_id)` 接受 node_id 参数，VM 不保存 current_node。

### 2.5 缓存策略

```
FrameStore.frame_updated(node_id, frame)
  -> 检查 _cache[node_id] 是否存在
  -> 存在：更新对应分组字段
  -> 不存在：构造新的 NodeDetailData
  -> emit data_updated(node_id)

NodeStore.node_removed(node_id)
  -> del _cache[node_id]
  -> emit data_removed(node_id)
```

### 2.6 空数据处理

字段缺失时使用 `None`（非 0），UI 层判断 None 显示 "N/A"。

```python
# 正确：
gpu.usage = None    # 无 GPU 数据

# 错误：
gpu.usage = 0.0     # UI 会误认为 GPU 空闲
```

### 2.7 与 DetailPanel 的关系

**不重写 DetailPanel**。渐进迁移：

| 阶段 | DetailPanel | NodeDetailViewModel |
|------|-------------|---------------------|
| 当前 | update_all(frame) 直接读帧 | 不存在 |
| 3-3B | NodesPage 同时注入 VM + DetailPanel | VM 输出 NodeDetailData |
| 3-3C | DetailPanel 改为读 NodeDetailData | VM 唯一数据源 |
| 最终 | DetailPanel 成为纯 UI 组件 | VM 唯一数据源 |

---

## 三、字段映射（43/43 覆盖）

| monitor_data 路径 | NodeDetailData 字段 | 转换 |
|-------------------|---------------------|------|
| system.hostname | system.hostname | str |
| system.local_ip | system.local_ip | str |
| system.uptime_seconds | system.uptime | format_uptime() |
| cpu.name | cpu.name | str |
| cpu.total_usage | cpu.usage | float or None |
| cpu.physical_cores | cpu.cores_phys | int or None |
| cpu.logical_cores | cpu.cores_logic | int or None |
| cpu.core_freq_mhz | cpu.freq_mhz | float or None |
| cpu.package_temp_c | cpu.temp_c | float or None |
| cpu.power_w | cpu.power_w | float or None |
| ram.total_gb | memory.total_gb | float or None |
| ram.used_gb | memory.used_gb | float or None |
| ram.available_gb | memory.avail_gb | float or None |
| ram.usage_percent | memory.usage | float or None |
| ram.swap_used_mb | memory.swap_mb | float or None |
| gpu.name | gpu.name | str |
| gpu.usage_percent | gpu.usage | float or None |
| gpu.vram_used_mb | gpu.vram_used | float or None |
| gpu.vram_total_mb | gpu.vram_total | float or None |
| gpu.core_temp_c | gpu.core_temp | float or None |
| gpu.hotspot_temp_c | gpu.hotspot_temp | float or None |
| gpu.core_freq_mhz | gpu.freq_mhz | float or None |
| gpu.power_w | gpu.power_w | float or None |
| disk[0].drive | disk.drive | str |
| disk[0].read_mb_s | disk.read_mb_s | float or None |
| disk[0].write_mb_s | disk.write_mb_s | float or None |
| disk[0].usage_percent | disk.usage | float or None |
| disk[0].free_gb | disk.free_gb | float or None |
| disk[] | disk.all_disks | list |
| net.interface | network.iface | str |
| net.upload_mb_s | network.up_mb_s | float or None |
| net.download_mb_s | network.down_mb_s | float or None |
| net.link_speed_mbps | network.link_speed | float or None |
| net_quality.latency_to_client_ms | quality.rtt | float or None |
| net_quality.latency_to_gateway_ms | quality.gw_rtt | float or None |
| net_quality.packet_loss_percent | quality.loss | float or None |
| net_quality.quality_score | quality.score | int or None |
| net_quality.quality_grade | quality.grade | str |
| fps.window_title | fps.window | str |
| fps.fps | fps.value | float or None |
| fps.frame_time_ms | fps.frame_time | float or None |
| fps.low_1_percent | fps.low1 | float or None |
| fps.source | fps.source | str |
| processes.top_cpu | processes.cpu_text | 格式化字符串 |
| processes.top_gpu | processes.gpu_text | 格式化字符串 |

---

## 四、测试重点

### 4.1 字段映射测试

构造完整 monitor_data 帧 -> VM 转换 -> NodeDetailData 43 字段逐一验证。

### 4.2 节点隔离测试

```
node_A cpu=20, node_B cpu=80
VM.update(node_A, frame_A)
检查: node_A.cpu.usage=20, node_B.cpu.usage=80 (不受影响)
```

### 4.3 空数据测试

```
帧无 gpu 字段 -> gpu.usage=None (非 0.0)
帧无 fps 字段 -> fps.value=None (非 0.0)
新节点无任何帧 -> 所有字段 None/"N/A"
```

### 4.4 删除测试

```
NodeStore.remove(node_A)
  -> VM._cache 删除 node_A
  -> data_removed.emit("node_A")
  -> get_data("node_A") 返回 None
```

### 4.5 缓存测试

```
push frame -> cache 创建
push 同节点 frame -> cache 更新（不新建）
push 不同节点 -> 各自独立缓存
```

---

## 五、变色规则（UI 层）

| 颜色模式 | NodeDetailData 字段 | 阈值 |
|----------|---------------------|------|
| usage_color | cpu.usage | 80/95 |
| usage_color | memory.usage | 80/90 |
| usage_color | gpu.usage | 80/95 |
| temp_color | cpu.temp_c | 80/85 |
| temp_color | gpu.core_temp | 80/85 |
| temp_color | gpu.hotspot_temp | 95/105 |
| score_color | quality.score | 60/80 |
| rtt_color | quality.rtt | 5/20 |
| rtt_color | quality.gw_rtt | 5/20 |

变色逻辑保留在 UI 层，ViewModel 只提供原始数值。

---

## 六、与现有 Store 接口

| Store | 方法 | 用途 |
|-------|------|------|
| NodeStore | get(node_id) | 节点元数据（alias, ip, port） |
| NodeStore | get_status(node_id) | 连接状态 |
| NodeStore | get_score(node_id) | 评分 (score, grade) |
| FrameStore | get(node_id) | 最新帧 |
| FrameStore | get_metric(node_id, path) | 按路径提取单指标 |

HistoryStore **不在此 VM 中使用**。趋势数据由 MonitorPage 直接读取。

---

## 七、迁移路径

### Phase 3-3A（当前）
- 创建 NodeDetailViewModel + NodeDetailData（内部分组 + to_dict 扁平化）
- 缓存策略：每节点 NodeDetailData
- 单元测试：字段映射 / 节点隔离 / 空数据 / 删除

### Phase 3-3B
- NodesPage 组合：NodeList + DetailPanel + NodeDetailViewModel
- NodeList 从 VM.get_summary() 读取摘要
- DetailPanel 仍用 update_all(frame)（暂不改动）

### Phase 3-3C
- DetailPanel 改为读 NodeDetailData
- VM 成为 DetailPanel 唯一数据源

### Phase 3-3D
- 删除 DetailPanel 中的旧数据读取逻辑
- DetailPanel 成为纯 UI 组件
