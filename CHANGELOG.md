# Changelog

## v5.3.4（2026-08-18）— UI Experience + Security + P1 Batch

### Added

- Devices Page（设备卡片网格：Stats Row + 名/状态/CPU·RAM·GPU 进度条/IP/时间）
- Dashboard Recent Activity（告警预览：红/黄圆点 + 节点/时间）
- Retention Settings UI（设置页 → Monitoring 区域：metrics/alerts/sessions 天数）
- Alert Recovery Detection（AlertStore 增加恢复事件 + 恢复卡片显示）

### Fixed

- P1-1: WS 鉴权竞态（先发 auth_result 再入订阅集合）
- P1-2: POST /api/config 落盘 + 类型校验 + log_level 实时生效
- P1-3: UDP 明文 token → token_hash 摘要（Host 发现对话框要求输入 token）
- P1-4: Database PRAGMA synchronous=NORMAL + busy_timeout=5000
- P1-5: --tray 双服务启动（托盘不可用时单进程后台）
- P1-6: Dashboard QTimer 轮询 → Signal 驱动（frame_updated 100ms debounce）
- R-1: Host 侧自动发现适配 token_hash（存 hash + 对话框输入 token）
- R-2: health 版本号统一为 "5.3.4"
- R-3: log_level 应用到 agent 根 logger（propagate=False 兼容）
- device_card.py:74 addWidget → addLayout（QVBoxLayout 传递修复）
- Settings dirty 双模型收敛（Page 委托 VM 标记）
- 版本号统一（README + 6 个 docs + health → v5.3.4）

### Changed

- history.db 路径：`%APPDATA%/LAN-PC-Monitor/data/history.db`（不再依赖启动 CWD）
- netifaces 替换为 psutil（`get_lan_ip` / `get_default_gateway`）
- Dashboard 2.0：System Overview（4 MetricBar + 阈值变色）
- History UX：时间按钮 + Metric Checkbox + 多曲线 Chart + tooltip + Summary

### Validation

- Tests：**994/994 PASS**

---

## v5.2.3（2026-08-15）— Architecture Stabilization Release

> **里程碑**：本项目从"开发阶段"进入"稳定维护阶段"的分界点（Release 发布日）。
> 发布后 v5.2.x 冻结，进入 v5.3 开发周期。

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
