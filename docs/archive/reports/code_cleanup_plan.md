# Code Cleanup Plan

> **Generated**: 2026-08-12
> **Status**: PLAN (待执行)
> **Scope**: host/, agent/, common/

---

## 一、当前目录树

### host/gui/widgets/ (21 文件)

| 文件 | 行数 | 状态 | 说明 |
|------|------|------|------|
| app_card.py | 55 | ❌ DEPRECATED | 未被任何页面使用 |
| card_widget.py | 35 | ❌ DEPRECATED | 与 app_card 重复，未被使用 |
| metric_card.py | 61 | ❌ DEPRECATED | 未被任何页面使用 |
| status_badge.py | 53 | ❌ DEPRECATED | 未被任何页面使用 |
| quality_badge.py | 40 | ❌ DEPRECATED | 未被任何页面使用 |
| page_header.py | 41 | ❌ DEPRECATED | 未被任何页面使用 |
| section_title.py | 18 | ❌ DEPRECATED | 未被任何页面使用 |
| empty_state.py | 34 | ❌ DEPRECATED | 未被任何页面使用 |
| metric_bar.py | 92 | ❌ DEPRECATED | 未被任何页面使用 |
| detail_panel.py | 302 | ⚠️ LEGACY | 使用旧 common.theme，仍被 detail_dashboard 引用 |
| node_list.py | 170 | ⚠️ LEGACY | 被 node_explorer 替代，但 LOCAL_NODE_ID 仍被使用 |
| node_card.py | 198 | ✅ ACTIVE | Dashboard 页面使用 |
| resource_card.py | 93 | ✅ ACTIVE | DetailDashboard 内部使用 |
| chart_widget.py | 120 | ✅ ACTIVE | ChartPanel 内部使用 |
| chart_panel.py | 128 | ✅ ACTIVE | MonitorPage 使用 |
| node_explorer.py | 165 | ✅ ACTIVE | NodesPage 使用 |
| detail_dashboard.py | 100 | ✅ ACTIVE | NodesPage 使用 |
| monitor_header.py | 112 | ✅ ACTIVE | MonitorPage 使用 |
| metric_selector.py | 127 | ✅ ACTIVE | MonitorPage 使用 |
| header_bar.py | 86 | ✅ ACTIVE | MainWindow 使用 |

### 已废弃模块

| 文件 | 状态 | 说明 |
|------|------|------|
| host/gui/overview_grid.py | ✅ 已删除 | Phase 3-8 删除 |
| host/gui/node_list.py (旧路径) | ✅ 已迁移 | 迁移到 widgets/ |

---

## 二、重复模块

### CardWidget vs AppCard

- `card_widget.py` (35行): QFrame 卡片容器
- `app_card.py` (55行): QFrame 卡片容器 + 点击信号
- **两个都未被使用**，功能几乎相同
- **建议**: 保留 app_card (功能更全)，删除 card_widget

### LOCAL_NODE_ID 重复定义

```
host/local_node.py:25          LOCAL_NODE_ID = "localhost"
host/gui/widgets/node_list.py:28  LOCAL_NODE_ID = "localhost"
host/gui/controllers/data_controller.py:21  LOCAL_NODE_ID = "localhost"
```

- **3 处重复定义相同值**
- **建议**: 创建 common/constants.py，统一引用

---

## 三、Theme 迁移计划

### 需要迁移的文件 (17 个 import 站点)

| 文件 | 旧 import | 新 import |
|------|-----------|-----------|
| host/main.py | `from common.theme import DARK_QSS` | `from host.gui.theme.style import dark_qss` |
| host/gui/discovery_dialog.py | `from common.theme import COLOR_NA` | `from host.gui.theme.colors import ThemeColors as TC` |
| host/gui/discovery_dialog.py | `from common.theme import remove_help_button` | 保留 (独立工具) |
| host/gui/widgets/detail_panel.py | `from common import theme` | `from host.gui.theme.colors import ThemeColors as TC` |
| host/gui/widgets/detail_panel.py | `from common.theme import apply_color` | 内联或迁移到 theme |
| host/gui/pages/alerts_page.py | `from common import theme` | `from host.gui.theme.colors import ThemeColors as TC` |
| host/gui/pages/settings_page.py | `from common import theme` | `from host.gui.theme.colors import ThemeColors as TC` |
| host/gui/widgets/node_list.py | `from common import theme` | 如果保留则迁移 |

### common/theme.py 处理

- **不删除** (agent 仍使用)
- host/ 侧全部迁移到 host.gui.theme
- agent/ 侧保留 shim

---

## 四、删除风险评估

| 操作 | 风险 | 测试覆盖 |
|------|------|----------|
| 删除 card_widget.py | 低 | 无测试依赖 |
| 删除 app_card.py | 低 | 无测试依赖 |
| 删除 metric_card.py | 低 | 无测试依赖 |
| 删除 status_badge.py | 中 | test_v52_node_widgets 有引用 |
| 删除 quality_badge.py | 中 | test_v52_node_widgets 有引用 |
| 删除 page_header.py | 低 | 无测试依赖 |
| 删除 section_title.py | 低 | 无测试依赖 |
| 删除 empty_state.py | 低 | 无测试依赖 |
| 删除 metric_bar.py | 中 | test_v52_node_widgets 有引用 |
| 迁移 detail_panel.py theme | 中 | test_v52_detail_panel 有测试 |
| 迁移 node_list.py theme | 低 | 无直接测试 |
| 创建 common/constants.py | 低 | 新增 |
| 迁移 DARK_QSS | 中 | test_p0 有测试 |

---

## 五、执行顺序

1. **创建 common/constants.py** (LOCAL_NODE_ID)
2. **更新所有 LOCAL_NODE_ID 引用**
3. **删除未使用 widgets** (8 个低风险)
4. **迁移 host/ theme imports** (7 个文件)
5. **运行全量测试**
6. **生成最终报告**
