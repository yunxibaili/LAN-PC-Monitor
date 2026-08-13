# -*- coding: utf-8 -*-
"""
v5.2 Host Store 层 —— 分片状态容器（纯逻辑 + Qt 信号）。

设计（见 docs/v5.2_migration_plan.md Phase 0 / docs/v5.2_architecture_review.md）：
- 将 v5.1 MainWindow 散落状态拆为 4 个分片 Store：
    NodeStore      节点连接/状态/RTT/丢包/评分
    FrameStore     最新帧缓存
    HistoryStore   历史 deque（v6 由 storage/ 取代）
    AlertStore     告警 + 30s 去重 + 计数
- 统一 Signal 规范：changed / updated / removed / reset（见 signals.py）。
- 所有 Store 纯逻辑实现，不依赖 UI；Qt 信号通过 store/signals.py 统一提供。

约束：不修改 connection_core.py / connection.py / collectors / AlertEngine / REST API。
"""
