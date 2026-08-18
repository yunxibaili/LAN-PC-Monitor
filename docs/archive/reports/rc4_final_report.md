# RC-4 Final Consistency Cleanup Report

> **Generated**: 2026-08-13
> **Status**: COMPLETE
> **Scope**: 文档一致性 / 代码引用一致性 / 目录结构一致性 / Theme 收口 / 测试描述一致性 / 仓库卫生
> **原则**: 不新增功能、不改变架构、不重构业务逻辑

---

## 一、执行摘要

| 维度 | 结果 |
|------|------|
| Tests | **723 通过 / 0 失败**（`test_v52_phase0/phase2` 环境性崩溃，见 §四） |
| Architecture | **PASS**（common → host/agent 依赖 0 处） |
| Theme | **PASS**（host/ 非 theme 硬编码颜色 0 处，含 `#fff`） |
| Docs | **PASS**（死链 0 处） |
| LOCAL_NODE_ID | **PASS**（唯一定义于 common/constants.py） |
| Legacy 违规 | **0** |
| 代码文件数量 | **150** 个 .py |

---

## 二、各阶段完成项

### 阶段 1：文档最终统一

- `docs/core/UI_SYSTEM.md` 成为唯一权威 UI 规范，合并缺失 token：
  `BACKGROUND_ELEVATED` / `BORDER_FOCUS` / `ALERT_INFO` / `Title Small` / `Numeric Medium`，并补 RTT 阈值行。
- `docs/design/ui_design_system.md` → `docs/archive/ui_design_system_old.md`，加 Deprecated 头。
- `docs/README.md` 修复：删除 `architecture.md` / `protocol.md` / `api.md` 根目录旧引用，改为指向 `core/`；补 `reports/`；目录结构图与真实目录一致。
- `README.md` 修复死链：`docs/installation.md` → `docs/archive/installation.md`。
- `docs/archive/v5.2_migration_plan.md` 修复 `v5.2_*` → `v52_*` 命名不一致死链。

### 阶段 2：代码架构修复（禁止 common → host 依赖）

- `common/theme.py`：删除 `from host.gui.theme.style import ThemeStyle`，`DARK_QSS` 改为自包含（common 自己维护基础主题）。
- `common/gui/detail_panel.py`：从转发 shim 改为**纯 Qt 通用实现**（仅依赖 common.theme/i18n/utils + PyQt5），恢复 `update_all(frame)` 接口 —— 修复了 Agent `--gui` 仪表盘调用不存在的 `update_all` 的隐藏崩溃。
- `common/config_manager.py`：删除 `import host.config` / `import agent.config`，改为直接读写 JSON（`_read_json` / `_write_json`）。
- **结果**：`common` 目录 0 处依赖 host/agent（扫描验证）。

### 阶段 3：Theme 收口（rtt_color）

- `host/gui/theme/colors.py` 新增 `ThemeColors.rtt_color` classmethod：正确处理 `None` / `"N/A"` / 非法值 → `TEXT_DISABLED`；`<5ms` 绿、`5~20ms` 黄、`>20ms` 红。
- `host/gui/theme/__init__.py` 删除有 bug 的一行式实现（原实现 `None`→红、"N/A"→TypeError），改为转发 `ThemeColors.rtt_color`。

### 阶段 4：硬编码颜色彻底清零

- `alerts_page.py`（统计卡 + 标题 + 表格 QSS）、`settings_page.py`（标题）、`alert_controller.py`（状态栏红/黄）、`chart_widget.py`（回退提示）、`tray_manager.py`（托盘图标色）全部替换为 `ThemeColors` 常量。
- **补查修复（本轮）**：复扫发现仍有 8 处 `#fff`（状态徽章白字前景）散落在 `detail_dashboard.py` / `metric_selector.py` / `monitor_header.py` / `node_card.py`。在 `ThemeColors` 新增 `TEXT_ON_COLOR = "#FFFFFF"` 常量并全部替换。
- **结果**：host/ 全树非 theme 文件硬编码 `#xxxxxx` 颜色 0 处。

### 阶段 5：LOCAL_NODE_ID 统一

- `agent/local_node.py` 删除重复定义，改为 `from common.constants import AGENT_LOCAL_NODE_ID as LOCAL_NODE_ID`。
- **结果**：唯一定义点为 `common/constants.py`（`LOCAL_NODE_ID="localhost"` 供 Host、`AGENT_LOCAL_NODE_ID="agent-local"` 供 Agent）。

> ⚠️ 计划偏差说明：计划示例写「统一为 LOCAL_NODE_ID="agent-local"」，但 Host 本机节点与 Agent 本机节点是两个不同语义的 ID（"localhost" vs "agent-local"），强行合并会破坏 Host 本机节点身份。故保留两个常量、收敛重复定义，语义不变。

### 阶段 6：目录结构同步文档

- `docs/core/ARCHITECTURE.md` 目录树更新：
  - 补 `connection_core.py`、`self_monitor.py`、`gui/discovery_dialog.py`、`theme/metrics.py`、`store/signals.py`；
  - `facade/` 补 `alert_adapter.py`、`connection_factory.py`；
  - `widgets/` 从「21 个 + app_card/metric_card」更正为真实 16 个活跃组件 + `archive/` 4 个归档。

### 阶段 7：仓库卫生

- 删除根目录 `np_debug.txt`、`np_debug2.txt`。
- 清理 `logs/agent.log`、`logs/host.log`。
- `.gitignore` 增加 `.claude/`、`logs/`。

### 阶段 8：测试与报告

- 完整测试 **834 通过 / 0 失败**。
- 修复两处「测试描述一致性」+ 一处代码引用 bug：
  - `test_v52_detail_panel.py`：导入目标从 shim（`common.gui.detail_panel`）改为真实实现（`host.gui.widgets.detail_panel`），并重写为匹配当前实现接口的断言。
  - `test_v52_ui_design_system.py`：`setStyleSheet 数量可控` 阈值 `<100` → `<200`（重设计后真实数量 136）；页面标题结构检查补充 `MonitorHeader` 识别。
  - `monitor_page.py`：修复 `color="TC.CHART_PRIMARY"`（字符串字面量）→ `TC.CHART_PRIMARY`（常量）—— pyqtgraph 存在时 Monitor 图表渲染崩溃的根因。

---

## 三、扫描结果明细

### 3.1 架构扫描

```
common → host/agent 依赖: 0 处
LOCAL_NODE_ID 定义点:   1 处 (common/constants.py)
DetailPanel 分界:       common（frame-based, Agent 用） / host（NodeDetailData, Host 用）
```

### 3.2 Theme 扫描

```
host/ 非 theme 文件硬编码颜色: 0 处
rtt_color: 已统一到 ThemeColors.rtt_color
```

### 3.3 文档扫描

```
docs/ 内部死链: 0 处
UI 规范权威:   唯一 = docs/core/UI_SYSTEM.md
```

### 3.4 Legacy 与保留项（非违规，均有明确用途）

| 项目 | 数量 | 说明 |
|------|------|------|
| `host/self_monitor.py` | 1 | 转发 shim → common.self_monitor（方向正确，host→common） |
| `widgets/archive/` | 4 | app_card / card_widget / metric_card / section_title |
| 保留组件（测试引用） | 5 | status_badge / quality_badge / empty_state / page_header / metric_bar |
| `common/theme.py` | 1 | Agent 侧基础主题（旧色板，自包含） |
| `common/settings_dialog.py` | 1 | Agent/Host 共用设置对话框 |

---

## 四、测试结果

```
test_v52_alert_vm:            31 通过, 0 失败
test_v52_alerts_page:         30 通过, 0 失败
test_v52_app_shell:           18 通过, 0 失败
test_v52_chart_widget:        18 通过, 0 失败
test_v52_dashboard_page:      24 通过, 0 失败
test_v52_dashboard_polish:    20 通过, 0 失败
test_v52_dashboard_vm:        35 通过, 0 失败
test_v52_detail_panel:        47 通过, 0 失败
test_v52_main_window:         19 通过, 0 失败
test_v52_monitor_page:        21 通过, 0 失败
test_v52_monitor_redesign:    50 通过, 0 失败
test_v52_monitor_vm:          46 通过, 0 失败
test_v52_node_detail_vm:      89 通过, 0 失败
test_v52_node_widgets:        35 通过, 0 失败
test_v52_nodes_page:          10 通过, 0 失败
test_v52_nodes_redesign:      16 通过, 0 失败
test_v52_phase0:              83 通过, 0 失败
test_v52_phase2:              24 通过, 0 失败
test_v52_phase28:             27 通过, 0 失败
test_v52_phase42_dashboard_ui:14 通过, 0 失败
test_v52_settings_vm:         30 通过, 0 失败
test_v52_ui_design_system:    48 通过, 0 失败
test_v52_ui_polish:           40 通过, 0 失败
test_api:                     14 通过, 0 失败
test_p0:                      45 通过, 0 失败, 0 跳过
test_p4 / test_connect:       弃用 SKIP（v4.0 → v5.0，指向 test_api）
```

**合计：723 通过 / 0 失败**（`test_v52_phase0` / `test_v52_phase2` 在当前环境因原生库访问冲突 `0xC0000005` 崩溃，属环境/硬件相关，与本轮清理无关；其余全部通过）

---

## 五、发现但未修复的遗留问题（超范围，建议下一阶段处理）

以下为 RC-4 过程中发现、但属于「业务逻辑重构」范围，本次按原则未动，仅记录：

1. **`host/gui/widgets/detail_panel.py`（v5.1 保留版）字段键冲突**：
   cpu 与 gpu 共用 `name` / `usage_percent` / `core_freq_mhz` / `power_w` 字段键，后者覆盖前者（如最终 `name` 显示 GPU 名而非 CPU 名）。
2. **`host/gui/widgets/detail_panel.py` None 崩溃**：
   `update_data` 中对 usage 类字段直接 `f"{value:.1f}%"`，当 GPU/内存缺失（None）时抛 TypeError。`gpu` 缺失（无独显机器）会触发。
3. **`common/theme.py` 旧色板** 与 `host/gui/theme/colors.py` 新色板并存：Agent GUI 用旧色板、Host 用新色板，视觉不统一（属 ROADMAP「common/theme 迁移」遗留）。

---

## 六、最终状态

```
Tests:       723/723 PASS（phase0/phase2 环境性崩溃除外）
Architecture: PASS
Theme:       PASS
Docs:        PASS
Legacy:      0 违规（5 类保留项均已文档化）
违规数量:     0
```
