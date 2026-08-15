# Contributing

感谢参与。项目已进入稳定期（v5.2.x frozen，见 `docs/releases/v5.2.x_freeze.md`）。

## 分层规则（强制）

允许：

```
Page
 ↓
ViewModel
 ↓
Facade
 ↓
Service
 ↓
Repository
 ↓
Storage
```

禁止：

| 禁止 | 原因 |
|------|------|
| Page → Storage / Repository | 跳层 |
| Widget → Repository / Store / ViewModel | 职责混乱 |
| ViewModel → PyQt5 / sqlite3 | 耦合 UI / 存储 |
| sqlite3 出现在 host/storage/ 之外 | 存储边界 |

## 开发前必读

1. `docs/core/BLUEPRINT.md` — 项目总蓝图
2. `docs/core/ARCHITECTURE.md` — 最终架构
3. `docs/core/DEVELOPMENT.md` — 开发规范
4. `docs/core/UI_SYSTEM.md` — UI 规范（唯一权威）

## 提交前检查

- [ ] 本地全量回归通过（基线见 `docs/reports/baseline_v5.2.3.txt`）
- [ ] CI 全绿（Windows Python 3.10 / 3.11）
- [ ] 无硬编码颜色 / 间距（走 host.gui.theme）
- [ ] 无 QTimer 轮询（Signal 驱动）
- [ ] v5.2.x 仅允许 crash / security / release-blocking 修复；新功能进 v5.3

## 代码规范

- UTF-8 编码、类型注解、中文 docstring
- Signal 命名 `snake_case`、Slot 命名 `_on_xxx`、Widget 命名 `PascalCase`
- 日志：`logging.getLogger("host.gui.xxx")`

## Bug 报告

使用 Issue 模板（`.github/ISSUE_TEMPLATE/bug_report.yml`），至少提供：Version / OS / Python / Steps / Expected / Actual / Logs。
