# Phase 5-4 History UI Final Report

> **Generated**: 2026-08-13
> **Status**: COMPLETE
> **Scope**: 历史趋势可视化页面 + 审查修复收口

---

## 一、交付内容

| 文件 | 说明 |
|------|------|
| `host/viewmodels/history_vm.py` | 新增：数据转换 + 查询编排 |
| `host/gui/pages/history_page.py` | 新增：历史趋势页 |
| `host/facade/history_facade.py` | 扩展：新增 `from_path()` 工厂 |
| `host/gui/navigation/side_nav.py` | 新增 History 导航项 |
| `host/gui/controllers/navigation_controller.py` | 新增 history 标题 |
| `host/gui/main_window.py` | 注册 HistoryPage + VM |
| `tests/test_v52_history_page.py` | 新增 20 项测试 |

---

## 二、审查发现与修复

### P1 Fixed — MainWindow 分层违规

**Before**:
```python
# main_window.py 直接 import storage 底层类
from host.storage.database import Database
from host.storage.repositories.metrics_repo import MetricsRepository
self._history_db = Database("history.db")
self._history_db.connect()
self._history_facade = HistoryFacade(MetricsRepository(self._history_db))
```

**After**:
```python
self._history_facade = HistoryFacade.from_path("history.db")
```

**Result**: storage 初始化封装进 `HistoryFacade.from_path()`，MainWindow 不再触碰 storage 底层。

---

### P1 Fixed — SummaryCard 重复定义

**Before**: `history_page.py` 内重新定义 `SummaryCard`（与 `chart_panel.py` 重复）。

**After**: 复用 `from host.gui.widgets.chart_panel import SummaryCard`。

**Result**: 消除重复组件，符合冻结计划「复用 SummaryCard」。

---

### P2 Fixed — Page 访问 VM 私有属性

**Before**:
```python
metric = self._vm._current_metric
```

**After**:
```python
metric = self._metric_combo.currentData()
```

**Result**: Page 不再依赖 VM 内部状态。

---

### P2 Fixed — HistoryVM 文档修正

**Before**: 「不直接碰 Facade/Repository/SQLite」（自相矛盾）

**After**: 「不直接碰 Repository / SQLite（仅经 Facade）」

**Result**: 文档与实现一致。

---

### P2 Fixed — 无效 chart title 赋值移除

**Before**: `self._chart._title = ...`（改了属性但不更新 QLabel，无效）

**After**: 移除。

**Result**: ChartWidget title 由内部管理。

---

### P3 Fixed — 未使用 import 清理

移除 `QScrollArea`、`QWidget` 未使用导入。

---

## 三、验证

```
test_v52_history_page:  20/20 PASS
test_v52_history_query: 23/23 PASS
全量回归:              901/901 PASS
```

---

## 四、Known Deferred Item

**history.db 相对路径**

- 决策：推迟到统一运行时数据目录规划。
- 理由：应与 host_config / agent_config / 未来 migration 策略对齐。
- 不属于 Phase 5-4 范围。

---

## 五、Phase 5 进度

| 阶段 | 内容 | 状态 |
|------|------|------|
| 5-1 | Storage Foundation | ✅ COMPLETE |
| 5-2 | Metrics Persistence | ✅ COMPLETE |
| 5-3 | History Query API | ✅ COMPLETE |
| 5-4 | History UI | ✅ COMPLETE |
| 5-5 | Retention / Cleanup | Future |
