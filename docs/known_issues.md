# v5.2.3 已知问题登记（Known Issues）

> **版本**: v5.2.3（Final Audit 快照）
> **生成**: 2026-08-15（v5.2.3 Final Audit）
> **原则**: 只登记、不修复 —— 保持 v5.2.x 稳定版本不被污染。修复统一排入 v5.3 / 未来计划。

---

## 遗留问题

| # | 问题 | 级别 | 计划 | 说明 |
|---|------|------|------|------|
| ~~1~~ | ~~history.db 路径统一~~ | ~~P2~~ | ~~v5.3~~ | ✅ 已修复（v5.3.1：`%APPDATA%/LAN-PC-Monitor/data/history.db`） |
| ~~2~~ | ~~Settings dirty 双模型~~ | ~~P2~~ | ~~v5.3~~ | ✅ 已修复（v5.3.4：Page 委托 VM 标记） |
| ~~3~~ | ~~Agent theme 迁移~~ | ~~P2~~ | ~~Phase 4-7~~ | ✅ 已修复（v5.3.4：Agent GUI 颜色统一到 ThemeColors；DetailPanel 保留 common/ 独立实现） |
| 4 | History downsample | P3 | 未来 | ✅ 已修复（v5.3.4：Facade 自动降采样 MAX_POINTS=500） |
| 5 | Controller 直连 host.config | P3 | 观察 | data_controller/window_controller 直接 upsert_host/save_config |
| 6 | storage_service → history_facade 反向依赖 | P3 | 观察 | 组合便利，依赖方向值得后续理顺 |
| ~~7~~ | ~~netifaces 无 cp310+ wheel~~ | ~~P2~~ | ~~v5.3-1~~ | ✅ 已修复（v5.3.1：替换为 psutil） |

---

## v5.3 计划顺序（P2 Cleanup Sprint）

| 序 | 内容 | 级别 | 理由 |
|----|------|------|------|
| v5.3-0 | Repository hygiene（CHANGELOG / README badge / Release 流程 / Issue & PR 模板） | P2 | 项目进入成熟期，先固定工程流程 |
| v5.3-1 | **netifaces 替换**（psutil.net_if_addrs / ifaddr） | P2 | CI 已暴露无 cp310+ wheel，影响 install/CI/deployment，基础设施优先 |
| v5.3-2 | **history.db 路径统一** | P2 | 涉及 storage_service / config / 用户数据目录，需稳定设计，不与 UI 混做 |
| v5.3-3 | **Settings dirty 双模型合并** | P2 | 内部模型整理，无外部依赖 |
| v5.3-4 | **Agent/Host Theme 统一**（common/theme.py 迁移） | P2 | 视觉 + 架构迁移，范围最大；视觉变化风险 > 架构收益，最后做 |

---

## 本环境已知环境问题（非产品缺陷）

| 项 | 值 |
|----|-----|
| 受影响测试 | `tests/test_v52_phase0.py`、`tests/test_v52_phase2.py` |
| 现象 | 进程以 `0xC0000005`（3221225477）原生访问冲突崩溃，无测试输出 |
| 依据 | 本机复现一致（0xC0000005），见 docs/archive/decisions.md（ADR 环境说明） |
| 备注 | 本机最终审计复现一致；疑与原生库/硬件采集相关，非代码回归 |

---

## 变更纪律

- v5.2.x 分支：**只修 P0 缺陷**（数据错误 / 崩溃 / 安全），不引入新功能。
- 上表 #1-#4 进入 v5.3 Roadmap；#5-#6 为观察项，随重构自然收敛。
- 本文件随每次 Final Audit 快照更新，不随功能开发滚动。
