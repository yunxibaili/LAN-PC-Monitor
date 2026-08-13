# v5.2 Phase 2.5 — MainWindow 架构扫描报告

> **Version**: v5.2
> **Status**: Scan Report（只读分析，未改代码）
> **对象**: `host/gui/main_window.py`（761 行，45 个方法/属性）
> **基线**: v5.2 Phase 2 完成态（告警/托盘/发现已解耦到 Store/Service/Manager）

---

## 一、当前 MainWindow 职责清单与分类

### A. 应保留（Window 生命周期 / 页面路由 / Signal 连接）

| 方法 | 职责 | 备注 |
|------|------|------|
| `__init__` | 组装 Stores/Service/Manager + 启动流程 | **核心**，保留装配逻辑 |
| `_restore_geometry` / `_save_geometry` / `_save_state` | 窗口几何/状态记忆 | 保留 |
| `_build_ui` 的窗口级布局骨架 | 顶部栏 + 中央 QStackedWidget + 状态栏 | **Phase 3 拆分** |
| `closeEvent` | 关闭清理（discovery/alert/tray 已解耦） | 保留 |
| `connected_nodes` | 当前在线节点（供状态栏/视图模式） | 保留 |
| `_apply_view_mode` / `_switch_single_mode` / `_switch_multi_mode` | 视图模式切换（页面路由） | 保留为路由 |
| `_on_toggle_overview` | 概览切换 | 保留 |
| `_on_node_selected` | 选中节点 → 详情（Signal 分发） | 保留 Signal 连接 |
| `_on_data` / `_on_status` / `_on_rtt` / `_on_loss` | NodeConnection 信号 → Store + UI | **保留 Signal 连接**，UI 部分 Phase 3 迁页面 |

### B. Phase 3 需要迁移（UI 组件创建 / Layout / Toolbar / Panel）

| 方法 | 迁移目标 | 说明 |
|------|----------|------|
| `_build_ui`（工具栏按钮组） | `SideNav` / Toolbar | 顶部按钮（添加/扫描/连接码/剪贴板/导入/导出/设置）→ 导航/工具栏组件 |
| `_build_ui`（节点列表+详情+概览） | `NodesPage` / `DashboardPage` | QSplitter 布局 → 页面化 |
| `_init_local_node` | `DashboardPage`/本机节点管理 | 本机卡片/列表项创建 |
| `_load_saved_nodes` / `_add_node` / `_remove_node` | `NodesPage` + `NodeController` | 节点 UI 增删 → 页面 |
| `_on_add_node` / `_on_scan_nodes` / `_on_connect_code` / `_on_clipboard` / `_on_import` / `_on_export` / `_on_add_local_node` / `_on_discovery_add` | `NodesPage` | 节点管理对话框/操作 → NodesPage |
| `_on_context_action` / `_edit_alias` | `NodesPage`（右键菜单） | 列表右键 → 页面 |
| `_on_overview_card_clicked` | `DashboardPage`（卡片点击） | 卡片 → Monitor 跳转 |
| `_check_alerts` / `_clear_node_alerts` / `_update_status_bar` / `_show_tray_alert` | `AlertsPage` + `AlertAdapter` | 告警 UI 展示 → AlertsPage |
| `_refresh_top` | 状态栏/导航徽标 | 顶部计数 → SideNav/StatusBar |

### C. 不应存在（业务逻辑应已迁到 Store/Service/Facade）

| 现状 | 应归属 | Phase 2 后状态 |
|------|--------|---------------|
| `self.frames` / `self.statuses` / `self.rtts` / `self.losses` / `self.scorers` / `self.scores` dict | `FrameStore` / `NodeStore` | ⚠️ **双写残留**：main_window 仍持有 dict + Store 同时写，Phase 3 应统一读 Store |
| `_inject_net_quality`（评分计算） | `NodeStore.update_quality` | ⚠️ main_window 仍直接读写 `self.rtts/self.losses/self.scorers`，应改为读 NodeStore |
| `_check_alerts` 的 `_alert_state` 去重 | `AlertStore`（30s 去重） | ⚠️ **两套去重并存**：AlertStore 30s + `_alert_state` 状态变化，Phase 3 统一 |
| `merged_hosts` | `DiscoveryService.get_hosts` | ✅ 已委托，保留兼容 property |
| `_auto_discover_background` | `DiscoveryService.auto_discover_background` | ✅ 已委托，保留兼容入口 |
| `_init_tray` / `_show_tray_alert` | `TrayManager` | ✅ 已委托，保留兼容入口 |
| `settings` 读写 | `SettingsFacade` | ✅ 已接入 |

> **结论**：Phase 2 已把"发现/托盘"业务逻辑解耦干净；**Phase 3 的核心是**把 `frames/statuses/rtts/losses/scorers/scores` 六组 dict 的"双写"收敛为"单一 Store 读取"，并去掉 `_alert_state` 冗余去重。

---

## 二、下一阶段页面拆分建议

### 目标页面结构（对齐 v5.2_ui_design）

```
HostMainWindow（瘦身：路由 + 生命周期 + Signal 连接）
 ├── SideNav            工具栏按钮迁移（导航）
 ├── DashboardPage      _on_overview_card_clicked + 卡片网格
 ├── NodesPage          _add/_remove/_scan/_connect_code/_clipboard/_import/_export
 │                       + _on_context_action/_edit_alias + 详情面板
 ├── MonitorPage        新增（图表，读 HistoryStore/FrameStore）
 ├── AlertsPage         _check_alerts UI 部分 + 告警表格
 └── SettingsPage       _open_settings
```

### 迁移优先级

| 优先级 | 页面 | 依赖 Store | 直接可移动方法 |
|--------|------|-----------|---------------|
| P0 | NodesPage | FrameStore/NodeStore | `_on_add_node`/`_on_scan_nodes`/`_on_connect_code`/`_on_clipboard`/`_on_import`/`_on_export`/`_on_add_local_node`/`_on_discovery_add`/`_on_context_action`/`_edit_alias` |
| P1 | DashboardPage | FrameStore | `_on_overview_card_clicked` + OverviewGrid 重构 |
| P2 | AlertsPage | AlertStore | `_check_alerts` UI 部分 + `_update_status_bar` |
| P3 | MonitorPage | HistoryStore | 新增（无旧方法迁移） |
| P4 | SettingsPage | SettingsFacade | `_open_settings` |

### 关键重构点（Phase 3 必须做）

1. **收敛六组 dict → Store 单一来源**：`_on_data/_on_status/_on_rtt/_on_loss` 只写 Store，UI 从 Store 读；删除 `self.frames/statuses/rtts/losses/scorers/scores` 的双写。
2. **统一告警去重**：去掉 `_alert_state`，只保留 AlertStore 30s 去重；UI 通过订阅 AlertStore 信号更新状态栏/页面。
3. **页面生命周期协议**：每页 `on_show()/on_hide()/on_node_add()/on_node_remove()`，配合 QStackedWidget.currentChanged 做可见性门控。
4. **不引入 QTimer**：保持 Signal 驱动（FrameStore.frame_updated / NodeStore 信号 → 页面增量更新）。

---

## 三、方法标记清单

### ✅ 可以直接移动（纯 UI/对话框操作，无 Store 耦合）

| 方法 | 目标页 |
|------|--------|
| `_on_add_node` | NodesPage |
| `_on_scan_nodes` | NodesPage |
| `_on_connect_code` | NodesPage |
| `_on_clipboard` | NodesPage |
| `_on_import` | NodesPage |
| `_on_export` | NodesPage |
| `_on_add_local_node` | NodesPage |
| `_on_discovery_add` | NodesPage |
| `_on_context_action` | NodesPage |
| `_edit_alias` | NodesPage |
| `_on_overview_card_clicked` | DashboardPage |
| `_open_settings` | SettingsPage |
| `_update_status_bar` | AlertsPage |

### 🔄 需要重构（移动时需改数据来源）

| 方法 | 重构点 |
|------|--------|
| `_build_ui` | 拆分窗口骨架 + 各页面布局；工具栏→SideNav |
| `_add_node` / `_remove_node` | 移页面但保留 Store 生命周期同步；删 dict 双写 |
| `_init_local_node` | 本机节点管理 → DashboardPage/NodesPage |
| `_load_saved_nodes` | 移 NodesPage，读 Store |
| `_on_data` | 拆"写 Store"（留 MainWindow/Service）与"UI 更新"（→ 页面订阅） |
| `_inject_net_quality` | 评分逻辑 → NodeStore，删除 main_window 直接读写 dict |
| `_check_alerts` / `_clear_node_alerts` | UI 部分 → AlertsPage；去 `_alert_state` 冗余 |
| `_show_tray_alert` | 已委托 TrayManager，保留入口即可 |

### ⛔ 必须保留在 MainWindow

| 方法 | 理由 |
|------|------|
| `__init__` | 装配 Store/Service/Manager + 启动 |
| `closeEvent` | 窗口生命周期清理 |
| `_restore_geometry` / `_save_geometry` / `_save_state` | 窗口状态记忆 |
| `connected_nodes` | 视图模式依赖 |
| `_apply_view_mode` / `_switch_single_mode` / `_switch_multi_mode` | 页面路由 |
| `_on_toggle_overview` | 路由 |
| `_on_node_selected` | Signal 连接（选中分发） |
| `merged_hosts` (property) | 兼容对话框入口（已委托 DiscoveryService） |
| `_refresh_top` | 顶部计数（可移 SideNav，但当前保留） |

---

## 四、风险提示

1. **双写一致性问题**：Phase 3 收敛 dict→Store 时，若页面与 MainWindow 读不同来源，会闪跳。建议一次性切换，不渐进。
2. **AlertStore 30s 去重 vs _alert_state 状态去重**：两者语义不同（时间窗口 vs 状态变化）。Phase 3 统一为 AlertStore 时间窗口，但需确认"red→warn→red 快速变化"不丢失。
3. **页面可见性门控**：若不做，Monitor 图表在非当前页仍重绘，浪费 CPU（50 节点时明显）。
4. **scorers 迁移**：QualityScorer 有滑动窗口状态，已保留在 NodeStore 内；页面只读 `get_score`，不复制。

---

**扫描结论**：v5.2 Phase 2 后 MainWindow 已成功解耦"发现/托盘/告警评估"；剩余主要工作是 **Phase 3 页面拆分**（Nodes/Dashboard/Alerts/Monitor/Settings 五页）+ **六组 dict 收敛到 Store** + **告警去重统一**。建议按 §二 优先级 P0→P4 推进。
