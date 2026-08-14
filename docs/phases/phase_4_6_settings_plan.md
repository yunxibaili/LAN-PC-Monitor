# Phase 4-6 Settings Redesign Plan

> **Version**: v5.2
> **Status**: DRAFT（冻结目标，评审通过后执行）
> **Date**: 2026-08-13
> **前置**: Phase 4-5 Alerts + 4-5.1 已完成；RC-6 基线冻结（tag `v5.2-rc1`）

---

## 1. 目标

将 `SettingsPage` 从 QTabWidget 表单升级为符合 UI_SYSTEM 规范的 SaaS Desktop 风格，同时修复 Settings 链路上既有的**分层泄漏**与**数据绑定 bug**。

**原则**（沿用 RC 系列）：

- 不新增功能
- 不改 ConfigManager 存储逻辑、不改 AlertEngine / AlertStore / AlertVM 数据接口
- 只修 Settings 链路（Page / ViewModel / Facade 边界）

---

## 2. 现状问题清单（已核实）

### 2.1 架构泄漏（P1）

| # | 位置 | 问题 |
|---|------|------|
| A1 | `settings_vm.py:62` | `get_alerts()` 直接访问 `self._facade._mgr`，穿透 Facade 戳 ConfigManager 私有字段 |
| A2 | `settings_vm.py:66` | `get_alerts()` 内 `from host.config import DEFAULT_ALERTS`，VM 层直接依赖 host.config 模块 |
| A3 | `settings_vm.py:98-99` | `facade` property 把 Facade 暴露给外部；`settings_page.py:249` 的 `_on_save` 用 `vm.facade.save()` 穿透 VM |

### 2.2 功能 bug（P1）

| # | 位置 | 问题 |
|---|------|------|
| B1 | `settings_page.py:225-228` | 告警 tab 4 个红线控件读**不存在的扁平 key**（`cpu_red` / `gpu_temp_red` / `ram_red` / `fps_red_min`）。ConfigManager/Facade 没有这些 key，告警规则实际存在 `host_cfg["alerts"]` 列表（path 形如 `cpu.total_usage`）。结果：控件恒显示硬编码默认值，与真实告警规则脱节 |
| B2 | `settings_page.py:236-249` | `_on_save` **不写回**这 4 个告警值 → 改了不生效；且 8 个 `vm.set()` 各触发一次 `_facade.save()`（VM.set 内部有 save），最后再 `vm.facade.save()`，共 **9 次写盘 + 8 次信号** |

### 2.3 UI 债（P2/P3）

| # | 问题 |
|---|------|
| U1 | QTabWidget 老风格（UI_SYSTEM.md 要求 Sidebar + Section Card）|
| U2 | 缺 Appearance tab（现 4 tab：通用/告警/节点/高级；设计 5 tab：General/Alerts/Nodes/Appearance/Advanced）|
| U3 | 硬编码间距 `16 / 12 / 8`（`settings_page.py:40-41,74,105,...`），应改用 `ThemeSpacing` |
| U4 | 无 dirty state（修改后无视觉反馈）、无 validation、无 save 反馈（保存仅 `log.info`）|

### 2.4 测试债（P2）

| # | 问题 |
|---|------|
| T1 | 无 SettingsPage 测试，仅有 `test_v52_settings_vm.py`（30 项）|
| T2 | 无 validation 测试、无 save 反馈测试、无告警规则绑定测试 |

---

## 3. 分阶段计划

### 4-6A：架构清理（先修边界，不碰 UI）

**目标**：把 Settings 链路的分层泄漏和告警数据绑定修对。

改动项：

1. **`SettingsVM.get_alerts()` 去跨层**
   - 删除 `self._facade._mgr` 与 `from host.config import DEFAULT_ALERTS`
   - 改为走 `SettingsFacade.get_alerts()`（新增列表接口，内部委托 ConfigManager 读 `host_cfg["alerts"]`，缺失时回退默认规则）
   - 默认告警规则从 Facade/ConfigManager 层提供，VM 不再 import host.config

2. **移除 `SettingsVM.facade` property**
   - `settings_page.py:249` 的 `vm.facade.save()` 改由 VM 提供受控接口（如 `vm.save()`，内部只 save 一次）
   - 消除 Page → Facade 的穿透

3. **修复告警 tab 数据绑定（B1/B2）**
   - 4 个红线控件改为读写 `alerts` 列表中的真实 path（`cpu.total_usage` / `gpu.core_temp_c` / `ram.usage_percent` / 对应 FPS 规则）
   - 通过 `vm.get_alert(path)` / `vm.set_alert(path, ...)` 读写
   - `_on_save` 补上这 4 个值的写回

4. **消除重复 save**
   - `_on_save` 批量写值后统一 save 一次；VM 增加「批量 set」或「set 后延迟 save」策略，避免 9 次写盘

**验收**：`get_alerts()` 无 `_mgr`/`host.config` 引用；`facade` property 移除；告警控件读写真实 alerts path；保存只写盘 1 次。

### 4-6B：UI 重设计（Sidebar + Section Card）

**目标**：SettingsPage 视觉升级到 SaaS Desktop 风格。

改动项：

1. QTabWidget → 左侧 Sidebar（General/Alerts/Nodes/Appearance/Advanced）+ 右侧 Section Card
2. 新增 **Appearance** tab（主题、UI 缩放、卡片列数等）
3. 硬编码间距全部替换为 `ThemeSpacing`
4. 增加 dirty state（修改标记 + 视觉提示）、validation（UDP 端口范围等）、save 反馈（成功/失败 toast 或状态条）

**约束**：本阶段**只改布局与样式**，不引入新的保存逻辑；数据绑定沿用 4-6A 修好的链路。

**验收**：5 个 Section 齐全；无硬编码间距/颜色；有 dirty / validation / save 反馈；`python tests/test_v52_ui_design_system.py` 与 `test_v52_ui_polish.py` 通过。

### 4-6C：补测试（SettingsPage 0 → N）

**目标**：为 SettingsPage 建立测试覆盖，防止回归。

改动项：

1. 新增 `tests/test_v52_settings_page.py`：
   - VM 注入 + 5 Section 渲染
   - 控件值 → vm 回读（含告警红线 path 绑定）
   - dirty state 切换
   - validation 触发
   - save 只触发一次（可用 fake facade 计数）
2. 扩展 `test_v52_settings_vm.py`：
   - `get_alerts()` 走 Facade 的边界测试
   - 移除 `facade` property 后的接口测试

**验收**：SettingsPage 测试从 0 → N；`test_v52_settings_vm.py` 全绿；全量测试 0 失败。

---

## 4. 约束（明确不碰）

| 不碰 | 原因 |
|------|------|
| ConfigManager 存储逻辑 | 只通过 Facade 接口访问 |
| AlertEngine / AlertStore / AlertVM | 告警产生与去重不属于本阶段 |
| agent_config.json / host_config.json 直写 | 必须走 Facade → ConfigManager |
| 其他页面（Dashboard/Nodes/Monitor/Alerts） | 隔离 Settings 改动 |
| i18n 重构 | 延后到 Phase 5-2 |

---

## 5. 验收标准（整体）

```
4-6A: SettingsVM 无 _mgr/host.config 泄漏；facade property 移除；
      告警控件绑定真实 alerts path；保存写盘 1 次
4-6B: 5 Section (General/Alerts/Nodes/Appearance/Advanced)；
      无硬编码间距/颜色；dirty + validation + save 反馈齐全
4-6C: test_v52_settings_page.py 新增并通过；test_v52_settings_vm.py 扩展通过
全量: 0 失败（含环境性崩溃说明）
```

---

## 6. 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| 告警规则绑定改动触碰 AlertEngine 输入 | 告警行为变化 | 只改 Page/VM 读写的 key 映射，不碰 engine 判定逻辑 |
| 批量 save 策略改动影响即时生效语义 | 配置丢失 | VM 保留「单 set 即时 save」或引入「批量 set + 单次 save」显式接口，先定语义再改 |
| Sidebar 重设计牵动 MainWindow 布局 | 回归 | 4-6B 只改 SettingsPage 内部，不碰 MainWindow 容器 |
| validation 边界不明确 | 过度校验 | 4-6A 先冻结校验规则清单（端口/缩放/阈值范围），4-6B 再落地 |

---

## 7. 执行顺序（冻结）

```
4-6A 架构清理 → 评审 → 4-6B UI 重设计 → 评审 → 4-6C 补测试 → 归档
```

每一子阶段完成后跑全量测试并出小结，确认无回归再进入下一子阶段。
