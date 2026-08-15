# Changelog

## v5.2.3（2026-08）— Architecture Stabilization Release

### Added

- SQLite persistence（Phase 5-1/5-2：Database / Schema / Repository / Frame→Record 写入）
- History query API（Phase 5-3：range / latest / aggregate）
- History UI（Phase 5-4：HistoryPage 趋势图表）
- Retention cleanup system（Phase 5-5：RetentionPolicy + Startup Trigger）

### Fixed

- pyadl AMD driver crash：Agent 在无 AMD 驱动机器上启动即崩（pyadl import 抛 `ADLError` 未被捕获）
- CI encoding issue：Windows runner cp1252 管道打印中文 UnicodeEncodeError（check_env 秒退）
- netifaces 无 cp310+ wheel（登记 v5.3-1，不阻塞本版；3.10/3.11 由 runner MSVC 从 sdist 构建）

### Architecture

- Storage service boundary（Facade → Repository → SQLite，sqlite3 仅限 host/storage/）
- Theme token system（common/theme_tokens 单一来源，RC-7）
- 6 页面全部 COMPLETE：Dashboard / Nodes / Monitor / Alerts / History / Settings

### Validation

- Tests：**988/988 PASS**（明细见 `docs/reports/baseline_v5.2.3.txt`）
- CI：**Windows Python 3.10 / 3.11 全绿**
- 审计：`docs/reports/v5.2.3_release_audit.md`

---

## v5.2（2026-08）— UI Redesign + Storage Foundation

- Design System 统一主题 / App Shell（HeaderBar + SideNav）
- Dashboard / Nodes / Monitor / Alerts / Settings UI 升级
- Settings redesign（MVVM 隔离 / dirty/save 模型 / sidebar）
- Phase 5 Storage Foundation（SQLite + schema + repository）

## v5.0（2025）— Agent/Host 分离重构

- 前后端分离（Agent 服务端 + Host 监控端），WebSocket + REST
- 零配置自动发现（mDNS + UDP）
- 红线告警引擎

## 发布 Tag 策略

- 正式版本：`v5.x.y`（如 `v5.2.3`）
- Release Candidate：`v5.x.y-rcN`（如 `v5.2.3-rc1`）
- 发布验证点：`v5.x.y-release`（CI 验证后的不可变发布 tag）
- 开发验证：`main`
