# 数据流说明

> **Version**: v5.2
> **Status**: CURRENT

## 1. 完整数据路径

```
Agent (采集器线程池, 每秒)
  ↓ get()
Aggregator (组装 monitor_data 帧)
  ↓ 最新帧缓存
WebSocket Server (广播给所有订阅者)
  ↓ 每秒推送
Host NodeConnection (WS 线程)
  ↓ data_received.emit(frame, node_id)
DataController._on_data() (主线程 slot)
  ↓
  ├── FrameStore.push(node_id, frame)     → 更新最新帧
  ├── HistoryStore.push(node_id, frame)   → 追加历史
  ├── NodeStore.update_status()           → 更新状态
  ├── AlertService._on_frame()            → 告警检测
  └── DashboardVM.data_changed.emit()     → 通知页面
        ↓
Page._refresh() (从 VM 获取数据, 渲染 Widget)
```

## 2. Signal 流

### 连接建立

```
DiscoveryService → DataController.on_node_added()
  → NodeStore.add_node()
  → NodeConnection.connect()
  → SideNav.add_node()
```

### 数据到达

```
NodeConnection.data_received(frame, node_id)
  → DataController._on_data()
    → FrameStore.push()
    → HistoryStore.push()
    → DashboardVM.data_changed.emit(node_id)
    → MonitorVM.data_changed.emit(node_id)
    → AlertService._on_frame()
```

### 状态变化

```
NodeConnection.status_changed(status, node_id)
  → DataController._on_status()
    → NodeStore.update_status()
    → SideNav.update_node_status()
    → MainWindow.statusBar().showMessage()
```

## 3. Store 刷新机制

| Store | 写入时机 | 读取方式 | 容量 |
|-------|----------|----------|------|
| FrameStore | 每帧到达 | VM.get_data() | 无限 |
| NodeStore | 节点增删 | VM.get_summary() | 无限 |
| HistoryStore | 每帧到达 | VM.get_history() | maxlen=300 |
| AlertStore | 告警触发 | VM.get_alerts() | 30s 去重 |

## 4. ViewModel 数据转换

```
Store (原始数据)
  ↓ VM.get_xxx()
Page (渲染数据)
  ↓ Widget.update()
UI (显示)
```

### DashboardViewModel

```python
def get_node_cards(self) -> list[NodeCardData]:
    """从 FrameStore 提取所有节点的卡片数据"""
    for node_id in self._node_store.node_ids():
        frame = self._frame_store.get(node_id)
        # 提取 CPU/GPU/RAM/Network/FPS/Score
        yield NodeCardData(...)
```

### MonitorViewModel

```python
def get_history(self, node_id, metric) -> list[ChartPoint]:
    """从 HistoryStore 提取图表数据点"""
    raw = self._history_store.query(node_id, metric)
    return [ChartPoint(ts, val) for ts, val in raw]
```

## 5. 不使用 QTimer

所有数据更新由 Signal 驱动：

- ✅ `data_received` → 立即更新
- ✅ `data_changed` → 立即刷新
- ❌ 不用 QTimer 轮询
- ❌ 不用定时器刷新

数据到达即更新，零延迟。
