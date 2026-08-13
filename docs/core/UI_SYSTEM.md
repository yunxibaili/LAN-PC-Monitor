# 唯一 UI 设计规范

> **Version**: v5.2 Phase4
> **Status**: CURRENT — 所有 GUI 开发以此为准

## 1. Color Palette

| 用途 | 代码 | 常量 |
|------|------|------|
| Background Primary | `#0F1117` | `BACKGROUND_PRIMARY` |
| Background Surface | `#161B22` | `BACKGROUND_SECONDARY` |
| Background Card | `#1C2333` | `BACKGROUND_CARD` |
| Background Elevated | `#1E293B` | `BACKGROUND_ELEVATED` |
| Border Default | `#21262D` | `BORDER_DEFAULT` |
| Border Focus | `#3B82F6` | `BORDER_FOCUS` |
| Primary / Accent | `#3B82F6` | `ACCENT_PRIMARY` |
| Info | `#60A5FA` | `ALERT_INFO` |
| Success / Online | `#22C55E` | `STATUS_ONLINE` |
| Warning | `#F59E0B` | `STATUS_WARNING` |
| Danger / Critical | `#EF4444` | `STATUS_ERROR` |
| Text Primary | `#E6EDF3` | `TEXT_PRIMARY` |
| Text Secondary | `#8B949E` | `TEXT_SECONDARY` |
| Text Disabled | `#484F58` | `TEXT_DISABLED` |

引用方式：

```python
from host.gui.theme.colors import ThemeColors as TC
color = TC.ACCENT_PRIMARY  # 不是 "#3B82F6"
```

## 2. Typography

| 级别 | 字号 | 字重 | 用途 |
|------|------|------|------|
| Title Large | 24px | Bold | 页面大标题 |
| Title Medium | 20px | Bold | 区域标题 |
| Title Small | 16px | Bold | 卡片标题 |
| Body | 14px | Regular | 正文 |
| Body Small | 12px | Regular | 辅助文字 |
| Caption | 11px | Regular | 标签 |
| Numeric Large | 32px | Bold | 指标大数字 |
| Numeric Medium | 20px | Bold | 中等数字 |

字体栈：`Microsoft YaHei` / `Segoe UI` / `Consolas`

## 3. Spacing

| Token | 值 |
|-------|-----|
| XS | 4px |
| SM | 8px |
| MD | 12px |
| LG | 16px |
| XL | 24px |
| XXL | 32px |

引用方式：

```python
from host.gui.theme.spacing import ThemeSpacing as S
widget.setContentsMargins(S.LG, S.SM, S.LG, S.SM)
```

## 4. Radius

| 元素 | 圆角 |
|------|------|
| Card | 12px |
| Button | 6px |
| Badge | 12px |

## 5. 阈值变色

| 指标 | 绿 | 橙 | 红 |
|------|-----|-----|-----|
| CPU/GPU | < 80% | 80~95% | > 95% |
| 温度 | < 80°C | 80~85°C | > 85°C |
| 内存 | < 80% | 80~90% | > 90% |
| FPS | > 60 | 30~60 | < 30 |
| 网络评分 | >= 80 | 60~79 | < 60 |
| RTT | < 5ms | 5~20ms | > 20ms |

## 6. 组件规范

### AppCard（基础容器）

```
圆角 12px | 背景 #1C2333 | 边框 1px #21262D | Hover 边框变蓝
```

### StatusBadge

| 状态 | 颜色 |
|------|------|
| ONLINE | 绿 #22C55E |
| OFFLINE | 红 #EF4444 |
| WARNING | 黄 #F59E0B |

### NodeCard

```
┌─────────────────────────────┐
│ 🖥 Gaming-PC         ● ONLNE│
│ CPU     ████████░░  45%     │
│ GPU     ██████░░░░  65%     │
│ RAM     █████░░░░░  53%     │
│ Quality: 96  A              │
└─────────────────────────────┘
```

### ResourceCard（资源圆环）

```
┌─────────────────┐
│ CPU              │
│ [环形]  45%      │
│ 65°C             │
└─────────────────┘
```

## 7. 页面布局

### Dashboard

```
HeaderRow → SummaryCards(4) → NodeGrid(自适应) → BottomRow
```

### Nodes

```
NodeExplorer(左) + DetailDashboard(右)  [QSplitter]
```

### Monitor

```
MonitorHeader → MetricSelector(5 tabs) → ChartPanel(图表+卡片)
```

### Alerts

```
HeaderRow → SummaryCards(3) → AlertTable
```

### Settings

```
HeaderRow → 5-Tab(General/Alerts/Nodes/Appearance/Advanced)
```

## 8. 强制规则

1. ✅ 颜色引用 `ThemeColors`
2. ✅ 间距引用 `ThemeSpacing`
3. ✅ 字体引用 `ThemeTypography`
4. ❌ 禁止内联 QSS 硬编码颜色
5. ❌ 禁止重复 padding 定义
