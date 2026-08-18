# RC-5 Pre-Commit Audit Report

> **生成**: 2026-08-13
> **模式**: 只读检查（不修改任何代码）
> **目的**: 基线冻结前最终一致性审计

---

## 检查结果

| # | 检查项 | 结果 |
|---|--------|------|
| 1 | 未追踪文件 | ✅ 均为 v5.2 新模块（store/viewmodels/pages/widgets/theme/tests/docs/tools/.github） |
| 2 | 临时文件 (.tmp/.bak) | ✅ 0 处 |
| 3 | 日志文件 (.log) | ✅ 0 处（logs/ 已 gitignore） |
| 4 | 缓存目录 (__pycache__) | ✅ 18 个，均已 gitignore，无 tracked |
| 5 | 编译产物 (.pyc/.pyo) | ✅ 无 tracked；build/ 已 gitignore |
| 6 | 测试生成文件 | ✅ 无 |
| 7 | docs 死链 | ✅ 0 处 |
| 8 | host/gui 硬编码颜色 | ✅ 0 处（非 theme 文件） |
| 9 | common → host 依赖 | ✅ 0 处 |
| 10 | 旧 v5.1 UI 文件残留 | ✅ 仅 2 个已删除（host/gui/node_list.py、overview_grid.py） |
| 11 | 敏感文件 (.pcm/.json/token) | ✅ 0 处（agent_config/host_config 等已 gitignore） |

---

## Git 变更统计

| 类型 | 数量 | 说明 |
|------|------|------|
| Modified (M) | 18 | v5.2 架构迁移 + theme 收口 |
| Deleted (D) | 2 | host/gui/node_list.py、host/gui/overview_grid.py（v5.1 遗留） |
| Untracked (??) | 大量新目录 | host/store、viewmodels、gui/pages、widgets、theme、tests/test_v52_*、docs/、tools/、.github/ |

全部变更归属：**v5.2 架构迁移 / UI Design System / RC 清理报告 / 测试更新**。

---

## 已知环境问题（不阻塞）

- `test_v52_phase0` / `test_v52_phase2` 在当前环境以 `0xC0000005` 原生访问冲突崩溃。
- 详见 [rc5_environment_notes.md](rc5_environment_notes.md)。

---

## 结论

```
READY FOR COMMIT
```

所有检查项通过，无敏感信息、无临时/缓存文件、无死链、无硬编码颜色、无违规依赖。
