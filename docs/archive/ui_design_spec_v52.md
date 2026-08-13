# PC Monitor v5.2 — SaaS UI Design Specification

**定位**：专业远程电脑监控 SaaS Desktop Client
**风格**：Dark Mode / Premium / Minimal / Data Dense / Enterprise Monitoring

---

## 一、Design System

### 1.1 Color Palette

| 用途 | 颜色 | 代码 |
|------|------|------|
| Background Primary | 深黑 | #0F1117 |
| Background Surface | 深灰蓝 | #161B22 |
| Background Card | 深蓝灰 | #1C2333 |
| Border | 低透明度灰 | #21262D |
| Primary / Accent | 蓝色 | #3B82F6 |
| Success | 绿色 | #22C55E |
| Warning | 黄色 | #F59E0B |
| Danger/Critical | 红色 | #EF4444 |
| Info | 浅蓝 | #60A5FA |
| Text Primary | 浅白 | #E6EDF3 |
| Text Secondary | 灰 | #8B949E |
| Text Disabled | 暗灰 | #484F58 |

### 1.2 Typography

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

字体：`Microsoft YaHei` / `Segoe UI` / `Consolas`

### 1.3 Spacing

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

## 二、Dashboard 总览页

### 2.1 整体布局

```
+----------------------------------------------------------+
| Sidebar 220px  │  PageHeader: Dashboard                   │
|                │  "System overview and performance at     │
| PC Monitor     │   a glance"                    [30m ▼]  │
|                │                                          │
| Dashboard  ◉   │  ┌──────┐┌──────┐┌──────┐┌──────┐      │
| Nodes          │  │Total ││Online││AvgCPU││Alerts│      │
| Monitor        │  │  4   ││  3   ││ 42%  ││  2   │      │
| Alerts  (2)    │  │nodes ││75% on││+5% vs││1C 1W │      │
| Settings       │  └──────┘└──────┘└──────┘└──────┘      │
|                │                                          │
| ONLINE NODES   │  ┌────────────┐┌────────────┐           │
| ● Gaming-PC    │  │ Gaming-PC  ││ Workstation│ ...       │
| ● Workstation  │  │ CPU 45%    ││ CPU 28%    │           │
| ● Design-Mac   │  │ GPU 65%    ││ GPU 35%    │           │
| ● Offline-PC   │  │ RAM 53%    ││ RAM 42%    │           │
|                │  │ FPS 144    ││ FPS 120    │           │
|                │  │ Q: 96 A    ││ Q: 88 B    │           │
|                │  └────────────┘└────────────┘           │
|                │                                          │
|                │  ┌─────────────────────────────┐        │
|                │  │ System Trend (30m)          │        │
|                │  │ CPU 42%  GPU 41%            │        │
|                │  │ RAM 44%  Network 128MB/s    │        │
|                │  └─────────────────────────────┘        │
+----------------------------------------------------------+
```

### 2.2 Summary Cards（5 个）

| 卡片 | 主值 | 副值 | 右侧 |
|------|------|------|------|
| Total Nodes | 4 | "All monitored nodes" | 图标 |
| Online Nodes | 3 | "75% online" | 趋势图 |
| Average CPU | 42% | "↑ 5% vs yesterday" | 迷你折线 |
| Alerts | 2 | "1 Critical 1 Warning" | ⚠ 图标 |
| Network Quality | 92 | "Excellent" | 径向仪表 |

每个卡片高度 90px，宽度自适应。

### 2.3 Node Cards

每个节点卡片：
- 宽度：自适应（1~4列）
- 高度：200px
- 内容：节点名 + ONLNE badge + CPU/GPU/RAM 条形 + FPS + Quality 徽章
- 交互：hover 提升 + 边框高亮 + 点击跳转 Monitor

### 2.4 System Trend

右侧或底部趋势图区域：
- CPU / GPU / RAM / Network 四个迷你趋势
- 显示当前值 + 迷你折线

---

## 三、Nodes 节点管理页

### 3.1 整体布局

```
+----------------------------------------------------------+
| Sidebar  │  PageHeader: 节点管理        [+ 添加] [扫描]  │
|          │                                               │
| PC Monitor│  ┌──────────────┬─────────────────────────┐  │
|          │  │ NodeList     │  Gaming-PC    ONLINE      │  │
|          │  │              │                           │  │
|          │  │ ● Gaming-PC  │  Overview│HW│Proc│Net│Hist│  │
|          │  │ ● Workstation│  ┌────────────────────┐  │  │
|          │  │ ○ Offline-PC │  │ CPU 45%    GPU 65% │  │  │
|          │  │              │  │ RAM 53%    FPS 144 │  │  │
|          │  │              │  └────────────────────┘  │  │
|          │  │              │                           │  │
|          │  │              │  Hardware Information      │  │
|          │  │              │  CPU: Intel i7-12700K     │  │
|          │  │              │  GPU: RTX 3080             │  │
|          │  │              │  RAM: 32GB DDR4 3200MHz   │  │
|          │  │              │  OS: Windows 11 Pro 22H2  │  │
|          │  │              │  Uptime: 2d 14h 32m       │  │
|          │  │              │                           │  │
|          │  │              │  Temperature               │  │
|          │  │              │  CPU 58°C  GPU 72°C        │  │
|          │  │              │  Motherboard 45°C  SSD 38°C│  │
|          │  └──────────────┴─────────────────────────┘  │
+----------------------------------------------------------+
```

### 3.2 NodeList

每个节点项：
```
┌──────────────────────┐
│ ● Gaming-PC          │  绿色圆点 + 名称
│   192.168.1.100      │  IP 地址
│   RTT 0.45ms  96 A   │  RTT + 评分徽章
└──────────────────────┘
```
选中项：蓝色左侧边框 + 背景高亮

### 3.3 Detail Dashboard

右侧详情区有 5 个 Tab：
- **Overview**：CPU/GPU/RAM/FPS 实时指标卡 + 硬件信息
- **Hardware**：详细硬件规格（CPU型号/GPU型号/RAM规格/OS/Uptime）
- **Processes**：进程列表（CPU/GPU Top 进程）
- **Network**：网络详情（接口/上下行/质量/RTT）
- **History**：历史数据趋势

---

## 四、Monitor 实时监控页

### 4.1 整体布局

```
+----------------------------------------------------------+
| Sidebar  │  PageHeader: 实时监控                          │
|          │                                               │
| PC Monitor│  Select Node: [Gaming-PC ▼]                  │
|          │                                               │
|          │  [CPU] [GPU] [RAM] [Network] [FPS] [Score]   │
|          │                                               │
|          │  ┌─────────────────────────────────────────┐  │
|          │  │  CPU Usage                             │  │
|          │  │  Average: 42%  Max: 78%                │  │
|          │  │  ▁▃▅▇▆▅▃▁▃▅▇▆▅▃  渐变面积图          │  │
|          │  │  ────────────────────────────────       │  │
|          │  │  70%  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ (阈值)  │  │
|          │  │  30%  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─          │  │
|          │  │  0% ─────────────────────────           │  │
|          │  └─────────────────────────────────────────┘  │
|          │                                               │
|          │  [1min] [5min] [30min] [3 Hours] [6 Hours]   │
|          │                                               │
|          │  ┌──────────────────────┐ ┌──────────────┐   │
|          │  │ Stats                │ │ Info         │   │
|          │  │ Avg: 42% Max: 78%    │ │ Node: Gaming │   │
|          │  │ Min: 12% Samples: 60 │ │ CPU: i7-12700K│   │
|          │  └──────────────────────┘ └──────────────┘   │
+----------------------------------------------------------+
```

### 4.2 节点选择器

顶部下拉框：选择要监控的节点

### 4.3 指标选择按钮

```
[CPU] [GPU] [RAM] [Network] [FPS] [Score]
```
选中态：蓝色边框 + 蓝色背景

### 4.4 主图表区域

- 高度：400px
- 深色背景 #1C2333
- 网格线 #21262D
- 曲线：渐变面积填充
- 阈值线：橙色虚线
- Tooltip：悬停显示精确值
- 时间范围：1min / 5min / 30min / 3h / 6h

### 4.5 底部信息

两个卡片：
- Stats：Average / Max / Min / Samples
- Info：Node / CPU 型号

---

## 五、Alerts 告警中心

### 5.1 整体布局

```
+----------------------------------------------------------+
| Sidebar  │  PageHeader: Alerts                            │
|          │                                               │
| PC Monitor│  ┌──────────┐┌──────────┐┌──────────┐       │
|          │  │ Critical ││ Warning  ││ Total    │       │
|          │  │    1     ││    1     ││    2     │       │
|          │  │ Requires ││ Needs    ││ Last 24h │       │
|          │  │ attention││ attention││          │       │
|          │  └──────────┘└──────────┘└──────────┘       │
|          │                                               │
|          │  [All] [Critical] [Warning] [Info]          │
|          │                                               │
|          │  ┌─────────────────────────────────────────┐  │
|          │  │ LEVEL  │ NODE    │ EVENT        │ TIME  │  │
|          │  │--------│---------│--------------│-------│  │
|          │  │🔴CRIT  │Gaming-PC│CPU Usage High│ 2min  │  │
|          │  │        │         │95% > 90%     │       │  │
|          │  │--------│---------│--------------│-------│  │
|          │  │🟡WARN  │Worksta. │GPU Temp High │15min  │  │
|          │  │        │         │82°C > 80°C   │       │  │
|          │  │--------│---------│--------------│-------│  │
|          │  │🔵INFO  │Design-M │Connected     │ 1hr   │  │
|          │  └─────────────────────────────────────────┘  │
+----------------------------------------------------------+
```

### 5.2 统计卡片

3 个卡片：
| 卡片 | 数字 | 说明 | 颜色 |
|------|------|------|------|
| Critical | N | Requires immediate attention | 红色 #EF4444 |
| Warning | N | Needs attention | 黄色 #F59E0B |
| Total Alerts | N | Last 24 hours | 蓝色 #3B82F6 |

### 5.3 Filter Chips

```
[All] [Critical] [Warning] [Info]
```
选中态：蓝色背景

### 5.4 告警列表

每条告警：
```
┌────────────────────────────────────────────────┐
│ 🔴 CRITICAL  Gaming-PC  CPU Usage High         │
│              95% > 90% for 5 min    2 minutes │
├────────────────────────────────────────────────┤
│ 🟡 WARNING   Workstation GPU Temperature High  │
│              82°C > 80°C             15 minutes │
├────────────────────────────────────────────────┤
│ 🔵 INFO      Design-Mac  Node Connected        │
│              Node has been connected  1 hour   │
└────────────────────────────────────────────────┘
```

等级颜色：
- CRITICAL：红色背景 + 白色文字
- WARNING：黄色/橙色背景 + 深色文字
- INFO：蓝色背景 + 白色文字

---

## 六、Settings 设置页

### 6.1 整体布局

```
+----------------------------------------------------------+
| Sidebar  │  PageHeader: Settings                          │
|          │                                               │
| PC Monitor│  ┌─────────────────────┐ ┌───────────────┐  │
|          │  │ Settings Nav         │ │ General        │  │
|          │  │                      │ │                │  │
|          │  │ ● General            │ │ Language       │  │
|          │  │   Alerts             │ │ English   [▼]  │  │
|          │  │   Nodes              │ │                │  │
|          │  │   Appearance         │ │ Start with     │  │
|          │  │   Advanced           │ │ Windows [ON]   │  │
|          │  │   About              │ │                │  │
|          │  │                      │ │ Minimize to    │  │
|          │  │                      │ │ tray      [ON] │  │
|          │  │                      │ │                │  │
|          │  │                      │ │ Data &         │  │
|          │  │                      │ │ Performance    │  │
|          │  │                      │ │                │  │
|          │  │                      │ │ Data ret(d)    │  │
|          │  │                      │ │ Max history    │  │
|          │  │                      │ │ HW accel  [ON]│  │
|          │  │                      │ │                │  │
|          │  │                      │ │ [Save Changes] │  │
|          │  └──────────────────────┴───────────────┘  │
+----------------------------------------------------------+
```

### 6.2 左侧导航

| 项目 | 图标 |
|------|------|
| General | 🔗 |
| Alerts | 🔔 |
| Nodes | 🖥 |
| Appearance | 🎨 |
| Advanced | ⚙ |
| About | ℹ |

### 6.3 卡片式设置

每个设置分组用 CardWidget 包裹：
- 标题 + 分隔线
- 表单项：标签 + 输入控件 + 说明文字
- 蓝色主按钮 "Save Changes"

---

## 七、组件规范

### 7.1 PageHeader

所有页面顶部统一：
```
┌────────────────────────────────────────────┐
│  标题                          操作按钮区   │
│  描述文字                                    │
└────────────────────────────────────────────┘
```

### 7.2 AppCard

所有卡片容器统一：
- 圆角 12px
- 背景 #1C2333
- 边框 1px #21262D
- Hover: 边框变蓝 #3B82F6
- Padding: 16px

### 7.3 MetricCard

```
┌─────────────────┐
│ 标题 (12px 灰)  │
│ 48% ↑3%         │  大数字 32px + 趋势箭头
└─────────────────┘
```

### 7.4 StatusBadge

| 状态 | 圆点 | 文字 | 颜色 |
|------|------|------|------|
| ONLINE | ● | ONLINE | 绿 #22C55E |
| OFFLINE | ○ | OFFLINE | 红 #EF4444 |
| WARNING | ◐ | WARNING | 黄 #F59E0B |
| RECONNECTING | ◐ | RECONNECTING | 黄 |
| AUTH FAILED | ○ | AUTH FAILED | 红 |
| UNKNOWN | ○ | UNKNOWN | 灰 |

### 7.5 NodeCard

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
- 圆角 12px，hover 边框变蓝，轻微阴影
- 高度 200px，宽度 320px

---

## 八、动画规范

| 场景 | 动画 | 时长 |
|------|------|------|
| Button hover | 背景变色 | 120ms |
| Card hover | 边框变蓝 + 微升 | 200ms |
| 页面切换 | 淡入淡出 | 200ms |
| 卡片展开/折叠 | 高度动画 | 300ms |
| 图表数据滚动 | 平移 | 200ms |

---

## 九、强制规则

所有 GUI 文件必须：
- 颜色引用 `ThemeColors`
- 间距引用 `ThemeSpacing`
- 字体引用 `ThemeTypography`
- 卡片使用 `AppCard`
- 标题使用 `PageHeader`
- 禁止内联 QSS（除动画过渡）
- 禁止重复 padding/间距定义

---

## 十、文件清单

### 新增组件
- `host/gui/widgets/app_card.py`（已有）
- `host/gui/widgets/metric_card.py`（已有）
- `host/gui/widgets/node_card.py`（已有）
- `host/gui/widgets/status_badge.py`（已有）

### 修改页面
- `host/gui/pages/dashboard_page.py`
- `host/gui/pages/nodes_page.py`
- `host/gui/pages/monitor_page.py`
- `host/gui/pages/alerts_page.py`
- `host/gui/pages/settings_page.py`

### Design System
- `host/gui/theme/spacing.py`（已有）
- `host/gui/theme/layout.py`（已有）
- `host/gui/theme/animation.py`（已有）
- `host/gui/theme/typography.py`（已有）
- `host/gui/theme/components.py`（已有）
- `host/gui/theme/icons.py`（已有）
