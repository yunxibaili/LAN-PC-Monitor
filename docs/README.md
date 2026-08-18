# LAN-PC-Monitor 文档

> **Version**: v5.4
> **Status**: 产品迭代阶段
> **原则**: 文档从"开发记录"变为"使用说明"。旧设计已删除或归档，AI 只能读到当前真相。

局域网远程电脑监控系统。Agent（被监控端）采集硬件数据，Host（监控端）集中展示。

## AI 阅读顺序（第一优先）

| 顺序 | 文档 | 说明 |
|------|------|------|
| 1 | [UI_GUIDE.md](UI_GUIDE.md) | ⭐ 唯一 UI 规范（Professional Monitoring Console） |
| 2 | [ARCHITECTURE.md](ARCHITECTURE.md) | 架构、目录、数据流、分层规则 |
| 3 | [DEVELOPMENT.md](DEVELOPMENT.md) | 开发规范（新增页面/组件/测试流程） |
| 4 | [ROADMAP.md](ROADMAP.md) | 当前阶段和未来计划 |

> 如果旧代码和文档冲突：**以当前代码 + 上述文档为准**。

## 参考文档

| 文档 | 说明 |
|------|------|
| [known_issues.md](known_issues.md) | 已知问题登记 |
| [releases/v5.2.3.md](releases/v5.2.3.md) | 发布说明 |
| [design/](design/) | UI 设计稿（HTML 原型：Dashboard/Devices/History） |
| [archive/decisions.md](archive/decisions.md) | 架构决策记录（ADR，为什么这样做） |

## 禁止阅读

- ❌ `archive/` 下的旧 phase/report/design 文档（已删除）
- ❌ 旧 `ui_design_*` / `BLUEPRINT` / `DATA_FLOW`（已删除）
- ❌ 历史 `migration_plan` / `cleanup_plan`（已删除）
