# 架构

> **Version**: v5.3.3
> **Status**: STABLE

## 1. 总体架构

```
Agent (采集+推送)
  ↓ WebSocket (每秒)
Connection (WS 客户端, Signal 驱动)
  ↓
Store (FrameStore / NodeStore / HistoryStore / AlertStore)
  ↓
ViewModel (数据转换层, 不含 PyQt5)
  ↓
Page (页面容器, 只导入 Widget + ViewModel)
  ↓
Widget (UI 组件, 只导入 Theme)
  ↓
Theme (ThemeColors / ThemeSpacing / ThemeTypography)
```

## 2. 目录结构

```
host/
 ├── config.py                # host_config.json 读写
 ├── connection.py            # NodeConnection (WebSocket 客户端)
 ├── connection_core.py       # ConnectionCore（纯 Python，无 PyQt5）
 ├── discovery.py             # UDP/mDNS 监听
 ├── alerts.py                # 红线告警引擎
 ├── facade/                  # 门面层（隔离 VM 与 Service/Storage）
 │   ├── settings_facade.py
 │   ├── history_facade.py
 │   ├── alert_adapter.py
 │   └── connection_factory.py
 ├── store/                   # 运行时数据存储（纯 Python 信号）
 │   ├── signals.py           # Signal（非 pyqtSignal）
 │   ├── frame_store.py
 │   ├── node_store.py
 │   ├── history_store.py
 │   └── alert_store.py
 ├── service/                 # 业务服务层
 │   ├── alert_service.py
 │   ├── discovery_service.py
 │   ├── metric_persistence.py # Runtime Frame → Storage Record
 │   └── storage_service.py    # Storage 组装 + 生命周期
 ├── storage/                 # SQLite 持久化层
 │   ├── database.py          # 连接 + lifecycle
 │   ├── schema.py            # 表定义 + 版本管理
 │   ├── records.py           # MetricRecord / AlertHistoryRecord / SessionRecord
 │   ├── retention.py         # 数据保留策略 + 清理
 │   └── repositories/
 │       ├── metrics_repo.py
 │       ├── alerts_repo.py
 │       └── sessions_repo.py
 ├── viewmodels/              # ViewModel（纯 Python）
 │   ├── dashboard_vm.py
 │   ├── node_detail_vm.py
 │   ├── monitor_vm.py
 │   ├── alert_vm.py
 │   ├── history_vm.py
 │   └── settings_vm.py
 ├── manager/
 │   └── tray_manager.py      # 托盘管理
 └── gui/                     # PyQt5 UI 层
     ├── main_window.py       # 主窗口（组装）
     ├── controllers/         # 控制器（协调 Store↔VM↔Page）
     ├── navigation/side_nav.py
     ├── theme/               # 设计系统（colors/spacing/typography/...）
     ├── pages/               # 6 个页面
     └── widgets/             # 可复用 UI 组件
```

## 3. 数据流

```
Agent Collector (采集器线程池, 每秒)
  ↓ get()
Aggregator (组装 monitor_data 帧)
  ↓
WebSocket Server (广播)
  ↓ 每秒推送
Host NodeConnection (WS 线程)
  ↓ data_received.emit(frame, node_id)
DataController._on_data() (主线程)
  ├── FrameStore.push(node_id, frame)       → 更新最新帧
  ├── HistoryStore.push_frame(node_id)      → 追加内存历史
  ├── NodeStore.update_status()             → 更新状态
  ├── AlertService._on_frame()              → 告警检测
  ├── MetricPersistenceService.persist_frame → SQLite 持久化
  └── DashboardVM.data_changed.emit()        → 通知页面
        ↓
Page._refresh() (从 VM 获取数据, 渲染 Widget)
```

持久化链路：

```
DataController → MetricPersistenceService
  → StorageService (Database + Repositories + Retention)
  → SQLite (metrics / alert_history / sessions)
  → HistoryFacade (range / latest / aggregate)
  → HistoryVM → HistoryPage
```

## 4. 分层依赖规则

### ✅ 允许

```
Page → Widget (UI 组件)
Page → ViewModel (数据转换)
Widget → Theme (样式常量)
ViewModel → Store / Facade (数据)
Service → Storage / Repository
```

### ❌ 禁止

```
Page → Store / Connection / ConfigManager / Storage / sqlite3 ❌
Widget → Store / ViewModel / Service ❌
ViewModel → PyQt5 / sqlite3 ❌
sqlite3 → 除 host/storage/ 外任何层 ❌
硬编码颜色/间距 ❌
QTimer 轮询 ❌
```

## 5. Signal 驱动（不轮询）

```
NodeConnection.data_received → DataController → Store.push
  → Store.frame_updated → VM.data_changed → Page._refresh
```

数据到达即更新，零延迟。

## 6. 设计系统

所有 GUI 颜色/间距/字体通过 Theme 引用，详见 [docs/UI_GUIDE.md](UI_GUIDE.md)：

```python
from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
```

## 7. 存储规范

数据流：`Collector → PersistenceService → Repository → SQLite`

| 规则 | 说明 |
|------|------|
| sqlite3 只在 host/storage/ | 其他层禁止 import sqlite3 |
| 删除走 Repository | 禁止 Service 直接执行 DELETE SQL |
| Record 与 Runtime 分离 | MetricRecord ≠ MonitorFrame |
| 查询走 Facade | VM 不直接碰 Repository |
| Storage 生命周期走 StorageService | MainWindow 不直接碰 Database |
| DB 路径 | `%APPDATA%/LAN-PC-Monitor/data/history.db`（见 storage_service.get_default_db_path） |
