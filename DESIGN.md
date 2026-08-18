# LAN-PC-Monitor 设计规范

> 基于 [Gentelella v4](https://github.com/ColorlibHQ/gentelella)（by ColorlibHQ）暗色模式。
> 本文件为唯一设计权威，所有新增/修改 UI 必须遵循。
> **Version**: v5.4

---

## 1. 设计令牌

### 1.1 颜色体系（Gentelella Dark Mode）

#### 背景层

| Token | 值 | 用途 |
|-------|-----|------|
| `body-bg` | `#0f1623` | 窗口/页面背景 |
| `bg-surface` | `#1a2332` | 卡片/侧栏/表面容器 |
| `bg-surface-secondary` | `#141d2b` | 表格表头/次级表面 |
| `bg-card` | `#1e2a3a` | 卡片（略亮于 surface） |
| `bg-elevated` | `#22303f` | 浮层/hover 状态 |
| `bg-hover` | `rgba(255,255,255,0.04)` | 导航项/列表项 hover |
| `bg-input` | `#141d2b` | 输入框背景 |

#### 文字层

| Token | 值 | 用途 |
|-------|-----|------|
| `text` | `#e6ebf2` | 主要文字 |
| `text-secondary` | `#b3bccb` | 次要文字/描述 |
| `text-muted` | `#8a93a3` | 弱化文字/标签 |
| `text-disabled` | `#5a6473` | 禁用/占位文字 |
| `text-inverse` | `#0f1623` | 反色文字（浅底深字） |

#### 主色 / 语义色

| Token | 值 | 用途 |
|-------|-----|------|
| `primary` | `#1ABB9C`（teal） | 主色调/强调/选中/链接 |
| `primary-dk` | `#169f85` | primary 深色（hover） |
| `primary-lt` | `rgba(26,187,156,0.14)` | primary 浅底（选中背景） |
| `green` | `#2fb344` | 成功/在线/正增长 |
| `yellow` | `#f59f00` | 警告/中等 |
| `red` | `#d63939` | 危险/离线/负增长 |
| `blue` | `#066fd1` | 信息/链接 |
| `azure` | `#4299e1` | 辅助信息 |
| `purple` | `#ae3ec9` | 紫色标记 |
| `cyan` | `#17a2b8` | 青色标记 |

#### 边框 / 阴影

| Token | 值 | 用途 |
|-------|-----|------|
| `border-color` | `rgba(255,255,255,0.08)` | 主边框（暗色模式） |
| `border-color-light` | `rgba(255,255,255,0.05)` | 细边框（表格/分隔） |
| `border-translucent` | `rgba(255,255,255,0.08)` | 卡片外边框 |
| `shadow` | `rgba(0,0,0,0.4) 0 2px 4px` | 标准阴影 |
| `shadow-card` | `border + rgba(0,0,0,0.3) 0 2px 4px` | 卡片阴影 |

### 1.2 字体系统

```
Font: Inter / Microsoft YaHei / Segoe UI / sans-serif
Base size: 14px (0.875rem)
Line height: 1.4286
Weights: 400 (normal) / 500 (medium) / 600 (bold)
```

| 级别 | 字号 | 字重 | 用途 |
|------|------|------|------|
| Title Large | 24px | Bold | 页面大标题 |
| Title Medium | 20px | Bold | 区域标题 |
| Title Small | 16px | Bold | 卡片标题 |
| Body | 14px | Regular | 正文 |
| Body Small | 12px | Regular | 辅助文字 |
| Caption | 11px | Regular | 标签/徽章 |

### 1.3 间距系统（4px 基准）

| Token | 值 | 用途 |
|-------|-----|------|
| `space-1` | 4px | 最小间距 |
| `space-2` | 8px | 紧凑间距 |
| `space-3` | 12px | 默认间距 |
| `space-4` | 16px | 松散间距 |
| `space-5` | 24px | 区域间距 |
| `space-6` | 32px | 大区域间距 |
| `space-7` | 48px | 页面级间距 |

### 1.4 圆角

| Token | 值 | 用途 |
|-------|-----|------|
| `radius-sm` | 4px | 按钮/输入框/徽章 |
| `radius` | 6px | 通用圆角 |
| `radius-lg` | 8px | 卡片/面板 |

---

## 2. 布局结构

### 2.1 页面布局

```
┌──────────────────────────────────────────┐
│ Sidebar (252px, fixed) │ Main Content    │
│                       │                 │
│ [Logo]                │ [Header Bar]    │
│                       │                 │
│ MONITOR               │ [Page Content]  │
│   ▣ 总览              │                 │
│   ▣ 设备              │                 │
│   ▣ 监控              │                 │
│   ⚠ 告警              │                 │
│ SYSTEM                │                 │
│   📈 历史             │                 │
│   ⚙ 设置              │                 │
│                       │                 │
│ ─────────             │                 │
│ 已连接设备             │                 │
│   ● PC-001            │                 │
└──────────────────────────────────────────┘
```

### 2.2 侧边栏

- 固定定位，宽度 252px（可折叠）
- 深色背景 `#1a2332`，底部 1px 分隔线
- Logo 区：图标 + 品牌名（teal 色）
- 导航项：图标 + 文字，hover 时背景半透明
- 激活项：左侧 3px teal 边框 + 文字白色
- 分组标题：小写字母 + 大写标签 + 间距 16px

### 2.3 顶栏

- 固定顶部，高度 56px
- 左侧：页面标题
- 右侧：搜索/通知/用户信息
- 背景：半透明 `rgba(20,29,43,0.85)`（暗色模式）

### 2.4 内容区

- 左边距 = 侧边栏宽度 + 24px
- 上边距 = 顶栏高度 + 24px
- 卡片网格：自适应列数

---

## 3. 组件规范

### 3.1 Card（卡片）

```
背景: bg-surface
边框: 1px border-color
圆角: 8px
阴影: shadow-card
Header: 12px 16px, 分隔线 border-color-light
Body: 16px 内边距
```

### 3.2 Button（按钮）

```
.btn-primary: bg=primary, color=white, hover=primary-dk
.btn-outline: bg=bg-surface, border=border-color, hover=bg-surface-secondary
.btn-sm: height=28px, font-size=12px
高度: 32px, 圆角: 4px, 字重: 500
```

### 3.3 StatusBadge（状态徽章）

```
内联 flex，6px 圆点 + 文字
.status-green: 绿 #2fb344
.status-yellow: 黄 #f59f00
.status-red: 红 #d63939
```

### 3.4 Progress（进度条）

```
高度: 5px, 背景: bg-surface-secondary, 圆角: 3px
bar: 圆角 3px, 颜色随阈值变化
```

### 3.5 Table（表格）

```
表头: bg-surface-secondary, 11px 大写, 0.3px 字距
行高: 8px 16px, 底部分隔线 border-color-light
hover: bg-surface-secondary
```

### 3.6 Stat Card（统计卡片）

```
左侧: 彩色 3px 边框（teal/green/yellow）
标题: 11px text-muted 大写
数值: 32px bold text
副标题: 12px text-secondary
```

### 3.7 Live Pulse（在线脉冲）

```
6px 绿色圆点 + 扩散动画（2s 循环）
动画: box-shadow 从 0→6px 扩散消失
prefers-reduced-motion 时禁用动画
```

### 3.8 Toggle Switch（开关）

```
高度 24px, 宽度 40px, 圆角 12px
背景: bg-surface-secondary → primary
滑块: 白色 18px 圆形
```

### 3.9 Chart Card（图表卡片）

```
Card 容器 + header（标题 + 时间范围按钮）+ 图表区
时间按钮: btn-sm, active 时 bg=primary
```

---

## 4. 页面模板

### 4.1 Dashboard（总览）

```
PageHeader: 标题 + 副标题
SystemOverview: 4 列 StatCard（CPU/GPU/RAM/Network）+ progress bar
TwoColumn:
  Left: ChartCard（折线图 + 时间按钮）
  Right: Recent Activity（告警列表）
DeviceGrid: 设备卡片网格（名称/状态/指标/IP/时间）
```

### 4.2 Devices（设备）

```
StatsRow: 在线/离线/警告/总数（StatCard）
DeviceGrid: 自适应列数，每卡包含：
  名称 + 别名
  StatusBadge
  3 列 MetricBar（CPU/RAM/GPU）
  IP + 最后通信时间
```

### 4.3 Monitor（监控）

```
MonitorHeader: 节点名 + 状态
MetricSelector: Tab 栏（CPU/GPU/RAM/Network/FPS）
ChartPanel: 大面积折线图 + SummaryCards
```

### 4.4 History（历史）

```
TimeRangeSelector: 按钮组（10min/1h/6h/24h/7d）
MetricCheckboxes: 多曲线选择
ChartWidget: 多曲线叠加 + tooltip
SummaryCards: Average/Peak/Samples
```

---

## 5. 图表规范

### 5.1 折线图

- 使用 pyqtgraph（惰性导入 + fallback）
- 多曲线叠加，每曲线独立颜色
- 十字准线 + tooltip（时间 + 值）
- 时间轴自适应格式（秒/分/时/天）
- 降采样：> 500 点自动时间桶聚合

### 5.2 颜色分配

| 指标 | 颜色 |
|------|------|
| CPU | `#1ABB9C`（teal） |
| GPU | `#2fb344`（green） |
| RAM | `#f59f00`（yellow） |
| Network Upload | `#d63939`（red） |
| Network Download | `#ae3ec9`（purple） |

---

## 6. 阈值变色规则

| 指标 | 正常 | 警告 | 危险 |
|------|------|------|------|
| CPU/GPU 使用率 | < 80% | 80~95% | > 95% |
| 内存使用率 | < 80% | 80~90% | > 90% |
| 温度 | < 80°C | 80~85°C | > 85°C |
| FPS | > 60 | 30~60 | < 30 |
| 网络评分 | >= 80 | 60~79 | < 60 |
| RTT | < 5ms | 5~20ms | > 20ms |

---

## 7. 致谢

本项目 UI 设计参考了 [Gentelella v4](https://github.com/ColorlibHQ/gentelella)（by ColorlibHQ），基于其暗色模式 token 体系对齐颜色方案。感谢 ColorlibHQ 提供的高质量开源 admin dashboard 模板。

---

## 8. 引用方式

```python
from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.theme.typography import ThemeTypography as TT

# 颜色
color = TC.ACCENT_PRIMARY   # #1ABB9C (teal)
bg = TC.BACKGROUND_PRIMARY  # #0f1623

# 间距
widget.setContentsMargins(S.LG, S.SM, S.LG, S.SM)

# 字体
f"font-size: {TT.TITLE_MEDIUM['size']}px; font-weight: bold;"
```
