# Archive 目录说明

> **Status**: 历史资料

## 用途

本目录存放项目历史设计文档，仅供回顾参考。

## 禁止

**禁止将 archive/ 中的文档作为开发依据。**

所有开发应参考 `docs/core/` 下的权威文档。

## 文件清单

| 文件 | 来源 | 说明 |
|------|------|------|
| `ui_design_v50.md` | 原 `ui_design.md` | v5.0 UI 设计 (已过期) |
| `unified_ui_design.md` | 原 `unified_ui_design.md` | 统一 UI 设计 (已合并) |
| `v52_ui_design_legacy.md` | 原 `v5.2_ui_design.md` | v5.2 旧 UI 设计 (已过期) |
| `v52_structure_audit.md` | 原 `v5.2_structure_audit.md` | 结构审计快照 |
| `v52_architecture_review.md` | 原 `v5.2_architecture_review.md` | 架构评审记录 |
| `v52_phase25_scan.md` | 原 `v5.2_phase2.5_scan.md` | Phase 2.5 扫描 |

## 正确用法

```python
# ✅ 正确：读取权威文档
read("docs/core/ARCHITECTURE.md")
read("docs/core/UI_SYSTEM.md")

# ❌ 错误：读取归档文档
read("docs/archive/v52_ui_design_legacy.md")
```
