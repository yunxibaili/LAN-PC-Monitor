# RC-7 Theme Token Consolidation Plan

> **Status**: DRAFT (待冻结)
> **Scope**: Host 侧 token 接线收口，不改变视觉表现
> **原则**: 收口、降债、稳定边界 — 不做视觉重构

---

## 1. 目标

将当前 Theme 三层状态：

```
host/gui/theme/colors.py        ← 当前生产色板（语义层）
host/gui/theme/spacing.py       ← 当前生产间距
host/gui/theme/typography.py    ← 当前生产字体
common/theme_tokens.py          ← 已创建但未接线（基础层）
common/theme.py                 ← legacy（Agent 使用）
```

收敛为：

```
common/theme_tokens.py          ← 基础设计令牌（单一来源）
        │
        ├── host/gui/theme/colors.py     ← 语义映射（引用 theme_tokens）
        ├── host/gui/theme/spacing.py    ← 引用 theme_tokens
        └── host/gui/theme/typography.py ← 引用 theme_tokens
```

**最终目标**：
- Host 侧 token 单一来源
- 语义层与基础层分离
- 保留兼容入口，不破坏已有调用
- common/theme.py 保持 legacy，不迁移

---

## 2. 非目标（必须写死）

RC-7 **不做**：

| 禁止 | 原因 |
|------|------|
| ❌ UI redesign | 属于 Phase 4-6/4-7 |
| ❌ 色彩方案调整 | 会引入视觉回归 |
| ❌ spacing 数值优化 | 会引入布局回归 |
| ❌ 字体策略改变 | 会引入渲染差异 |
| ❌ Agent GUI 重构 | 属于 Phase 4-7 |
| ❌ 修改 common/theme.py | Agent 依赖，RC-7 不迁移 |
| ❌ 删除 legacy 文件 | 需保留兼容入口 |
| ❌ 修改业务页面 | RC 只收口，不改功能 |
| ❌ 创建新 token 文件 | 防止第四套来源 |

---

## 3. 当前问题记录

### P1: Token 重复定义

| 文件 | 内容 | 角色 |
|------|------|------|
| `common/theme_tokens.py` | `COLOR_BG_DARK = "#0F1117"` | 基础层（未接线） |
| `host/gui/theme/colors.py` | `BACKGROUND_PRIMARY = "#0F1117"` | 语义层（生产使用） |

相同值，两套定义。

### P2: common/theme.py legacy

当前 `common/theme.py` 包含 Agent 仍使用的：
- `DARK_QSS`（深色主题 QSS）
- `COLOR_*` 旧色板（与 host/gui/theme 不同色值）
- `usage_color()` 等 helper
- `apply_color()` / `remove_help_button()`

**RC-7 不修改此文件**。保持 legacy 状态，由 Phase 4-7 Agent GUI Upgrade 决定最终方案。

### P3: common/theme.py 引用统计

| 引用方 | 文件数 | 说明 |
|--------|--------|------|
| host/ | 0 | RC-4 已清除 |
| agent/ | 3 | main.py ×2, gui/main_window.py |
| common/ | 2 | connect_dialog.py, settings_dialog.py |
| tests/ | 1 | test_p0.py |

---

## 4. 实施阶段

### RC-7A: Host Theme Token Wiring

**范围**：`common/theme_tokens.py` → `host/gui/theme/`

**目标**：colors.py / spacing.py / typography.py 的基础值来自 theme_tokens

**方案**：

**colors.py 分层设计**：

```python
# host/gui/theme/colors.py
from common.theme_tokens import ThemeTokens

class ThemeColors:
    # ---- 基础 token：来自 common/theme_tokens.py ----
    BACKGROUND_PRIMARY = ThemeTokens.COLOR_BG_DARK       # "#0F1117"
    BACKGROUND_SURFACE = ThemeTokens.COLOR_BG_SURFACE    # "#161B22"
    BACKGROUND_CARD = ThemeTokens.COLOR_BG_CARD          # "#1C2333"

    TEXT_PRIMARY = ThemeTokens.COLOR_TEXT_PRIMARY         # "#E6EDF3"
    TEXT_SECONDARY = ThemeTokens.COLOR_TEXT_SECONDARY     # "#8B949E"
    TEXT_DISABLED = ThemeTokens.COLOR_TEXT_DISABLED       # "#484F58"

    ACCENT_PRIMARY = ThemeTokens.COLOR_ACCENT            # "#3B82F6"
    STATUS_ONLINE = ThemeTokens.COLOR_SUCCESS            # "#22C55E"
    STATUS_WARNING = ThemeTokens.COLOR_WARNING           # "#F59E0B"
    STATUS_ERROR = ThemeTokens.COLOR_DANGER              # "#EF4444"
    ALERT_INFO = ThemeTokens.COLOR_INFO                  # "#60A5FA"

    BORDER_DEFAULT = ThemeTokens.COLOR_BORDER            # "#21262D"

    # ---- 语义 token：保留 host/gui/theme/colors.py 现有定义 ----
    # 这些属于 Host UI 语义层，不经过 theme_tokens
    TEXT_ON_COLOR = "#FFFFFF"
    BACKGROUND_ELEVATED = "#1E293B"
    BACKGROUND_HOVER = "#253049"
    BACKGROUND_INPUT = "#0D1117"
    CHART_PRIMARY = "#3B82F6"
    CHART_SECONDARY = "#F59E0B"
    CHART_THRESHOLD_WARN = "#F59E0B"
    CHART_THRESHOLD_DANGER = "#EF4444"
    BAR_BG = "#21262D"
    BAR_SUCCESS = "#22C55E"
    BAR_WARNING = "#F59E0B"
    BAR_DANGER = "#EF4444"
    TABLE_HEADER_BG = "#161B22"
    TABLE_ALT_ROW = "#141920"
    TABLE_GRID = "#21262D"
    TABLE_HOVER = "#1C2333"
    # ... 其他语义 token 保持不变
```

**关键区分**：
- 基础 token（来自 theme_tokens）：跨端稳定，Host/Agent 可共享
- 语义 token（保留 colors.py）：Host UI 专用，不强制迁移

**spacing.py**：

```python
# host/gui/theme/spacing.py
from common.theme_tokens import ThemeTokens

class ThemeSpacing:
    XS = ThemeTokens.SPACING_XS
    SM = ThemeTokens.SPACING_SM
    MD = ThemeTokens.SPACING_MD
    LG = ThemeTokens.SPACING_LG
    XL = ThemeTokens.SPACING_XL
    XXL = ThemeTokens.SPACING_XXL
```

**typography.py**（直接转换，保持现有 API）：

```python
# host/gui/theme/typography.py
from common.theme_tokens import ThemeTokens

class ThemeTypography:
    FAMILY = ThemeTokens.FONT_FAMILY

    # 值转换："24px" → 24（int）
    TITLE_LG = {
        "size": int(ThemeTokens.FONT_SIZE_TITLE_LG.replace("px", "")),
        "weight": "bold"
    }
    TITLE_MD = {
        "size": int(ThemeTokens.FONT_SIZE_TITLE_MD.replace("px", "")),
        "weight": "bold"
    }
    BODY = {
        "size": int(ThemeTokens.FONT_SIZE_BODY.replace("px", "")),
        "weight": "normal"
    }
    # ... 同理

    def css(self) -> str:
        """返回 CSS 格式字符串（保持现有 API）。"""
        return f"font-family: {self.FAMILY}; font-size: {self.TITLE_LG['size']}px;"
```

**关键**：外部 API（`TT.TITLE_LG` / `TT.css()`）不变，只改内部来源。

**验收**：
- colors.py 基础 token 无独立 hex（语义 token 可保留 hex）
- spacing.py 基础值来自 theme_tokens
- typography.py 值来自 theme_tokens
- 现有调用 `TC.XXX` / `S.XXX` / `TT.XXX` 不变

### RC-7B: Legacy Theme Boundary Clarification

**范围**：仅文档

**目标**：明确 common/theme.py 的 legacy 身份

**方案**：

在 `common/theme.py` 头部增加文档说明：

```python
"""
Legacy Theme System — Agent GUI 兼容层。

状态: legacy
用途: Agent GUI 当前依赖此模块
迁移: Phase 4-7 Agent GUI Upgrade 时决定

Host GUI 不使用此模块。
新开发应使用 host/gui/theme。
"""
```

**不修改任何代码**。

**验收**：
- common/theme.py 文件头有 legacy 标记
- 不修改 Agent QSS / COLOR_* / DARK_QSS
- 不删除任何内容

---

## 5. theme_tokens 职责范围

### 基础设计令牌（theme_tokens 负责）

| 类别 | 示例 |
|------|------|
| 颜色 | `COLOR_BG_DARK`, `COLOR_TEXT_PRIMARY`, `COLOR_SUCCESS`, `COLOR_ACCENT` |
| 间距 | `SPACING_XS`, `SPACING_SM`, `SPACING_MD`, `SPACING_LG` |
| 字体 | `FONT_FAMILY`, `FONT_SIZE_TITLE_LG`, `FONT_SIZE_BODY` |
| 圆角 | `RADIUS_CARD`, `RADIUS_BUTTON` |

### 语义 token（colors.py 保留）

| 类别 | 示例 |
|------|------|
| 图表 | `CHART_PRIMARY`, `CHART_THRESHOLD_WARN` |
| 表格 | `TABLE_HEADER_BG`, `TABLE_ALT_ROW` |
| 进度条 | `BAR_BG`, `BAR_SUCCESS` |
| 状态 | `STATUS_OFFLINE`, `STATUS_ONLINE` |

这些语义 token 由 colors.py 定义，不经过 theme_tokens。

---

## 6. 风险控制

### 风险 1: 旧 import 不受影响

```python
# 这些调用保持不变
from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
```

**策略**：只改内部来源，不改外部 API

### 风险 2: common/theme.py 使用者

当前引用统计：
- agent/: 3 处
- common/: 2 处
- tests/: 1 处

**策略**：RC-7 不修改 common/theme.py，保持现状

### 风险 3: 值差异

theme_tokens 和 colors.py 的当前值必须完全一致。

**策略**：先比对所有 token 值，确认一致后再接线

### 风险 4: Agent 视觉回归

**策略**：RC-7 不碰 common/theme.py，Agent 视觉不变

---

## 7. 完成标准

### RC-7A 验收

| 检查 | 标准 |
|------|------|
| TC API | 现有调用 `TC.XXX` 全部通过 |
| typography API | `TT.TITLE_LG` / `TT.css()` 无破坏 |
| colors.py 基础 token | 无重复 hex（来自 theme_tokens） |
| colors.py 语义 token | 可保留独立 hex |
| spacing.py | 基础值来自 theme_tokens |
| common/theme.py | 内容不变 |
| host/gui 非 theme 区 | 无硬编码颜色 |
| 全量测试 | 0 回归 |

### RC-7B 验收

| 检查 | 标准 |
|------|------|
| common/theme.py | 文件头有 legacy 标记 |
| Agent QSS | 不变 |
| Agent COLOR_* | 不变 |
| DARK_QSS | 不变 |

---

## 8. 不允许的操作

| 禁止 | 原因 |
|------|------|
| 创建新的 theme_constants.py | 防止第四套来源 |
| 创建新的 ui_tokens.py | 防止第四套来源 |
| 修改 common/theme.py | Agent 依赖，Phase 4-7 再处理 |
| 修改 Page / Widget 布局 | RC 不做 UI |
| 修改色彩方案 | 会引入视觉回归 |
| 修改 Agent QSS | 会改变 Agent 视觉 |
| 替换 Agent COLOR_BG / COLOR_ACCENT | 会改变 Agent 视觉 |

---

## 9. 后续路线

```
v5.2-rc1
   │
   ├── RC-4  consistency
   ├── RC-5  baseline
   ├── RC-6  foundation
   ├── Phase 4-5  alerts
   ├── Phase 4-6  settings
   └── RC-7  theme token consolidation
          │
          ▼
   v5.2 architecture stable
          │
          ▼
   Phase 5     历史数据 SQLite
   Phase 4-7   Agent GUI Modernization (common/theme.py 迁移在此决定)
   Phase 5-2   i18n / Productization
   v1.0
```
