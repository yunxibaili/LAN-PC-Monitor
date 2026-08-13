# Deprecated

This document has been superseded by:

docs/core/UI_SYSTEM.md

---

# PC Monitor v5.2 — UI Design System (Authority)

> **Version**: v5.2 (Phase 4 Consolidated)
> **Status**: CURRENT — 唯一权威 UI 设计规范
> **Date**: 2026-08-12
> **Supersedes**: ui_design.md, unified_ui_design.md, v5.2_ui_design.md, ui_design_spec_v52.md

---

## 一、Design System

### 1.1 Color Palette (ThemeColors)

| 用途 | 颜色名 | 代码 | 常量 |
|------|--------|------|------|
| Background Primary | 深黑 | `#0F1117` | `BACKGROUND_PRIMARY` |
| Background Surface | 深灰蓝 | `#161B22` | `BACKGROUND_SECONDARY` |
| Background Card | 深蓝灰 | `#1C2333` | `BACKGROUND_CARD` |
| Background Elevated | 深蓝 | `#1E293B` | `BACKGROUND_ELEVATED` |
| Border Default | 低透明度灰 | `#21262D` | `BORDER_DEFAULT` |
| Border Focus | 蓝色 | `#3B82F6` | `BORDER_FOCUS` |
| Primary / Accent | 蓝色 | `#3B82F6` | `ACCENT_PRIMARY` |
| Success / Online | 绿色 | `#22C55E` | `STATUS_ONLINE` |
| Warning | 黄色 | `#F59E0B` | `STATUS_WARNING` |
| Danger / Critical | 红色 | `#EF4444` | `STATUS_ERROR` |
| Info | 浅蓝 | `#60A5FA` | `ALERT_INFO` |
| Text Primary | 浅白 | `#E6EDF3` | `TEXT_PRIMARY` |
| Text Secondary | 灰 | `#8B949E` | `TEXT_SECONDARY` |
| Text Disabled | 暗灰 | `#484F58` | `TEXT_DISABLED` |

### 1.2 Typography (ThemeTypography)

| 级别 | 字号 | 字重 | 用途 |
|------|------|------|------|
| Title Large | 24px | Bold | 页面大标题 |
| Title Medium | 20px | Bold | 区域标题 |
| Title Small | 16px | Bold | 卡片标题 |
| Body | 14px | Regular | 正文 |
| Body Small | 12px | Regular | 辅助文字 |
| Caption | 11px | Regular | 标签/注释 |
| Numeric Large | 32px | Bold | 指标大数字 |
| Numeric Medium | 20px | Bold | 中等数字 |

字体栈：`Microsoft YaHei` / `Segoe UI` / `Consolas`

### 1.3 Spacing (ThemeSpacing)

| Token | 值 |
|-------|-----|
| XS | 4px |
| SM | 8px |
| MD | 12px |
| LG | 16px |
| XL | 24px |
| XXL | 32px |

### 1.4 Radius

| 元素 | 圆角 |
|------|------|
| Card | 12px |
| Button | 6px |
| Input | 6px |
| Badge | 12px |
| Chart | 12px |

### 1.5 Animation

| Token | 值 | 用途 |
|-------|-----|------|
| FAST | 120ms | Hover 变色 |
| NORMAL | 200ms | 页面切换 |
| SLOW | 300ms | 卡片展开/折叠 |

### 1.6 Icons

使用 Unicode 符号：📊🖥📈🔔⚙ ●○◐

---

## 二、阈值变色规范

| 指标 | 绿 (正常) | 橙 (警告) | 红 (危险) |
|------|----------|----------|----------|
| CPU/GPU 使用率 | < 80% | 80~95% | > 95% |
| 温度 (CPU/GPU) | < 80°C | 80~85°C | > 85°C |
| 内存使用率 | < 80% | 80~90% | > 90% |
| FPS | > 60 | 30~60 | < 30 |
| 网络评分 | >= 80 | 60~79 | < 60 |
| RTT | < 5ms | 5~20ms | > 20ms |

---

## 三、组件规范

### 3.1 AppCard (基础容器)

所有卡片容器统一：
- 圆角 12px
- 背景 `#1C2333` (BG_CARD)
- 边框 1px `#21262D` (BORDER_DEFAULT)
- Hover: 边框变蓝 `#3B82F6` (ACCENT_PRIMARY)
- Padding: 16px

### 3.2 StatusBadge

| 状态 | 文字 | 颜色 |
|------|------|------|
| ONLINE | ONLINE | 绿 `#22C55E` |
| OFFLINE | OFFLINE | 红 `#EF4444` |
| WARNING | WARNING | 黄 `#F59E0B` |
| RECONNECTING | RECONNECTING | 黄 |
| AUTH FAILED | AUTH FAILED | 红 |

### 3.3 MetricCard

```
┌─────────────────┐
│ 标题 (12px 灰)  │
│ 48% ↑3%         │  大数字 32px + 趋势箭头
└─────────────────┘
```

### 3.4 NodeCard

```
┌─────────────────────────────┐
│ 🖥 Gaming-PC         ● ONLNE│  名称 + 状态
│                             │
│ CPU     ████████░░  45%     │  进度条 + 数值
│ GPU     ██████░░░░  65%     │
│ RAM     █████░░░░░  53%     │
│                             │
│ ↑12.3 ↓45.6 MB/s           │  网络
│ Quality: 96  A              │  评分
└─────────────────────────────┘
```

### 3.5 ResourceCard (资源圆环)

```
┌─────────────────┐
│ CPU              │  标签
│ [环形]  45%      │  环形进度 + 数值
│ 65°C 14/32GB     │  副指标
└─────────────────┘
```

### 3.6 PageHeader

所有页面顶部统一：
```
┌────────────────────────────────────────────┐
│  标题                          操作按钮区   │
│  描述文字                                    │
└────────────────────────────────────────────┘
```

---

## 四、Dashboard 总览页

### 4.1 布局

```
DashboardPage
├── HeaderRow: 标题 + 节点统计 + 筛选(全部/异常/在线)
├── SummaryCards: 4 个统计卡 (Total/Online/CPU/Alerts)
├── NodeGrid: QScrollArea → 自适应列数 (min 320px/卡)
│   ├── NodeCard (本机)
│   ├── NodeCard (游戏主机)
│   └── NodeCard (离线节点)
└── BottomRow: 最近告警摘要
```

### 4.2 筛选按钮

[全部] [异常] [在线]
- 全部：显示所有节点
- 异常：评分 < 80 或离线
- 在线：已连接

---

## 五、Nodes 节点管理页

### 5.1 布局

```
NodesPage (QSplitter 水平分割)
├── [左] NodeExplorer (280px)
│   ├── 搜索框
│   └── 节点列表 (NodeListItem)
└── [右] DetailDashboard
    ├── NodeHeader (名称 + 状态)
    ├── ResourceCards (CPU/GPU/RAM/Disk 2×2)
    └── DetailPanel (完整字段)
```

---

## 六、Monitor 实时监控页

### 6.1 布局

```
MonitorPage
├── MonitorHeader (节点名 + 状态 + 统计)
├── MetricSelector [CPU] [GPU] [RAM] [Network] [FPS]
└── ChartPanel
    ├── ChartWidget (大面积折线图)
    └── SummaryCards (Current/Average/Peak/Status)
```

### 6.2 图表规范

- 数据源：HistoryStore (maxlen=300, 5分钟)
- X轴：相对时间（秒）
- Y轴：使用率 0-100%；其他自动
- 曲线：2px 蓝色 (#3B82F6)
- 阈值：1px 虚线 橙(80%) + 红(95%)
- 网格：alpha 0.3

---

## 七、Alerts 告警中心

### 7.1 布局

```
AlertsPage
├── HeaderRow: 标题 + 筛选 + 清除
├── SummaryCards: 3个统计 (Critical/Warning/Total)
└── AlertTable: QTableWidget
    列: 时间 | 节点 | 指标 | 当前值 | 阈值 | 等级
```

---

## 八、Settings 设置页

### 8.1 5 个标签页

| 标签 | 内容 |
|------|------|
| General | 语言/开机自启/最小化到托盘 |
| Alerts | 开关/规则管理/恢复默认 |
| Nodes | 自动发现/UDP端口/重连间隔 |
| Appearance | 主题/缩放/卡片列数 |
| Advanced | 日志级别/调试/WS超时 |

---

## 九、强制规则

所有 GUI 文件必须：
1. 颜色引用 `ThemeColors` (host.gui.theme.colors)
2. 间距引用 `ThemeSpacing` (host.gui.theme.spacing)
3. 字体引用 `ThemeTypography` (host.gui.theme.typography)
4. 卡片使用 `AppCard` 或其子类
5. 标题使用 `PageHeader`
6. **禁止** 内联 QSS 硬编码颜色
7. **禁止** 重复 padding/间距定义

---

## 十、架构分层

```
Agent (采集)
  ↓ WebSocket
Connection (WS 客户端)
  ↓ Signal
Store (数据存储)
  ↓
ViewModel (数据转换)
  ↓
Page (页面容器)
  ↓
Widget (UI 组件)
  ↓
Theme (样式系统)
```

页面禁止直接访问 Store/Connection/ConfigManager。
ViewModel 禁止导入 PyQt5。

---

## 十一、文件清单

### Theme System

| 文件 | 职责 |
|------|------|
| `host/gui/theme/colors.py` | ThemeColors 颜色常量 |
| `host/gui/theme/spacing.py` | ThemeSpacing 间距常量 |
| `host/gui/theme/typography.py` | ThemeTypography 字体常量 |
| `host/gui/theme/style.py` | QSS 样式生成 |
| `host/gui/theme/components.py` | 组件样式 |
| `host/gui/theme/layout.py` | 布局常量 |
| `host/gui/theme/icons.py` | 图标 |
| `host/gui/theme/animation.py` | 动画常量 |

### Widgets

| 文件 | 职责 |
|------|------|
| `app_card.py` | 基础容器卡 |
| `node_card.py` | 节点概览卡 |
| `resource_card.py` | 资源圆环卡 |
| `metric_card.py` | 单指标卡 |
| `metric_bar.py` | 进度条 |
| `chart_widget.py` | 折线图 |
| `chart_panel.py` | 图表面板 |
| `status_badge.py` | 状态徽章 |
| `quality_badge.py` | 网络质量徽章 |
| `node_explorer.py` | 节点探索面板 |
| `detail_dashboard.py` | 节点详情仪表盘 |
| `monitor_header.py` | 监控页头部 |
| `metric_selector.py` | 指标选择器 |
| `header_bar.py` | 顶部导航栏 |
| `page_header.py` | 页面头部 |
| `section_title.py` | 区块标题 |
| `empty_state.py` | 空状态占位 |

### Pages

| 文件 | 职责 |
|------|------|
| `dashboard_page.py` | 总览页 |
| `nodes_page.py` | 节点管理页 |
| `monitor_page.py` | 实时监控页 |
| `alerts_page.py` | 告警中心 |
| `settings_page.py` | 设置页 |

### ViewModels

| 文件 | 职责 |
|------|------|
| `dashboard_vm.py` | Dashboard 数据转换 |
| `node_detail_vm.py` | 节点详情数据转换 |
| `monitor_vm.py` | Monitor 数据转换 |
| `alert_vm.py` | Alert 数据转换 |
| `settings_vm.py` | Settings 数据转换 |
