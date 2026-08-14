# Phase 5-4 History UI Plan

> **Status**: FROZEN
> **Design**: Desktop Grafana + Gentelella 混合风格
> **Framework**: PyQt5 + pyqtgraph + RC-7 Theme Tokens
> **Architecture**: Page → VM → Facade → Repository → SQLite

---

## 1. 整体布局

```
MainWindow
├── SideNav (全局导航，History ★ 已注册)
└── HistoryPage
       ├── HistoryHeader    (Node + Metric + Range 选择器)
       ├── HistoryChart     (ChartWidget 折线图)
       └── HistorySummary   (AVG / MAX / MIN / COUNT)
```

沿用 MainWindow 框架，Sidebar 不在页面内。

---

## 2. 技术选型（冻结）

| 项 | 选型 |
|----|------|
| Charts | pyqtgraph（复用 ChartWidget） |
| Theme | RC-7 tokens（ThemeColors/Spacing/Typography） |
| Layout | MVVM + Facade |

**禁止**：ECharts / QtCharts / 新图表库 / 自绘 QPainter

---

## 3. HistoryHeader

```
┌──────────────────────────────────────────┐
│  Node:  [ DESKTOP-01 ▼ ]                 │
│  Metric: [ CPU Usage ▼ ]                 │
│  Range:  [Last 1h ▼]                     │
│                              [ Load ]     │
└──────────────────────────────────────────┘
```

- NodeSelector: QComboBox
- MetricSelector: QComboBox
- RangeSelector: QPushButton 组（5m/30m/1h/6h/24h）
- Load: QPushButton 触发查询

不做：自动刷新 / 时间轮询 / WebSocket 更新

---

## 4. HistoryChart + Summary

```
┌───────────────────────────────────┐
│  ChartWidget (pyqtgraph)          │
│  ─ 折线趋势图                     │
│  ─ 阈值线                         │
├───────────────────────────────────┤
│ ┌──────┐ ┌──────┐ ┌──────┐      │
│ │ AVG  │ │ MAX  │ │ MIN  │      │
│ │ 42%  │ │ 91%  │ │ 12%  │      │
│ └──────┘ └──────┘ └──────┘      │
└───────────────────────────────────┘
```

复用：ChartWidget + SummaryCard

---

## 5. 页面状态

### Empty State
```
📈
No history data available
Start monitoring to collect metrics
```

### Loading State
```
Loading history...
```

---

## 6. 新增文件

```
host/viewmodels/history_vm.py      # 数据转换
host/gui/pages/history_page.py     # 历史趋势页
tests/test_v52_history_page.py     # 测试
```

---

## 7. 验收

| 项目 | 目标 |
|------|------|
| HistoryVM / HistoryPage 存在 | ✅ |
| Page → VM → Facade 单向 | ✅ |
| ChartWidget / SummaryCard 复用 | ✅ |
| 无硬编码颜色 | ✅ |
| tests pass | ✅ |
