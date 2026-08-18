# v5.2 项目结构审计与重构规划

> **Version**: v5.2
> **Status**: Architecture Audit（只读分析，未改代码）
> **日期**: 2026-08-11
> **范围**: agent/ host/ common/ tests/ docs/

---

## 一、当前真实调用关系图

### 1.1 数据流主链路（已收敛）

```
Agent (WS monitor_data)
  → host/connection_core.py (回调 on_data)
  → host/connection.py (NodeConnection Qt 信号)
  → host/gui/main_window.py (Signal 连接 _on_data)
      → host/store/frame_store.py   (frame_store.push → AlertService)
      → host/store/history_store.py (历史)
      → host/service/alert_service.py → host/facade/alert_adapter.py → host/store/alert_store.py
      → host/store/node_store.py    (状态/RTT/评分, QualityScorer 唯一持有)
  → host/viewmodels/*.py (页面数据转换层)
  → host/gui/pages/*.py (5 页面)
  → host/gui/widgets/*.py (组件库)
  → host/gui/theme/*.py (colors/metrics/style)
```

### 1.2 组件依赖图

```
host/gui/main_window.py (1014 行, 巨型)
 ├── [v5.1 旧] common/gui/detail_panel.py (301)
 ├── [v5.1 旧] host/gui/node_list.py (170)  — NodeListWidget/LOCAL_NODE_ID
 ├── [v5.1 旧] host/gui/overview_grid.py (195) — OverviewGrid
 ├── [v5.2] host/gui/navigation/side_nav.py (209)
 ├── [v5.2] host/gui/pages/*.py (5 页: dashboard/nodes/monitor/alerts/settings)
 ├── [v5.2] host/viewmodels/*.py (5 个: dashboard/node_detail/monitor/alert/settings)
 ├── [v5.2] host/gui/theme/*.py (colors/metrics/style)
 └── [v5.2] host/store/*.py + facade/* + service/* + manager/*

host/gui/pages/nodes_page.py (162)
 ├── [v5.1 旧] common/gui/detail_panel.py (DetailPanel)
 └── [v5.1 旧] host/gui/node_list.py (NodeListWidget/LOCAL_NODE_ID)
     └── 经 NodeDetailViewModel (host/viewmodels/node_detail_vm.py, 393)

host/gui/pages/dashboard_page.py → widgets/node_card + empty_state + page_header + theme
host/gui/pages/monitor_page.py  → widgets/chart_widget + viewmodels/monitor_vm
host/gui/pages/alerts_page.py   → (读 alert_store; 由 test_v52_alerts_page 覆盖)
host/gui/pages/settings_page.py → viewmodels/settings_vm + facade
```

### 1.3 关键观察

1. **main_window.py 1014 行** = v5.1 旧 UI（_build_ui 全量构建）+ v5.2 新层（_init_v52_ui 叠加 SideNav+5页）。**双 UI 并存**。
2. **LOCAL_NODE_ID 两处定义**：`host/gui/node_list.py:28` 与 `host/local_node.py:25`。
3. **DetailPanel 被三方引用**：main_window（旧）、nodes_page（v5.2 但复用旧组件）、agent/gui（仪表盘）。是 v5.1 唯一仍在用的"页面级"组件。
4. **theme 两套**：`common/theme.py`（v5.1，140 行）与 `host/gui/theme/*`（v5.2，colors/metrics/style）。
5. **self_monitor 三处**：common/self_monitor.py（真身）、host/self_monitor.py（转发）、agent/self_monitor.py（转发）。
6. **local_node 两处**：host/local_node.py 与 agent/local_node.py（角色隔离，但结构重复）。

---

## 二、v5.1 遗留代码清单

### 2.1 明确的 v5.1 遗留（应清理或迁移）

| 文件/项 | 行数 | 状态 | 建议 |
|---------|------|------|------|
| `host/gui/main_window.py` 中 `_build_ui` 旧布局（top/detail_stack/splitter/node_list/detail_panel/overview） | ~150 | 与 v5.2 `_init_v52_ui` 并存 | Phase 3 完成后删除，只留 v5.2 布局 |
| `host/gui/node_list.py` | 170 | 被 nodes_page 复用，但属于 v5.1 组件 | 迁移到 `widgets/` 或保留（v5.2 nodes_page 依赖） |
| `host/gui/overview_grid.py` | 195 | main_window 引用，但 v5.2 DashboardPage 用 NodeCard | **死代码候选**（v5.2 Dashboard 已用 NodeCard） |
| `common/gui/detail_panel.py` | 301 | 被 nodes_page/agent/main_window 引用 | 迁移到 `host/gui/widgets/` 或重构 |
| `host/discovery.py` 旧类 DiscoveryListener/MdnsDiscovery | 205 | 已被 service/discovery_service.py 封装 | 保留（service 依赖），但 main_window 应只经 service |
| `common/theme.py` v5.1 主题 | 140 | 与 host/gui/theme/* v5.2 并存 | v5.2 页面用新 theme；旧 theme 供旧 UI/agent 用 |

### 2.2 纯冗余/死代码

| 项 | 说明 |
|----|------|
| `np_debug.txt` / `np_debug2.txt` | 顶层调试残留文件 |
| `host/gui/widgets/__init__.py` | 空（"Phase 3-1 暂空"），但 widgets/ 已有 11 个组件 |
| `client/` 目录 | 已在 v5.1 删除（确认无此目录） |
| `node/` 目录 | 已在 v5.1 删除（确认无此目录） |

### 2.3 双实现/双定义

| 项 | 位置 A | 位置 B | 建议 |
|----|--------|--------|------|
| LOCAL_NODE_ID | host/gui/node_list.py:28 | host/local_node.py:25 | 统一到 common/ |
| DetailPanel | common/gui/detail_panel.py | — | 迁 host/gui/widgets/ |
| theme | common/theme.py | host/gui/theme/* | 分层：common 基础色 + host/gui/theme 组件级 |
| self_monitor | common/self_monitor.py | host/ + agent/ 转发 | 已合理（转发层），保留 |

---

## 三、当前 MainWindow 职责（1014 行拆分建议）

### 应保留（窗口生命周期/路由/Signal 连接）

`__init__`（装配）、`closeEvent`、几何/状态记忆、视图模式路由、`_on_nav_changed`、`_on_data`（Signal→Store）、`_on_status/_on_rtt/_on_loss`（→Store）、`merged_hosts`、托盘/发现入口。

### Phase 3 应迁移（UI 组件/Layout/对话框）

`_build_ui` 旧布局、`_init_v52_ui` 页面创建、节点管理对话框（`_on_add_node/_on_scan_nodes/_on_connect_code/_on_clipboard/_on_import/_on_export/_on_add_local_node/_on_discovery_add`）、右键菜单、告警 UI 展示。

### 迁移目标结构

```
host/gui/
 ├── main_window.py     瘦身: 路由 + 生命周期 + Signal 连接 (~300 行)
 ├── navigation/side_nav.py
 ├── pages/             dashboard/nodes/monitor/alerts/settings
 ├── widgets/           组件库 (11 个 + 迁移 DetailPanel/NodeListWidget)
 ├── theme/             colors/metrics/style
 └── [删除] node_list.py / overview_grid.py / (迁入 widgets)

host/viewmodels/        dashboard/node_detail/monitor/alert/settings
host/store/             node/frame/history/alert
host/service/           alert/discovery
host/facade/            settings/alert
host/manager/           tray
```

---

## 四、重构规划（分阶段，只动 host/gui 层）

### Phase 3-7：旧组件迁移
- `node_list.py` → `host/gui/widgets/node_list.py`（保留 LOCAL_NODE_ID 导出兼容）
- `overview_grid.py` → 若 v5.2 DashboardPage 完全替代，则**删除**（确认无引用后）
- `common/gui/detail_panel.py` → `host/gui/widgets/detail_panel.py`（nodes_page 改引用）

### Phase 3-8：main_window 瘦身
- 删除 `_build_ui` 旧布局，只保留 v5.2 布局（SideNav + 5 页）
- 节点管理对话框 → NodesPage 内部
- 告警 UI → AlertsPage（已通过 alert_vm）
- 目标 main_window ≤ 400 行

### Phase 3-9：主题/常量统一
- `LOCAL_NODE_ID` 统一到 `common/constants.py`（或 common/utils）
- v5.2 页面统一用 `host/gui/theme/`，旧 `common/theme.py` 仅供 agent 仪表盘

### Phase 3-10：死代码清理
- 删除 `np_debug*.txt`
- 删除未引用的 `overview_grid.py`（确认）
- `widgets/__init__.py` 补导出

---

## 五、风险提示

1. **双 UI 并存**：main_window 旧布局（index 0）仍可切回，v5.2 新页在 index 1-5。若删除旧布局，需先确认 SideNav 默认页已覆盖全部旧功能（节点管理/概览/告警/设置）。
2. **DetailPanel 依赖**：nodes_page + agent 仪表盘 + main_window 三处引用。迁移需同步改 3 处 + 测试。
3. **LOCAL_NODE_ID 双定义**：若统一，需检查所有 `from host.gui.node_list import LOCAL_NODE_ID` 引用点。
4. **overview_grid 删除风险**：v5.2 DashboardPage 的 NodeCard 是否 1:1 覆盖 OverviewCard 功能（卡片点击→Monitor）需验证。
5. **测试依赖旧组件**：`test_v52_detail_panel.py`/`test_v52_nodes_page.py` 引用 DetailPanel/NodeListWidget，迁移后需同步。

---

**审计结论**：v5.2 Store→ViewModel→Page→Widget 架构已建立且数据流清晰；剩余工作是**清理 v5.1 遗留 UI 组件 + 瘦身 main_window + 统一常量/主题**。建议按 Phase 3-7 → 3-10 顺序推进，每步保持测试绿。
