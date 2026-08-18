# Architecture Decisions (ADR)

> 关键架构决策记录。替代历史 phase/report 文档。
> 为什么这样做——防止未来遗忘。**这不是开发依据，只读。**

---

## ADR-001: 为什么用 psutil 替代 netifaces

**状态**: 已实施（v5.3.1）

**原因**: netifaces 0.11.0（2021 停更）PyPI wheel 仅到 cp39；Python 3.12+ 全新安装因 distutils 移除直接失败；3.10/3.11 CI 需 sdist 编译约 40s。

**方案**: `get_lan_ip()` / `get_default_gateway()` 改用 psutil（已在依赖树，零新增依赖）。

---

## ADR-002: 为什么 history.db 用 %APPDATA%

**状态**: 已实施（v5.3.1）

**原因**: `StorageService("history.db")` 依赖进程 CWD。换启动方式（桌面/CMD/IDE）= 换数据库，数据割裂。

**方案**: `%APPDATA%/LAN-PC-Monitor/data/history.db`（storage_service.get_default_db_path），目录自动创建。

---

## ADR-003: 为什么不用 QTimer 轮询

**状态**: 已实施（v5.3.4）

**原因**: 架构声明 "Signal 驱动零延迟"，QTimer 轮询违反该原则且造成 ≤2s 数据滞后。

**方案**: Dashboard 用 frame_updated 信号 + 100ms singleShot debounce（非轮询）。

---

## ADR-004: 为什么 UDP 发现不广播明文 token

**状态**: 已实施（v5.3.4，安全加固）

**原因**: 明文 token 广播到整个局域网，同网段嗅探即可窃取后直连 Agent。

**方案**: 广播 `token_hash`（sha256[:8]）；Host 发现后需用户在发现对话框输入 token 才能连接。

---

## ADR-005: 为什么 WS 先发 auth_result 再入订阅

**状态**: 已实施（v5.3.4）

**原因**: 先入订阅集合再发 auth_result，push_loop 可能抢先广播 monitor_data，Host 首帧误判 auth_failed 且停止重连。

**方案**: 先 `send_str(auth_result)` 成功后再 `_subscribers.add(ws)`。

---

## ADR-006: 为什么 StorageService 独立组装 Storage 层

**状态**: 已实施（v5.2 Phase 5-5B）

**原因**: 让 MainWindow 不直接碰 Database/Repository，生命周期统一管理。

**方案**: `StorageService` 组装 Database + 3 个 Repository + HistoryFacade + RetentionService。

---

## ADR-007: 为什么数据库用 synchronous=NORMAL

**状态**: 已实施（v5.3.4）

**原因**: 每秒全量写入 + 主线程同步 commit（synchronous=FULL 含 fsync）卡 GUI。

**方案**: WAL 已保证崩溃安全，synchronous=NORMAL 降低 fsync 频率 + busy_timeout=5000 防死锁。

---

## ADR-008: 为什么分层禁止 Page → Store 直访

**状态**: 架构原则（v5.2）

**原因**: 保持 MVVM 单向数据流，VM 是唯一数据转换层，避免 UI 直接依赖存储实现。

**方案**: Page → ViewModel → Facade → Service → Repository → SQLite。

---

## ADR-009: 为什么 UI 参考 Gentelella 但提取原则

**状态**: v5.4 设计方向

**原因**: Gentelella 是 Web 后台模板，直接复制会产出"网页感"的 Qt 应用；本项目是 Windows 桌面监控软件。

**方案**: 提取信息层级/卡片布局/颜色语义，结合 Grafana 信息密度 + Windows Fluent 桌面规范 → docs/UI_GUIDE.md（唯一 UI 真相）。
