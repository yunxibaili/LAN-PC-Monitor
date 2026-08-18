# Phase 3-7：v5.1 UI 组件迁移到 v5.2 widgets 架构

> **Version**: v5.2
> **Status**: 完成
> **日期**: 2026-08-11
> **目标**: 将 v5.1 遗留 UI 组件（NodeListWidget / DetailPanel）迁移到 v5.2 `host/gui/widgets/` 架构，保持 Store → ViewModel → Page → Widget 分层，禁止 Page 访问 Store / Widget 含业务逻辑。

---

## 一、修改文件

| 文件 | 改动 |
|------|------|
| `host/gui/widgets/node_list.py` | **新增**：从 `host/gui/node_list.py` 迁移（NodeListWidget / NodeListItemWidget / LOCAL_NODE_ID），logger 改为 `host.gui.widgets.node_list` |
| `host/gui/widgets/detail_panel.py` | **新增**：从 `common/gui/detail_panel.py` 迁移（DetailPanel / update_data / clear / 字段映射），logger 改为 `host.gui.widgets.detail_panel` |
| `host/gui/widgets/__init__.py` | **修改**：统一导出全部 12 个组件（含 ChartWidget 惰性导入保护） |
| `host/gui/main_window.py` | **修改**：DetailPanel / NodeListWidget import 改到 `host.gui.widgets.*` |
| `host/gui/pages/nodes_page.py` | **修改**：DetailPanel / NodeListWidget import 改到 `host.gui.widgets.*` |
| `common/gui/detail_panel.py` | **修改**：改为兼容转发 shim（`from host.gui.widgets.detail_panel import DetailPanel`） |

## 二、删除文件

| 文件 | 说明 |
|------|------|
| `host/gui/node_list.py` | 已迁移到 `host/gui/widgets/node_list.py`，删除旧文件 |

## 三、引用变化

### NodeListWidget / LOCAL_NODE_ID

| 原引用 | 新引用 |
|--------|--------|
| `from host.gui.node_list import LOCAL_NODE_ID, NodeListWidget`（main_window） | `from host.gui.widgets.node_list import ...` |
| `from host.gui.node_list import LOCAL_NODE_ID, NodeListWidget`（nodes_page） | `from host.gui.widgets.node_list import ...` |
| `host/gui/node_list.py` 自身 | 删除（widgets 版取代） |

### DetailPanel

| 原引用 | 新引用 |
|--------|--------|
| `from common.gui.detail_panel import DetailPanel`（main_window） | `from host.gui.widgets.detail_panel import DetailPanel` |
| `from common.gui.detail_panel import DetailPanel`（nodes_page） | `from host.gui.widgets.detail_panel import DetailPanel` |
| `from common.gui.detail_panel import DetailPanel`（agent/gui/main_window.py） | **保留 shim 兼容**（common/gui/detail_panel.py 转发） |
| `from common.gui.detail_panel import DetailPanel`（test_v52_detail_panel.py） | **保留 shim 兼容** |

## 四、测试结果

| 测试 | 结果 | 说明 |
|------|------|------|
| test_api.py | **14/14** | REST + WS 回归 |
| test_v52_phase0.py | **83/83** | Store/facade/service |
| test_v52_phase2.py | **24/24** | 解耦 |
| test_v52_phase28.py | **27/27** | 数据源收敛 |
| test_v52_alert_vm.py | **31/31** | AlertViewModel |
| test_v52_nodes_page.py | ⚠️ 需 PyQt5 | 沙箱无 PyQt5，无法运行；import 路径已更新（nodes_page 用 widgets） |
| test_v52_detail_panel.py | ⚠️ 需 PyQt5 | 走 shim 兼容，import 不破坏 |

> **沙箱限制**：PyQt5 相关测试（nodes_page / detail_panel / chart_widget 等）在无 PyQt5 环境无法运行，但全部模块编译通过、import 路径一致。

## 五、架构约束遵守

- ✅ **Store → ViewModel → Page → Widget**：nodes_page 通过 NodeDetailViewModel 获取数据，DetailPanel 仅 `update_data(data)` 消费 VM 输出
- ✅ **Page 不访问 Store**：DetailPanel 已是纯展示（无 Store/monitor_data 访问），nodes_page 只经 VM
- ✅ **Widget 无业务逻辑**：NodeListWidget / DetailPanel 均为纯 UI 组件
- ✅ **main_window 不含页面 UI 细节**：本次未改动 main_window 布局逻辑，仅改 import

## 六、overview_grid 处理结论

`host/gui/overview_grid.py` **保留**：
- 仍被 main_window legacy UI 引用（`self.overview`，`_apply_view_mode` 的 MODE_OVERVIEW 模式 + `_on_toggle_overview` 工具栏按钮）
- v5.2 DashboardPage（NodeCard）是替代方向，但**未完全接管**"概览模式"语义
- **删除计划**：待 Phase 3-8 main_window 瘦身时，若 v5.2 Dashboard 完全覆盖概览功能，则随 legacy UI 一并移除

## 七、风险说明

1. **common/gui/detail_panel.py shim**：agent 仪表盘依赖它，保留转发不破坏 agent；新代码用 widgets 版。
2. **LOCAL_NODE_ID 双定义**：`host/gui/widgets/node_list.py` 与 `host/local_node.py` 各有一份，本次未统一（避免扩大改动面），后续统一到 common。
3. **ChartWidget 惰性导入**：依赖 pyqtgraph，缺失时 `__init__.py` 置 `ChartWidget = None`，不破坏 widgets 包。
4. **PyQt5 测试需真机**：沙箱无法验证 GUI 测试，建议真机跑 `test_v52_nodes_page.py` / `test_v52_detail_panel.py` 确认渲染。

---

**结论**：v5.1 两个 UI 组件已迁移到 v5.2 widgets 架构，主链路（host 侧）已全部走 widgets 路径，agent 通过 shim 兼容不受影响。overview_grid 保留待 Phase 3-8。
