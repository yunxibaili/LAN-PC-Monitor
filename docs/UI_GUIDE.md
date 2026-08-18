# LAN-PC-Monitor UI Guide

> **唯一 UI 规范**。所有 GUI 开发以此为准。
> **Version**: v5.4
> **UI 参考**: [Gentelella v4](https://github.com/ColorlibHQ/gentelella)（暗色模式对齐）

---

## 1. 总原则

- 颜色、间距、字体全部走 Theme token，**禁止硬编码**
- 组件先查 `host/gui/widgets/` 是否已有，**禁止复制创建近似组件**
- 页面样式统一走 Theme，**禁止页面自己内联定义新样式**

---

## 2. 布局

```
MainWindow
├── HeaderBar (顶部导航)
├── SideNav (左侧栏)
└── ContentStack (页面容器)
    ├── DashboardPage
    ├── NodesPage
    ├── MonitorPage
    ├── AlertsPage
    ├── HistoryPage
    └── SettingsPage
```

每个页面结构：
- `PageHeader`（标题 + 副标题）
- 内容区（按页面类型不同）

---

## 3. 颜色（Gentelella Dark Mode 对齐）

| 用途 | 值 | 常量 |
|------|-----|------|
| 背景-主 | `#0f1623` | `TC.BACKGROUND_PRIMARY` |
| 背景-面 | `#1a2332` | `TC.BACKGROUND_SECONDARY` |
| 背景-卡片 | `#1e2a3a` | `TC.BACKGROUND_CARD` |
| 边框 | `rgba(255,255,255,0.08)` | `TC.BORDER_DEFAULT` |
| 主色/强调 | `#1ABB9C`（teal） | `TC.ACCENT_PRIMARY` |
| 成功/在线 | `#2fb344` | `TC.STATUS_ONLINE` |
| 警告 | `#f59f00` | `TC.STATUS_WARNING` |
| 危险/离线 | `#d63939` | `TC.STATUS_ERROR` |
| 文字-主 | `#e6ebf2` | `TC.TEXT_PRIMARY` |
| 文字-次 | `#b3bccb` | `TC.TEXT_SECONDARY` |
| 文字-禁用 | `#5a6473` | `TC.TEXT_DISABLED` |
| 图表-主 | `#1ABB9C` | `TC.CHART_PRIMARY` |
| 图表-次 | `#f59f00` | `TC.CHART_SECONDARY` |

引用方式：

```python
from host.gui.theme.colors import ThemeColors as TC
color = TC.ACCENT_PRIMARY  # 不是 "#3B82F6"
```

---

## 4. 字体

| 级别 | 字号 | 字重 | 用途 |
|------|------|------|------|
| Title Large | 24px | Bold | 页面大标题 |
| Title Medium | 20px | Bold | 区域标题 |
| Title Small | 16px | Bold | 卡片标题 |
| Body | 14px | Regular | 正文 |
| Body Small | 12px | Regular | 辅助文字 |
| Caption | 11px | Regular | 标签 |
| Numeric Large | 32px | Bold | 指标大数字 |

字体栈：`Microsoft YaHei` / `Segoe UI` / `Consolas`

---

## 5. 间距与圆角

| 间距 Token | 值 |
|-----------|-----|
| XS | 4px |
| SM | 8px |
| MD | 12px |
| LG | 16px |
| XL | 24px |

| 元素 | 圆角 |
|------|------|
| Card | 12px |
| Button | 6px |
| Badge | 12px |

```python
from host.gui.theme.spacing import ThemeSpacing as S
widget.setContentsMargins(S.LG, S.SM, S.LG, S.SM)
```

---

## 6. 阈值变色

| 指标 | 绿 | 橙 | 红 |
|------|-----|-----|-----|
| CPU/GPU | < 80% | 80~95% | > 95% |
| 温度 | < 80°C | 80~85°C | > 85°C |
| 内存 | < 80% | 80~90% | > 90% |
| FPS | > 60 | 30~60 | < 30 |
| 网络评分 | >= 80 | 60~79 | < 60 |

---

## 7. 组件规范

### 基础容器（AppCard 风格）

```
圆角 12px | 背景 #1C2333 | 边框 1px #21262D
```

### MetricBar（指标条）

```
标签 + 数值（右对齐）+ 进度条（6px 高，圆角，阈值变色）
```
位于 `host/gui/widgets/metric_bar.py`

### SummaryCard（汇总卡）

```
标题(小字) + 大数值(20-28px bold) + 副标题
```
位于 `host/gui/widgets/chart_panel.py`

### ChartWidget（折线图）

```
支持多曲线叠加 + 十字准线 + tooltip
```
位于 `host/gui/widgets/chart_widget.py`

### StatusBadge（状态徽章）

| 状态 | 颜色 |
|------|------|
| ONLINE | 绿 #2fb344 |
| OFFLINE | 红 #d63939 |
| WARNING | 黄 #f59f00 |

### NodeCard（节点卡）

```
┌─────────────────────────────┐
│ 🖥 Gaming-PC         ● ONLINE│
│ CPU     ████████░░  45%     │
│ GPU     ██████░░░░  65%     │
│ RAM     █████░░░░░  53%     │
│ Quality: 96  A              │
└─────────────────────────────┘
```

---

## 8. Do Not（禁止）

1. ❌ **禁止新增颜色** —— 颜色只能从 `ThemeColors` 引用；新增颜色必须先改 `common/theme_tokens.py` 再改 `host/gui/theme/colors.py`
2. ❌ **禁止复制组件** —— 复用 `host/gui/widgets/` 现有组件；若确实缺，先在 widgets/ 新增并加测试
3. ❌ **禁止页面自己定义样式** —— 页面只引用 Theme token，不在 Page 内写内联 QSS 色值
4. ❌ **禁止硬编码间距/字号** —— 用 `ThemeSpacing` / `ThemeTypography`
5. ❌ **禁止参考旧 UI 文档** —— archive/ 里的 `ui_design_*` 已废弃，一律以本文为准

---

## 9. 新增页面/组件流程

```
1. 复用 widgets/ 现有组件（SummaryCard / MetricBar / ChartWidget / NodeCard ...）
2. 确需新组件 → host/gui/widgets/xxx.py，只 import Theme
3. 页面 → host/gui/pages/xxx_page.py，继承 PageBase
4. 注册 → main_window.py _init_viewmodels / _init_ui
5. 测试 → tests/test_v52_xxx.py（含架构扫描 + Theme 扫描）
```

## 10. 致谢

本项目 UI 设计参考了 [Gentelella v4](https://github.com/ColorlibHQ/gentelella)（by ColorlibHQ），基于其暗色模式 token 体系对齐颜色方案。具体借鉴：

- 暗色模式色板（body-bg / surface / text / border）
- Sidebar 分组导航模式（section header + nav items）
- Stat card 样式（彩色左边条 + 大数值 + 标签）
- 间距/圆角/阴影比例

感谢 ColorlibHQ 提供的高质量开源 admin dashboard 模板。
