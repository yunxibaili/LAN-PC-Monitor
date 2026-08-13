# Phase 3-5：MonitorPage 设计文档

> **Status**: COMPLETE
> **Date**: 2026-08-12
> **Result**: MonitorPage + MonitorViewModel 实现完成，46+21 项测试全通过
> **Implementation**: `host/gui/pages/monitor_page.py`, `host/viewmodels/monitor_vm.py`
> **Tests**: `test_v52_monitor_vm.py`, `test_v52_monitor_page.py`

## 一、历史趋势数据源分析

### 1.1 HistoryStore 已实现接口

| 方法 | 用途 |
|------|------|
| `query(node_id, metric, limit)` | 返回 `[(ts, value), ...]`，最近优先 |
| `get_history(node_id, metric, limit)` | query 别名 |
| `last(node_id, metric)` | 最近一个点的 value |
| `metrics(node_id)` | 该节点已有指标名列表 |
| `node_count()` | 节点总数 |
| `point_count()` | 全部点数 |
| `push_frame(node_id, frame)` | 从帧批量写入（cpu/gpu/ram/fps/score/net_up/net_down） |

### 1.2 HistoryStore 数据结构

```
_data = defaultdict(lambda: defaultdict(lambda: deque(maxlen=300)))
# node_id -> { metric -> deque[(timestamp, value)] }
```

### 1.3 已有指标名（push_frame 提取器）

| metric key | frame 路径 | 说明 |
|------------|-----------|------|
| `cpu` | cpu.total_usage | CPU 使用率 |
| `gpu` | gpu.usage_percent | GPU 使用率 |
| `ram` | ram.usage_percent | 内存使用率 |
| `fps` | fps.fps | 帧率 |
| `score` | net_quality.quality_score | 网络评分 |
| `net_up` | net.upload_mb_s | 上传速度 |
| `net_down` | net.download_mb_s | 下载速度 |

### 1.4 MainWindow 写入点

```python
# MainWindow._on_data() L752
self.history_store.push_frame(node_id, frame)  # 每秒写入
```

### 1.5 关键约束

- MainWindow **不直接读取** history_store.query()（Monitor 专属）
- HistoryStore 的信号（point_added/node_removed/reset）已定义但 MainWindow 未连接
- maxlen=300 → 约 5 分钟 @1s

---

## 二、MonitorViewModel 设计

### 2.1 职责

MonitorViewModel 是 MonitorPage 与 HistoryStore 之间的数据层：
- 订阅 HistoryStore 信号（point_added, node_removed）
- 按节点+指标提取历史数据
- 提供指标列表查询
- 不持有 UI 状态，不做轮询

### 2.2 数据结构

```python
@dataclass
class ChartPoint:
    timestamp: float
    value: float

@dataclass
class MetricSeries:
    node_id: str
    metric: str
    points: list  # list[ChartPoint]
```

### 2.3 信号

```python
class MonitorViewModel:
    data_changed = Signal(str)   # node_id（某节点数据变化）
```

### 2.4 方法

```python
class MonitorViewModel:
    def __init__(self, history_store, node_store):
        """
        :param history_store: HistoryStore 实例
        :param node_store: NodeStore 实例（查询节点元数据）
        """

    # 查询
    def get_history(self, node_id: str, metric: str,
                    limit: int | None = None) -> list[ChartPoint]
    def get_available_metrics(self, node_id: str) -> list[str]
    def get_node_ids(self) -> list[str]
    def get_summary(self, node_id: str) -> dict

    # 刷新
    def refresh(self, node_id: str | None = None) -> None
```

### 2.5 支持指标映射

| metric key | 中文显示名 | 单位 | Y 轴范围 |
|------------|-----------|------|----------|
| `cpu` | CPU 使用率 | % | 0-100 |
| `gpu` | GPU 使用率 | % | 0-100 |
| `ram` | 内存使用率 | % | 0-100 |
| `net_up` | 上传速度 | MB/s | auto |
| `net_down` | 下载速度 | MB/s | auto |
| `score` | 网络评分 | — | 0-100 |
| `rtt` | RTT | ms | auto |
| `loss` | 丢包率 | % | 0-100 |

**注意**：rtt 和 loss 在 HistoryStore 中未自动写入（push_frame 不包含）。MonitorPage 需要通过 MainWindow 或 NodeStore 获取。v5.2 第一版暂不包含 rtt/loss，仅使用 push_frame 已有的 7 个指标。

### 2.6 信号流

```
HistoryStore.push_frame(node_id, frame, ts)
  → point_added(node_id, metric, value)
  → MonitorViewModel._on_point_added(node_id, metric)
  → data_changed.emit(node_id)

HistoryStore.node_removed(node_id)
  → MonitorViewModel._on_node_removed(node_id)
  → data_changed.emit(node_id)
```

### 2.7 数据转换

```python
def get_history(self, node_id, metric, limit=None):
    raw = self._history_store.query(node_id, metric, limit)
    return [ChartPoint(timestamp=ts, value=val) for ts, val in raw]
```

---

## 三、MonitorPage UI 设计

### 3.1 页面结构

```
MonitorPage(PageBase)
├── headerRow: QHBoxLayout
│   ├── backBtn: QPushButton("← 返回总览")
│   ├── title: QLabel("📈 监控 — {node_alias}")
│   ├── statusBadge: QLabel("● 已连接")
│   └── stretch
│
├── metricSelector: QScrollArea (horizontal)
│   └── metricButtons: [QPushButton("CPU"), QPushButton("GPU"), ...]
│
└── chartArea: QStackedWidget
    └── [0] chartWidget: ChartWidget (pyqtgraph)
```

### 3.2 数据更新路径

```
MonitorViewModel.data_changed(node_id)
  → MonitorPage._on_data_changed(node_id)
  → if node_id == current_node:
      _refresh_chart()
        → data = vm.get_history(node_id, current_metric, limit=300)
        → chart_widget.set_series(data)
```

### 3.3 生命周期

```
on_show():
    vm.data_changed.connect(self._on_data_changed)
    self._refresh_chart()

on_hide():
    vm.data_changed.disconnect(self._on_data_changed)

set_node(node_id):
    self._current_node = node_id
    self._update_title()
    self._refresh_chart()
```

### 3.4 指标选择

点击指标按钮 → 切换 current_metric → 刷新图表。

---

## 四、ChartWidget 设计

### 4.1 接口

```python
class ChartWidget(QWidget):
    """纯 UI 组件：接收 ChartPoint 列表并渲染折线图。"""

    def __init__(self, title: str = "", y_range: tuple = (0, 100))
    def set_series(self, points: list[ChartPoint], color: str = "#007acc")
    def clear(self)
```

### 4.2 内部结构

```
ChartWidget(QWidget)
├── titleLabel: QLabel (指标名称)
├── plotWidget: pg.PlotWidget (pyqtgraph)
│   ├── plotCurve (蓝色折线)
│   ├── thresholdLine1 (橙色虚线, 80%)
│   └── thresholdLine2 (红色虚线, 95%)
└── valueLabel: QLabel (最新值)
```

### 4.3 阈值配置

| 指标 | warn 阈值 | danger 阈值 |
|------|----------|------------|
| cpu/gpu/ram | 80 | 95 |
| net_up/net_down | — | — |
| score | 60 | — |

### 4.4 禁止

- 不访问 HistoryStore
- 不访问 FrameStore
- 不访问 NodeStore
- 纯接收 set_series(points) 渲染

---

## 五、节点切换流程

```
用户在 NodesPage/SideNav 点击节点
  → MainWindow._on_nav_node_clicked(node_id)
  → MonitorPage.set_node(node_id)
  → _refresh_chart()
    → data = vm.get_history(node_id, current_metric)
    → chart_widget.set_series(data)
```

---

## 六、异常设计

### 6.1 无历史数据

```
vm.get_history() 返回 []
  → chart_widget.clear()
  → 显示 "暂无历史数据"
```

### 6.2 节点不存在

```
vm.get_history("nonexistent", ...) 返回 []
  → 图表清空
```

### 6.3 指标无数据

```
vm.get_history("node-A", "fps") 返回 []
  → 图表清空（该指标在 HistoryStore 中无点）
```

---

## 七、测试规划

### 7.1 MonitorViewModel 测试 (test_v52_monitor_vm.py)

| 用例 | 验证 |
|------|------|
| get_history 基本 | push 后 query 返回 ChartPoint 列表 |
| get_available_metrics | push_frame 后返回 ["cpu","gpu",...] |
| get_node_ids | 多节点 push 后返回正确列表 |
| 空数据 | 无 push 时返回 [] |
| refresh | 调用后 data_changed 信号触发 |
| 多节点隔离 | node_A 数据不影响 node_B |
| 指标过滤 | query("A","cpu") 只返回 cpu 数据 |

### 7.2 ChartWidget 测试 (test_v52_chart_widget.py)

| 用例 | 验证 |
|------|------|
| set_series | 创建曲线，验证点数 |
| clear | 清空后无曲线 |
| 空 points | set_series([]) 不崩溃 |
| 阈值线 | 创建后可见 |

### 7.3 MonitorPage 测试 (test_v52_monitor_page.py)

| 用例 | 验证 |
|------|------|
| VM 注入 | set_view_model 正常 |
| set_node | 更新 current_node |
| 生命周期 | on_show/on_hide 不崩溃 |
| 源码扫描 | 无 HistoryStore/FrameStore/NodeConnection/QTimer import |

---

## 八、迁移步骤

### Phase 3-5A（当前）
- 生成设计文档
- 确认 HistoryStore 接口完整

### Phase 3-5B
- 新增 host/viewmodels/monitor_vm.py
- MonitorViewModel + ChartPoint + MetricSeries
- 单元测试：test_v52_monitor_vm.py

### Phase 3-5C
- 新增 host/gui/widgets/chart_widget.py
- 基于 pyqtgraph 的折线图
- 单元测试：test_v52_chart_widget.py

### Phase 3-5D
- 重写 host/gui/pages/monitor_page.py
- 组合 MonitorViewModel + ChartWidget
- MainWindow 集成：set_node → VM.refresh
- 单元测试：test_v52_monitor_page.py
- 全量回归

---

## 九、禁止事项

| 禁止项 | 原因 |
|--------|------|
| MonitorPage 访问 FrameStore | 趋势数据由 HistoryStore 提供 |
| MonitorPage 访问 NodeConnection | 不涉及通信 |
| MonitorViewModel 访问 FrameStore | 仅通过 HistoryStore |
| 引入 QTimer | Signal 驱动架构 |
| 修改 HistoryStore | Phase 0 已完成 |
| 修改 HistoryStore.push_frame | 保持已有 7 个指标 |

---

## 十、与现有模块的兼容

### HistoryStore 不变

push_frame 保持现有 7 个指标提取器不变。rtt/loss 暂不支持（push_frame 未写入），v6 可扩展。

### MainWindow 不变

_history_store.push_frame() 和 _history_store.remove_node() 已在 _on_data() 和 _remove_node() 中调用。MonitorPage 通过 set_stores(history=self.history_store) 获取引用。

### NodeDetailViewModel 不变

HistoryStore 分离设计已实现（DetailVM 只管实时状态），MonitorPage 通过独立的 MonitorVM 访问历史数据。
