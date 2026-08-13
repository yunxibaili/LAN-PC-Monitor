# Phase 3-3C：DetailPanel 数据解耦设计文档

> **Status**: COMPLETE
> **Date**: 2026-08-11
> **Result**: DetailPanel 数据解耦完成，48 项测试全通过
> **Implementation**: `host/gui/widgets/detail_panel.py`
> **Tests**: `test_v52_detail_panel.py`

## 一、当前 DetailPanel 分析

### 1.1 类结构

```
DetailPanel(QScrollArea)
├── __init__()
├── _build_ui()              # 构建布局
├── _make_group(title, fields)  # 创建 QGroupBox + 字段标签
├── update_all(frame: dict)  # 数据更新入口（v5.1 核心方法）
├── get_summary(frame: dict) # 提取摘要（供 OverviewGrid/NodeList）
├── _update_header(frame)    # 更新顶部标题
├── _update_group(data, labels, **modes)  # 通用字段更新 + 变色
├── _update_disk(disks, labels)   # 磁盘特殊处理
└── _update_proc(processes, labels) # 进程特殊处理
```

### 1.2 UI 组件

| 组件 | 类型 | 数量 | 说明 |
|------|------|------|------|
| header_label | QLabel | 1 | 顶部标题（主机名/IP/运行时间） |
| _panels[title] | dict | 8 | (QGroupBox, {field_key: QLabel}) |
| 各字段 QLabel | QLabel | ~40 | 数据值显示（变色） |
| _PANEL_FIELDS | list | 8组 | 字段映射配置表 |

### 1.3 数据解析位置

**问题核心**：`update_all(frame)` 同时做：
1. 数据提取：`frame.get("cpu", {})` → 字段值
2. 格式化：`_fmt(value)` → 字符串
3. 变色判定：`_color_for(key, value, **modes)` → 颜色
4. UI 渲染：`label.setText()` / `apply_color(label, color)`

**数据解析与 UI 渲染完全耦合在一个方法内。**

### 1.4 耦合点

| 耦合 | 位置 | 说明 |
|------|------|------|
| update_all 做数据提取 | L109-135 | `frame.get("cpu", {})` 直接从 dict 取值 |
| _update_group 做变色 | L144-150 | `_color_for(key, value)` 含业务阈值逻辑 |
| get_summary 做数据提取 | L178-195 | `cpu.get("total_usage")` 等直接从 dict 取值 |
| 隐式依赖 frame 结构 | 全局 | 字段名与 monitor_data 协议强绑定 |

---

## 二、迁移目标

### 目标架构

```
FrameStore
  │  frame_updated(node_id, frame)
  ▼
NodeDetailViewModel
  │  _build_detail_data(node_id, frame)
  │  → NodeDetailData (内部分组 + to_dict)
  ▼
DetailPanel
  │  update_data(data: NodeDetailData)
  │  → 子组件更新
  ▼
QLabel / QGroupBox
```

### DetailPanel 约束

| 项目 | 约束 |
|------|------|
| 禁止访问 Store | DetailPanel 不 import FrameStore / NodeStore |
| 禁止解析 monitor_data | 不调用 frame.get("cpu", {}) |
| 禁止保存 node_id | 不持有 _current_node |
| 禁止 QTimer | 纯被动接收数据 |
| 允许的输入 | `update_data(data: NodeDetailData)` |
| 允许的内部逻辑 | 变色判定（阈值常量）、字符串格式化 |

---

## 三、DetailPanel 新接口设计

### 3.1 新方法

```python
def update_data(self, data: NodeDetailData) -> None:
    """用 NodeDetailData 更新整个面板（替代 update_all(frame)）。"""
    self._update_header_from_data(data)
    # 遍历各子组件更新
    for panel_name, widget in self._panels.items():
        widget.update_from_data(data)
```

### 3.2 旧方法保留（兼容期）

```python
def update_all(self, frame: dict) -> None:
    """v5.1 兼容接口。Phase 3-3D 删除。"""
    # 转发给内部子组件
    for panel_name, widget in self._panels.items():
        widget.update_from_frame(frame)
```

### 3.3 迁移策略

| Phase | DetailPanel 方法 | 状态 |
|-------|-----------------|------|
| 3-3A 当前 | update_all(frame) | v5.1 原始 |
| 3-3C Phase A | +update_data(NodeDetailData) | 新增 |
| 3-3C Phase B | NodesPage 调用 update_data | 切换数据源 |
| 3-3C Phase C | update_all 标记 @deprecated | 标记废弃 |
| 3-3D | 删除 update_all | 彻底移除 |

---

## 四、组件拆分设计

### 4.1 当前 _PANEL_FIELDS 映射

| 分组 | 数据类字段 | UI 子组件 |
|------|-----------|-----------|
| cpu.group | CpuData | DetailCpuWidget |
| ram.group | MemoryData | DetailMemoryWidget |
| gpu.group | GpuData | DetailGpuWidget |
| disk.group | DiskData | DetailDiskWidget |
| net.group | NetworkData | DetailNetworkWidget |
| netq.group | QualityData | DetailQualityWidget |
| fps.group | FpsData | DetailFpsWidget |
| proc.group | ProcessData | DetailProcessWidget |

### 4.2 子组件接口

```python
class DetailSectionWidget(QWidget):
    """详情面板子组件基类。"""

    def update_from_data(self, data: NodeDetailData) -> None:
        """从 NodeDetailData 更新显示。"""
        raise NotImplementedError

    def update_from_frame(self, frame: dict) -> None:
        """v5.1 兼容：从原始帧更新。Phase 3-3D 删除。"""
        raise NotImplementedError

    def clear(self) -> None:
        """清空所有字段显示。"""
        raise NotImplementedError
```

### 4.3 各子组件设计

#### DetailHeaderWidget

```
输入: data.identity + data.system
显示: hostname | local_ip | uptime
更新: update_from_data(data) → header_label.setText(...)
```

#### DetailCpuWidget

```
输入: data.cpu
显示:
  CPU 型号: name
  使用率:   usage %   (usage_color 80/95)
  物理核心: cores_phys
  逻辑核心: cores_logic
  频率:     freq_mhz MHz
  温度:     temp_c °C  (temp_color 80/85)
  功耗:     power_w W
更新: update_from_data(data) → 逐字段 setText + apply_color
```

#### DetailMemoryWidget

```
输入: data.memory
显示:
  总计: total_gb GB
  已用: used_gb GB   (usage_color 80/90)
  可用: avail_gb GB
  使用率: usage %    (usage_color 80/90)
  Swap: swap_mb MB
更新: update_from_data(data) → 逐字段 setText + apply_color
```

#### DetailGpuWidget

```
输入: data.gpu
显示:
  GPU 型号: name
  使用率:   usage %   (usage_color 80/95)
  显存:     vram_used / vram_total MB
  核心温度: core_temp °C  (temp_color 80/85)
  热点温度: hotspot_temp °C (temp_color 95/105)
  核心频率: freq_mhz MHz
  功耗:     power_w W
更新: update_from_data(data) → 逐字段 setText + apply_color
```

#### DetailDiskWidget

```
输入: data.disk
显示:
  盘符: drive
  读取: read_mb_s MB/s
  写入: write_mb_s MB/s
  使用率: usage %  (usage_color 85/95)
  剩余: free_gb GB
  多盘提示: tooltip (disk.all_disks)
更新: update_from_data(data) → 逐字段 setText + apply_color
```

#### DetailNetworkWidget

```
输入: data.network
显示:
  网卡: iface
  上行: up_mb_s MB/s
  下行: down_mb_s MB/s
  链路: link_speed Mbps
更新: update_from_data(data) → 逐字段 setText
```

#### DetailQualityWidget

```
输入: data.quality
显示:
  RTT:    rtt ms       (rtt_color 5/20)
  网关RTT: gw_rtt ms  (rtt_color 5/20)
  丢包:   loss %
  评分:   score        (score_color 60/80)
  等级:   grade
更新: update_from_data(data) → 逐字段 setText + apply_color
```

#### DetailFpsWidget

```
输入: data.fps
显示:
  窗口: window
  FPS:  value
  帧时间: frame_time ms
  1%Low: low1
  来源: source
更新: update_from_data(data) → 逐字段 setText
```

#### DetailProcessWidget

```
输入: data.processes
显示:
  CPU Top: cpu_text (多行)
  GPU Top: gpu_text (多行)
更新: update_from_data(data) → setText
```

---

## 五、NodeDetailData 字段映射

### 5.1 NodeDetailData → DetailPanel 完整映射

| NodeDetailData 字段 | UI 组件 | 显示内容 | 变色 |
|---------------------|---------|----------|------|
| identity.node_id | header | （不直接显示） | - |
| identity.alias | header | 标题前缀 | - |
| identity.status | header | 状态文字 | - |
| system.hostname | header | hostname | - |
| system.local_ip | header | local_ip | - |
| system.uptime | header | 运行时间 | - |
| cpu.name | CpuWidget | 型号 | - |
| cpu.usage | CpuWidget | 使用率% | usage_color(80/95) |
| cpu.cores_phys | CpuWidget | 物理核心数 | - |
| cpu.cores_logic | CpuWidget | 逻辑核心数 | - |
| cpu.freq_mhz | CpuWidget | 频率 MHz | - |
| cpu.temp_c | CpuWidget | 温度°C | temp_color(80/85) |
| cpu.power_w | CpuWidget | 功耗 W | - |
| memory.total_gb | MemWidget | 总计 GB | - |
| memory.used_gb | MemWidget | 已用 GB | usage_color(80/90) |
| memory.avail_gb | MemWidget | 可用 GB | - |
| memory.usage | MemWidget | 使用率% | usage_color(80/90) |
| memory.swap_mb | MemWidget | Swap MB | - |
| gpu.name | GpuWidget | 型号 | - |
| gpu.usage | GpuWidget | 使用率% | usage_color(80/95) |
| gpu.vram_used | GpuWidget | 显存已用 MB | - |
| gpu.vram_total | GpuWidget | 显存总计 MB | - |
| gpu.core_temp | GpuWidget | 核心温度°C | temp_color(80/85) |
| gpu.hotspot_temp | GpuWidget | 热点温度°C | temp_color(95/105) |
| gpu.freq_mhz | GpuWidget | 频率 MHz | - |
| gpu.power_w | GpuWidget | 功耗 W | - |
| disk.drive | DiskWidget | 盘符 | - |
| disk.read_mb_s | DiskWidget | 读取 MB/s | - |
| disk.write_mb_s | DiskWidget | 写入 MB/s | - |
| disk.usage | DiskWidget | 使用率% | usage_color(85/95) |
| disk.free_gb | DiskWidget | 剩余 GB | - |
| disk.all_disks | DiskWidget | tooltip | - |
| network.iface | NetWidget | 网卡名 | - |
| network.up_mb_s | NetWidget | 上行 MB/s | - |
| network.down_mb_s | NetWidget | 下行 MB/s | - |
| network.link_speed | NetWidget | 链路 Mbps | - |
| quality.rtt | QualityWidget | RTT ms | rtt_color(5/20) |
| quality.gw_rtt | QualityWidget | 网关 RTT ms | rtt_color(5/20) |
| quality.loss | QualityWidget | 丢包% | - |
| quality.score | QualityWidget | 评分 | score_color(60/80) |
| quality.grade | QualityWidget | 等级 | - |
| fps.window | FpsWidget | 窗口标题 | - |
| fps.value | FpsWidget | FPS | - |
| fps.frame_time | FpsWidget | 帧时间 ms | - |
| fps.low1 | FpsWidget | 1% Low | - |
| fps.source | FpsWidget | 来源 | - |
| processes.cpu_text | ProcWidget | CPU Top | - |
| processes.gpu_text | ProcWidget | GPU Top | - |

### 5.2 覆盖率

**43/43 字段 100% 覆盖**（含 identity 3 字段 + system 3 字段 + 8 个数据组 37 字段）。

---

## 六、节点切换流程

### 6.1 当前流程（v5.1）

```
NodeList 选中节点
  → MainWindow._on_node_selected()
  → frame = self.frames[node_id]
  → detail_panel.update_all(frame)
```

### 6.2 目标流程（v5.2）

```
NodeList 选中节点
  → NodesPage._on_node_selected()
  → current_node_id = node_id
  → _refresh_detail()
      → data = node_detail_vm.get_data(node_id)
      → detail_panel.update_data(data)     # 新接口
      → header_label.setText(...)          # 顶部状态
```

### 6.3 数据流路径

```
NodeConnection → MainWindow._on_data → FrameStore.push
  → NodeDetailViewModel._on_frame_updated → 缓存 NodeDetailData
  → NodesPage._refresh_detail → NodeDetailViewModel.get_data(node_id)
  → DetailPanel.update_data(NodeDetailData)
```

---

## 七、生命周期设计

### 7.1 NodesPage 生命周期

```python
def on_show(self):
    """页面显示时刷新。"""
    self._node_detail_vm.refresh_all()  # 重建缓存
    self._refresh_detail()              # 更新当前选中节点

def on_hide(self):
    """页面隐藏。"""
    pass  # 无需特殊操作
```

### 7.2 DetailPanel 生命周期

```
__init__()          → 构建 UI
update_data(data)   → 被动接收数据，刷新渲染
clear()             → 清空所有字段
```

DetailPanel 不主动拉取数据，不保存状态，不启动定时器。

---

## 八、异常设计

### 8.1 节点不存在

```
NodeDetailViewModel.get_data(node_id) → None
  → DetailPanel.clear()
  → 显示 "暂无数据"
```

### 8.2 帧为空

```
FrameStore.get(node_id) → None
  → NodeDetailViewModel 不生成 NodeDetailData
  → get_data 返回 None → DetailPanel.clear()
```

### 8.3 GPU 不存在

```
frame 无 "gpu" 字段
  → _build_detail_data 中 gpu = frame.get("gpu", {})
  → 所有 gpu.* 字段为 None
  → DetailGpuWidget.update_from_data() 显示 "N/A"
```

### 8.4 磁盘为空

```
frame["disk"] = []
  → disk.all_disks = []
  → disk.drive = "N/A"
  → DetailDiskWidget 显示 "无磁盘数据"
```

### 8.5 字段缺失

```
frame["cpu"]["total_usage"] 不存在
  → _safe_float(None) → None
  → cpu.usage = None
  → DetailCpuWidget 显示 "N/A"
```

---

## 九、测试设计

### 9.1 测试文件

`tests/test_v52_detail_panel.py`

### 9.2 测试用例

| 用例 | 验证点 |
|------|--------|
| NodeDetailData 输入 | update_data 正确刷新各子组件 |
| 空数据 | update_data(None) → clear() |
| GPU 不存在 | gpu.usage=None → 显示 N/A |
| 磁盘为空 | disk=[] → 显示 "无磁盘数据" |
| 字段缺失 | 部分字段 None → 正常显示其余字段 |
| 节点切换 | 两次 update_data → 值覆盖 |
| 变色正确 | cpu 90% → 红色，score 50 → 红色 |
| get_summary 兼容 | 返回 dict 格式与 v5.1 一致 |

### 9.3 禁止验证

| 禁止项 | 验证方式 |
|--------|----------|
| 访问 FrameStore | DetailPanel 无 import FrameStore |
| 访问 NodeStore | DetailPanel 无 import NodeStore |
| 访问 monitor_data | DetailPanel 无 frame.get() |
| QTimer | DetailPanel 无 QTimer 导入/使用 |

---

## 十、迁移步骤

### Phase A：新增 update_data()

1. DetailPanel 新增 `update_data(data: NodeDetailData)` 方法
2. 内部调用各子组件的 `update_from_data(data)`
3. 保留 `update_all(frame)` 不变
4. 新增 `clear()` 方法
5. 测试：test_v52_detail_panel.py 验证新接口

### Phase B：NodesPage 切换 VM 数据

1. NodesPage._refresh_detail() 改为调用 `detail_panel.update_data(data)`
2. 移除 `detail_panel.update_all(frame)` 调用
3. 测试：test_v52_nodes_page.py 仍通过

### Phase C：MainWindow 清理

1. MainWindow 中 `detail_panel.update_all(frame)` 调用改为 VM 路径
2. `detail_panel.get_summary(frame)` 改为 `vm.get_summary(node_id)`
3. 测试：test_p0/test_api 仍通过

### Phase D：删除旧方法

1. DetailPanel 删除 `update_all()` 方法
2. 删除 `_PANEL_FIELDS` 旧映射
3. 删除旧的 `_update_group`/`_update_disk`/`_update_proc`
4. 测试：所有测试仍通过

---

## 十一、禁止事项

| 禁止项 | 原因 |
|--------|------|
| 修改 connection.py / connection_core.py | v5.1 通信层稳定 |
| 修改 collectors | 采集层稳定 |
| 修改 AlertEngine | 告警逻辑稳定 |
| 修改 monitor_data 协议 | 多节点兼容约束 |
| 修改 REST API | 外部接口稳定 |
| 引入 QTimer | Signal 驱动架构约束 |
| 重新设计 Store | Phase 0 已完成 |

---

## 十二、风险与降级

### 风险 1：DetailPanel 变色逻辑迁移

**风险**：_color_for() 中的阈值判断依赖字段名（如 "total_usage"），迁移后字段名变为 NodeDetailData 的属性名。

**降级**：变色逻辑保留在各子组件中，使用 NodeDetailData 的属性名重写，不依赖旧字段名。

### 风险 2：OverviewGrid.get_summary 兼容

**风险**：OverviewGrid 消费的 summary dict 格式必须与 v5.1 一致。

**降级**：NodeDetailViewModel.get_summary() 已验证返回格式兼容。MainWindow._on_data 中 `detail_panel.get_summary(frame)` 改为 `vm.get_summary(node_id)` 即可。

### 风险 3：磁盘多盘处理

**风险**：DetailPanel._update_disk() 取 disk[0] 并设 tooltip。迁移后 DiskWidget 需同样处理。

**降级**：DiskWidget 接收 `data.disk`（含 all_disks），渲染逻辑与旧版一致。
