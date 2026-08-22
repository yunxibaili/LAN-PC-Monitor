# LAN-PC-Monitor UI 设计规范

> **Version**: v5.3.4
> **定位**: Professional Monitoring Console（专业运维监控控制台）
> **不是**: 后台管理系统、商城、普通 Dashboard
> **模式**: 亮色模式优先，所有元素直接借鉴参考项目，不自行生成

---

## 1. 设计原则

### 提取自（不复制）

| 参考来源 | 提取什么 | 不复制什么 |
|----------|---------|-----------|
| [Gentelella](https://github.com/ColorlibHQ/gentelella) | Sidebar 结构、Card 布局、Dashboard 密度、颜色语义 | Bootstrap、网页布局、商业后台风格 |
| Grafana | 信息层级、图表表达、实时数据展示 | 面板拖拽、插件体系 |
| Windows Fluent | 控件规范、桌面应用手感 | 动画、圆角过度 |

### 核心关键词

```
clean          干净简洁
dense info     信息密度高
technical      技术感
real-time      实时数据
low distraction 低干扰
```

### 禁止

- ❌ Bootstrap 风格
- ❌ 复制网页布局
- ❌ 新增随机颜色
- ❌ 独立页面风格
- ❌ 随意动画
- ❌ 修改已有 Theme Token
- ❌ ERP/商城/后台管理风格

---

## 2. 颜色系统（亮色模式）

### 背景层

| Token | 值 | 用途 |
|-------|-----|------|
| Primary | `#FFFFFF` | 主背景（白色） |
| Secondary | `#F9FAFB` | 表面容器（卡片/侧栏） |
| Card | `#F3F4F6` | 卡片背景 |
| Border | `#E5E7EB` | 边框/分隔线 |

### 文字层

| Token | 值 | 用途 |
|-------|-----|------|
| Primary | `#111827` | 主要文字/标题 |
| Secondary | `#6B7280` | 次要文字/描述 |
| Disabled | `#9CA3AF` | 禁用/占位 |

### 语义色

| 状态 | 值 | 用途 |
|------|-----|------|
| 正常 | `#22C55E` | 在线/正常/完成 |
| 警告 | `#EAB308` | 警告/中等 |
| 危险 | `#EF4444` | 离线/危险/错误 |
| 信息 | `#3B82F6` | 链接/选中/强调 |

### 图表颜色

| 指标 | 颜色 |
|------|------|
| CPU | `#3B82F6`（蓝） |
| GPU | `#A855F7`（紫） |
| RAM | `#22C55E`（绿） |
| Network | `#F97316`（橙） |

### 引用方式

```python
from host.gui.theme.colors import ThemeColors as TC
bg = TC.BACKGROUND_PRIMARY   # #FFFFFF
text = TC.TEXT_PRIMARY        # #111827
status = TC.STATUS_ONLINE    # #22C55E
```

---

## 3. 布局体系

### 主窗口

```
┌──────────────────────────────────────────────┐
│ HeaderBar                    [搜索] [通知] [⚙] │
├──────────┬───────────────────────────────────┤
│          │                                   │
│ Sidebar  │        Main Content Area          │
│ (220px)  │                                   │
│          │  ┌─────────────────────────────┐  │
│ 监控      │  │  Page Content               │  │
│  总览     │  │                             │  │
│  历史     │  │                             │  │
│  告警     │  │                             │  │
│ 网络      │  └─────────────────────────────┘  │
│  设备     │                                   │
│ 系统      │                                   │
│  设置     │                                   │
└──────────┴───────────────────────────────────┘
```

### Sidebar 规范

- 宽度: 220px
- 背景: `#F9FAFB`（亮色）
- Active: 左侧 3px accent bar (`#3B82F6`)
- 图标: 16-18px SVG（currentColor）
- 文字: 14px
- 分组标题: 10px 大写 + 字距

禁止:
- ❌ 大图标
- ❌ 彩色菜单
- ❌ 渐变背景

---

## 4. 信息密度原则

### Dashboard

```
第一层：System Overview（4 个 MetricCard 一行）
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ CPU    │ │ GPU    │ │ RAM    │ │Network │
│45.2 %  │ │62.0 %  │ │50.1 %  │ │57 Mbps │
│████░░░ │ │██████░ │ │█████░░ │ │███░░░░ │
└────────┘ └────────┘ └────────┘ └────────┘

第二层：双栏布局
┌──────────────────┬──────────────┐
│ Performance      │ Recent       │
│ History          │ Activity     │
│ [Chart]          │ [Alert List] │
└──────────────────┴──────────────┘

第三层：Device Status Cards
┌─────────┐ ┌─────────┐ ┌─────────┐
│ PC-001  │ │ PC-002  │ │ Server  │
│ ● 在线  │ │ ● 在线  │ │ ⚠ 警告  │
│ CPU 45% │ │ CPU 32% │ │ CPU 88% │
└─────────┘ └─────────┘ └─────────┘
```

### MetricCard 规范

- Title: 11px 大写
- Value: 24-32px bold
- Progress: 5px bar
- Status: 彩色左边条 3px
- 禁止: ❌ 只显示数字 ❌ 大面积颜色 ❌ 3D效果

---

## 9. 图表设计

### 折线图规范

- 数据类型：Trend Over Time（时间序列趋势）
- 背景: transparent
- 网格: `rgba(0,0,0,0.06)`
- 线宽: 2px，多系列用不同线型（实线/虚线/点线）
- 填充: 线下方 20% 透明度

### 颜色分配（按 Skill 建议）

| 指标 | 颜色 | 说明 |
|------|------|------|
| CPU | `#3B82F6`（蓝） | Primary |
| GPU | `#A855F7`（紫） | Secondary |
| RAM | `#22C55E`（绿） | Success |
| Network | `#F97316`（橙） | Accent |

### 降采样规则（按 Skill 建议）

- < 1000 点：SVG 直接渲染
- ≥ 1000 点：Canvas + 降采样
- > 10000 点：聚合到时间间隔

### Tooltip

- 十字准线跟随鼠标
- 显示: 时间 + 所有系列值
- 格式: `HH:MM:SS`

### 无障碍

- 不仅靠颜色区分系列（加线型/标签）
- 键盘焦点可查看数值
- 停用动画时显示静态快照

---

## 6. 状态反馈

### 在线状态

```
● 在线    #22C55E  (绿色实心圆)
● 离线    #6B7280  (灰色实心圆)
● 警告    #EAB308  (黄色实心圆)
● 连接中  #3B82F6  (蓝色闪烁)
```

### 告警级别

```
● CRITICAL  #EF4444  (红色)
● WARNING   #EAB308  (黄色)
● INFO      #3B82F6  (蓝色)
● RECOVERED #22C55E  (绿色)
```

---

## 7. 页面规范

### 7.1 Dashboard（总览）

布局: SystemOverview → 双栏(Chart+Alerts) → DeviceGrid

### 7.2 History（历史）

布局: TimeRangeButtons → MetricCheckboxes → Chart → SummaryCards

快捷按钮: 10min / 1h / 6h / 24h / 7d

### 7.3 Devices（设备）

布局: StatsRow → DeviceCardGrid

每卡: 名称/状态/指标进度条/IP/最后通信时间

### 7.4 Monitor（监控）

布局: MonitorHeader → MetricSelector(Tab) → ChartPanel

### 7.5 Alerts（告警）

布局: SummaryCards → AlertTimeline

### 7.6 Settings（设置）

布局: Sidebar(分区) → ContentStack

---

## 10. 交付前检查（Skill Pre-Delivery Checklist）

- [ ] 不用 emoji 做图标（用 SVG）
- [ ] 所有可点击元素有 cursor:pointer
- [ ] Hover 状态有平滑过渡（150-300ms）
- [ ] 文字对比度 ≥ 4.5:1
- [ ] 键盘导航可见焦点
- [ ] 尊重 prefers-reduced-motion
- [ ] 响应式：375px / 768px / 1024px / 1440px
- [ ] 图表：多系列用不同线型，不仅靠颜色区分
- [ ] 实时数据：标注更新时间，显示 stale 状态

## 11. 致谢

本项目 UI 设计参考了 [Gentelella v4](https://github.com/ColorlibHQ/gentelella)（by ColorlibHQ）的设计原则（布局体系、信息密度、颜色语义），并结合 Grafana 的信息层级和 Windows Fluent 的桌面应用规范。

感谢以下开源项目的灵感：
- [Gentelella](https://github.com/ColorlibHQ/gentelella) — Dashboard 布局与组件结构
- [Grafana](https://github.com/grafana/grafana) — 监控面板信息层级
- [Windows Fluent Design](https://developer.microsoft.com/en-us/fluentui) — 桌面控件规范

---

## 9. AI 开发指令

### 设计前必须输出

```
1. 页面 UI 结构说明
2. 组件列表（复用现有 / 新增）
3. 颜色使用（全部走 ThemeColors）
4. 数据来源（ViewModel 字段）
```

### 代码约束

- 颜色: ThemeColors
- 间距: ThemeSpacing
- 字体: ThemeTypography
- 组件: 复用 widgets/ 现有组件
- 架构: Page → ViewModel → Facade → Service
- 不增加业务逻辑到 Widget

### 禁止清单

- ❌ 新增颜色
- ❌ 新建重复组件
- ❌ 页面独立 CSS
- ❌ 随意修改布局
- ❌ 添加无需求功能
