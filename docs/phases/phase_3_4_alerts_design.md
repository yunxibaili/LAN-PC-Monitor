# Phase 3-4：AlertsPage 设计文档

> **Status**: COMPLETE
> **Date**: 2026-08-11
> **Result**: AlertsPage + AlertViewModel 实现完成，30 项测试全通过
> **Implementation**: `host/gui/pages/alerts_page.py`, `host/viewmodels/alert_vm.py`
> **Tests**: `test_v52_alerts_page.py`, `test_v52_alert_vm.py`

## 一、现有 Alert 架构分析

### 1.1 数据流（已实现）

```
Agent/LocalNode → monitor_data → MainWindow._on_data
  → FrameStore.push → AlertService._on_frame (订阅触发)
    → AlertAdapter.evaluate(frame)
      → AlertEngine.check(frame) → hits[{name,path,value,level,threshold}]
      → 补充 timestamp/node_id/node_alias → AlertStore.push(alert)
        → 30s 窗口去重 → alert_added signal
          → MainWindow: 日志 + TrayManager 气泡
```

### 1.2 AlertStore 已有信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `alert_added` | `dict` | 新告警（含 8 字段） |
| `alert_cleared` | `str` (node_id) | 节点告警清空 |
| `count_changed` | `int` | 未恢复告警数变化 |
| `reset` | 无 | 整体重置 |

### 1.3 AlertStore 已有查询方法

| 方法 | 返回 |
|------|------|
| `alerts(limit)` | list[dict]（最新在前） |
| `active()` | list[dict]（未恢复） |
| `active_count()` | int |
| `red_count()` | int |
| `warn_count()` | int |
| `node_alerts(node_id)` | list[dict] |
| `summary()` | dict{red, warn, active, total} |

### 1.4 告警 dict 结构（8 字段）

```python
{
    "timestamp":  float,   # time.time()
    "node_id":    str,
    "node_alias": str,
    "name":       str,     # "CPU 使用率"
    "path":       str,     # "cpu.total_usage"
    "value":      Any,     # 当前值
    "threshold":  Any,     # 触发阈值
    "level":      str,     # "red" / "warn"
}
```

### 1.5 30s 去重语义

AlertStore.push() 内部：
```
key = (node_id, path)
last = _last_alert_ts.get(key)
if last and (now - last) < 30:
    return False  # 跳过
_last_alert_ts[key] = now
_alerts.append(alert)
_active[key] = alert
return True
```

- 同一节点同一指标 30s 内只记一次
- clear_node() 清空活动告警但保留去重时间戳（防瞬时抖动）
- reset_all() 清空全部（历史+去重+活动）

### 1.6 托盘联动

当前 MainWindow._on_alert_added() 调用：
- `self.alert_store.alert_added.connect(self._on_alert_added)` → 写日志 + TrayManager.show_message()

AlertsPage **不是告警产生者**——它只消费 AlertStore.alert_added 信号。

---

## 二、AlertViewModel 设计

### 2.1 职责

AlertViewModel 是 AlertsPage 与 AlertStore 之间的数据层：
- 订阅 AlertStore 信号（alert_added, alert_cleared, count_changed）
- 维护告警历史缓存（有序列表）
- 提供过滤/查询接口给 AlertsPage
- 不持有 UI 状态，不做轮询

### 2.2 信号

```python
class AlertViewModel:
    alerts_changed = Signal()    # 列表变化（增删/过滤条件变化）
    count_changed = Signal(int)  # 未恢复告警数变化（供 SideNav 徽标）
```

### 2.3 AlertItem 数据结构

```python
@dataclass
class AlertItem:
    node_id: str
    node_alias: str
    name: str
    path: str
    value: Any
    level: str       # "red" / "warn"
    threshold: Any
    timestamp: float

    def time_str(self) -> str:
        """格式化时间：HH:MM:SS"""
        ...

    def level_color(self) -> str:
        """level -> 颜色常量"""
        ...
```

### 2.4 方法

```python
class AlertViewModel:
    def __init__(self, alert_store):
        self._store = alert_store
        self._items = []       # AlertItem 列表（最新在前）
        self._filter_level = None   # None=全部, "red"/"warn"
        self._filter_node = None    # None=全部, node_id

    # 数据获取
    def get_items(self) -> list        # 当前过滤后的告警列表
    def get_count(self) -> int         # 未恢复告警总数
    def get_red_count(self) -> int     # 红色未恢复数
    def get_warn_count(self) -> int    # 橙色未恢复数
    def get_summary(self) -> dict      # {total, red, warn}

    # 过滤
    def set_filter_level(self, level) -> None  # None/"red"/"warn"
    def set_filter_node(self, node_id) -> None  # None/node_id
    def clear_filters(self) -> None

    # 操作
    def clear_node(self, node_id: str) -> None  # 清空节点告警
    def clear_all(self) -> None                  # 清空全部
```

### 2.5 数据转换

AlertStore.dict → AlertItem：
```python
def _to_item(self, alert: dict) -> AlertItem:
    return AlertItem(
        node_id=alert.get("node_id", ""),
        node_alias=alert.get("node_alias", ""),
        name=alert.get("name", ""),
        path=alert.get("path", ""),
        value=alert.get("value"),
        level=alert.get("level", "warn"),
        threshold=alert.get("threshold"),
        timestamp=alert.get("timestamp", 0),
    )
```

### 2.6 信号流

```
AlertStore.alert_added(dict)
  → AlertViewModel._on_alert_added(alert)
  → 转换为 AlertItem
  → 插入 self._items 列表（最新在前）
  → alerts_changed.emit()

AlertStore.count_changed(int)
  → AlertViewModel._on_count_changed(count)
  → count_changed.emit(count)  # 供 SideNav 徽标

AlertStore.alert_cleared(str)
  → AlertViewModel._on_node_cleared(node_id)
  → 移除该节点的所有 AlertItem
  → alerts_changed.emit()
```

---

## 三、AlertsPage UI 设计

### 3.1 页面结构

```
AlertsPage(PageBase)
├── headerRow: QHBoxLayout
│   ├── title: QLabel("告警中心")
│   ├── summaryCards: QHBoxLayout
│   │   ├── StatCard("当前告警", count, COLOR_ACCENT)
│   │   ├── StatCard("红色", red_count, COLOR_DANGER)
│   │   ├── StatCard("橙色", warn_count, COLOR_WARN)
│   │   └── StatCard("今日", today_count, COLOR_TEXT)
│   ├── stretch
│   └── clearBtn: QPushButton("清除全部")
│
├── filterBar: QHBoxLayout
│   ├── levelFilter: QComboBox("全部"/"仅红线"/"仅预警")
│   ├── nodeFilter: QComboBox("所有节点"/节点列表)
│   └── searchBox: QLineEdit(搜索告警名/路径)
│
└── alertTable: QTableWidget
    ├── 列: 时间 | 节点 | 类型 | 指标 | 当前值 | 阈值 | 等级
    └── 行高: 36px
```

### 3.2 数据更新路径

```
AlertViewModel.alerts_changed
  → AlertsPage._on_alerts_changed()
  → 重新填充 QTableWidget

AlertViewModel.count_changed
  → AlertsPage._on_count_changed()
  → 更新 summaryCards 数值
  → 通知 SideNav 徽标
```

### 3.3 过滤逻辑

```python
def _on_filter_changed(self):
    """下拉框或搜索框变化时调用。"""
    level = self._level_combo.currentData()
    node = self._node_combo.currentData()
    search = self._search_box.text().strip().lower()
    self._vm.set_filter_level(level)
    self._vm.set_filter_node(node)
    self._filter_search = search
    self._refresh_table()

def _refresh_table(self):
    """用 VM.get_items() 重新填充表格。"""
    items = self._vm.get_items()
    if self._filter_search:
        items = [i for i in items if self._filter_search in i.name.lower()
                 or self._filter_search in i.path.lower()
                 or self._filter_search in i.node_alias.lower()]
    self._populate_table(items)
```

### 3.4 表格渲染

| 列 | 宽度 | 数据来源 |
|----|------|----------|
| 时间 | 100px | AlertItem.time_str() |
| 节点 | 120px | AlertItem.node_alias |
| 类型 | 120px | AlertItem.name |
| 指标 | 140px | AlertItem.path |
| 当前值 | 80px | AlertItem.value |
| 阈值 | 80px | AlertItem.threshold |
| 等级 | 60px | AlertItem.level (彩色标签) |

等级列颜色：
- "red" → COLOR_DANGER (红底白字)
- "warn" → COLOR_WARN (橙底白字)

### 3.5 空状态

无告警时显示居中提示：「暂无告警」，表格隐藏。

---

## 四、生命周期

### 4.1 PageBase 生命周期（由 MainWindow 管理）

```
on_show()  → vm 刷新 + 连接信号（如需要）
on_hide()  → 无特殊操作（VM 保持连接，下次 on_show 直接显示）
cleanup()  → 断开信号（窗口关闭时）
```

### 4.2 信号连接时机

```
__init__()
  → vm.alerts_changed.connect(self._on_alerts_changed)
  → vm.count_changed.connect(self._on_count_changed)

on_show()
  → self._refresh_table()

on_hide()
  → 无操作（VM 持续更新，页面回到前台时刷新）

cleanup()
  → vm.alerts_changed.disconnect(self._on_alerts_changed)
  → vm.count_changed.disconnect(self._on_count_changed)
```

### 4.3 数据刷新链

```
AlertStore.push(alert)
  → VM._on_alert_added(alert)
  → _items.insert(0, item)
  → VM.alerts_changed.emit()
  → AlertsPage._on_alerts_changed()
  → _refresh_table()
  → QTableWidget.setRowCount(N) + 填充行
```

---

## 五、托盘联动

### 5.1 当前 MainWindow 中的连接

```python
# MainWindow.__init__
self.alert_store.alert_added.connect(self._on_alert_added)

def _on_alert_added(self, alert):
    log.warning("告警: %s %s %s=%s (阈值:%s)",
                alert["node_alias"], alert["name"],
                alert["path"], alert["value"], alert["threshold"])
    if self.cfg.get("alert_popup", True):
        self.tray_manager.show_message(
            f"告警 - {alert['node_alias']}",
            f"{alert['name']}: {alert['path']}={alert['value']}",
            "warning", 3000)
```

### 5.2 AlertsPage 与托盘的关系

```
AlertStore.push(alert)
  ├─→ AlertVM → AlertsPage 刷新表格（显示）
  ├─→ MainWindow._on_alert_added → 日志 + TrayManager（通知）
  └─→ AlertVM.count_changed → SideNav 徽标（导航）
```

**AlertsPage 不是告警产生者**——它只消费。托盘由 MainWindow 独立连接。

### 5.3 SideNav 告警徽标（未实现，Phase 3-4 预留）

SideNav 导航按钮上叠加红色数字徽标。由 MainWindow 连接 AlertVM.count_changed 后更新。

---

## 六、与现有 Store 的接口

### AlertStore 使用

| 方法 | AlertsPage 用途 |
|------|-----------------|
| 通过 AlertVM.get_items() | 表格数据 |
| 通过 AlertVM.get_summary() | 统计卡片 |
| 通过 AlertVM.set_filter_level() | 级别过滤 |
| 通过 AlertVM.set_filter_node() | 节点过滤 |
| vm.clear_node(node_id) | 清空按钮 |
| vm.clear_all() | 清空全部 |

### AlertStore 信号

| 信号 | VM 处理 |
|------|---------|
| alert_added | → _items.insert → alerts_changed |
| alert_cleared | → _items 移除 → alerts_changed |
| count_changed | → count_changed（转发） |

---

## 七、异常设计

### 7.1 告警风暴（大量 push）

AlertStore 已有 _max_entries=500 限制。
AlertVM 的 _items 同样限制长度，超限时丢弃旧条目。

### 7.2 节点删除

NodeStore.node_removed → MainWindow 调用 alert_store.clear_node()
  → AlertVM._on_node_cleared() → 移除该节点 AlertItem
  → alerts_changed

### 7.3 清空操作

清空按钮 → vm.clear_all() → alert_store.clear_all()
  → _items 清空 → alerts_changed

---

## 八、测试规划

### 8.1 AlertViewModel 测试

tests/test_v52_alert_vm.py：

| 用例 | 验证 |
|------|------|
| 新告警 | push → vm.get_items() 返回 AlertItem |
| 去重 | 30s 内重复 push → items 不增长 |
| 节点隔离 | node_A 的告警不影响 node_B |
| 过滤-级别 | set_filter_level("red") → 只返回 red |
| 过滤-节点 | set_filter_node("A") → 只返回 node_A |
| 过滤-搜索 | set_filter_search("CPU") → 只返回 name/path 含 CPU |
| 清空 | clear_all → items 清空 |
| count | get_red_count/get_warn_count 正确 |
| 信号 | push → alerts_changed 触发 |

### 8.2 AlertsPage 测试

tests/test_v52_alerts_page.py：

| 用例 | 验证 |
|------|------|
| VM 注入 | set_view_model 正常 |
| 空状态 | 无告警 → 显示「暂无告警」 |
| 表格显示 | 有告警 → QTableWidget 有行 |
| 信号刷新 | VM alerts_changed → 表格更新 |
| 过滤 | 选择过滤 → 表格行数变化 |
| 生命周期 | on_show/on_hide/cleanup 不崩溃 |
| 禁止访问 Store | AlertsPage 无 import AlertStore |

---

## 九、迁移步骤

### Phase A：新增 AlertViewModel

1. 创建 host/viewmodels/alert_vm.py
2. AlertItem 数据结构 + AlertViewModel 类
3. 单元测试：test_v52_alert_vm.py

### Phase B：创建 AlertsPage

1. 重写 host/gui/pages/alerts_page.py
2. 顶部统计卡片 + 过滤栏 + QTableWidget
3. 注入 AlertViewModel
4. 单元测试：test_v52_alerts_page.py

### Phase C：MainWindow 集成

1. MainWindow 创建 AlertVM 并注入 AlertsPage
2. SideNav 告警徽标连接 count_changed
3. 集成验证

### Phase D：清理（如有旧代码）

- 确认 AlertsPage 无直接 AlertStore 访问
- 确认无 QTimer

---

## 十、禁止事项

| 禁止项 | 原因 |
|--------|------|
| 修改 AlertEngine | v5.1 逻辑稳定 |
| 修改 AlertService | 订阅机制已验证 |
| 修改 Agent/Connection/Collector | 不涉及 |
| 引入 QTimer | Signal 驱动架构约束 |
| AlertsPage 直接访问 alert_store._alerts | 必须通过 VM |
| 重新设计 AlertStore | Phase 0 已完成 |
