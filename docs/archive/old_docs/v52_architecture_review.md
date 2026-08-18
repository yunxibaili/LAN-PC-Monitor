# v5.2 UI 设计文档 — 架构一致性审查报告

审查日期: 2026-08-11
审查对象: docs/v5.2_ui_design.md
对照基线: v5.1 实际代码 (host/ + common/ + agent/)

---

## 一、页面与现有模块对应

| v5.2 页面 | 对应 v5.1 模块 | 状态 |
|-----------|----------------|------|
| DashboardPage | host/gui/overview_grid.py (OverviewGrid) | 部分匹配 — v5.1 OverviewGrid 仅 6 项卡片，v5.2 需要重构为 NodeCard |
| NodesPage | host/gui/main_window.py (节点列表+详情) | 匹配 — v5.1 已有 NodeListWidget + DetailPanel |
| MonitorPage | 无对应 | **新增** — v5.1 无独立监控页面，详情嵌入在 NodesPage 右侧 |
| AlertsPage | 无对应 | **新增** — v5.1 告警仅在状态栏+托盘气泡，无独立页面 |
| SettingsPage | host/gui/main_window.py (_open_settings) | 部分匹配 — v5.1 有设置对话框入口，但 5 标签页需重构 |

结论: MonitorPage 和 AlertsPage 是全新模块，需从零实现。DashboardPage/NodesPage/SettingsPage 在 v5.1 有骨架，需大幅重构。

---

## 二、SettingsManager 配置入口

v5.2 设计文档暗示存在 SettingsManager 类，但 v5.1 实际没有。

### v5.1 现状

host/config.py 使用模块级函数 + 字典:
- DEFAULT_CONFIG: 静态字典常量 (10 个字段)
- load_config() / save_config(): 读写 host_config.json
- load_alerts() / upsert_host() / remove_host(): 业务函数

HostMainWindow 直接持有 self.cfg 字典，通过函数调用修改。

### v5.2 设计所需

Settings 页面 5 个标签页共 15+ 个设置项。v5.1 的 DEFAULT_CONFIG 只有 10 个字段，但 v5.2 设计预留了 7 个新字段 (theme, ui_scale, chart_refresh_ms, history_minutes, alert_dedup_seconds, ws_read_timeout, reconnect_interval)。

### 审查结论

**不匹配**。需要明确决策:

方案 A (推荐): 在 host/config.py 中扩展 DEFAULT_CONFIG，添加 v5.2 新字段，保持函数模式不变。Settings 页面直接读写 self.cfg 字典。

方案 B: 创建 SettingsManager 类封装配置逻辑，提供信号通知变更。增加复杂度但更规范。

---

## 三、HostState 拆分需求

v5.2 引入 HostState 作为全局状态容器，但 v5.1 没有此类。

### v5.1 现状 — HostMainWindow 持有的状态

```
self.cfg: dict                    # 配置
self.nodes: dict                  # node_id -> NodeConnection
self.frames: dict                 # node_id -> 最新帧
self.statuses: dict               # node_id -> 状态
self.rtts: dict                   # node_id -> RTT
self.losses: dict                 # node_id -> 丢包率
self.scores: dict                 # node_id -> (score, grade)
self.scorers: dict                # node_id -> QualityScorer
self.current_node: str            # 当前选中节点
self.local_pack: LocalCollectorPack  # 本机采集器
self.alert_engine: AlertEngine    # 告警引擎
self._alert_state: dict           # 告警去重状态
self._tray: QSystemTrayIcon       # 托盘图标
self._view_mode: str              # 视图模式
```

### v5.2 设计所需

```
HostState:
  nodes/frames/statuses/rtts/losses/scores  # 从 v5.1 迁移
  history: dict[node_id -> deque(300)]       # v5.1 不存在，需新增
  alerts: list[dict] + alert_count           # v5.1 不存在，需新增
  cfg + alert_rules                          # 从 v5.1 迁移
  local_pack                                 # 从 v5.1 迁移
```

### 审查结论

**需要拆分，但方式需调整**。

v5.1 散落在 HostMainWindow 的 16 个状态属性中。v5.2 要求拆出 HostState 类。但 v5.1 还有 4 个状态未在 HostState 中体现:
- scorers (QualityScorer 实例字典) — v5.2 遗漏
- current_node (当前选中节点) — v5.2 遗漏
- alert_engine (告警引擎实例) — v5.2 遗漏
- _tray (托盘图标) — v5.2 遗漏

建议 HostState 包含全部 20 个状态属性，不遗漏。

---

## 四、QTimer 刷新适合长期运行

### v5.2 设计

每页 1s QTimer 读取 state 并刷新 UI。

### v5.1 现状

纯信号驱动: NodeConnection.data_received 信号 -> MainWindow._on_data() -> 立即更新 UI。无 QTimer。零延迟。

### 审查结论

**QTimer 模式不适合 v5.2 的场景**。原因:

1. **信号驱动更精确**: v5.1 数据到达即更新，QTimer 1s 轮询最多引入 1s 延迟
2. **折线图需要连续数据**: QTimer 1s 固定采样可能丢失 Agent 推送的第 2 帧（Agent 也是 1s 推送，但时钟不完全对齐）
3. **长期运行风险**: QTimer 在 Qt 事件循环中每秒触发一次，16 个图表同时重绘可能导致卡顿
4. **性能兜底冲突**: SelfMonitor 降级时要把刷新频率从 1s 调到 2s，但 QTimer 固定 1s 无法调

建议: 保持 v5.1 的信号驱动模式，图表在信号回调中增量更新（每次数据到达 push 一个点）。不要引入 QTimer 轮询。

---

## 五、WebSocket 数据进入 UI

### v5.2 设计描述

```
Agent -> WS monitor_data -> NodeConnection._on_data -> MainWindow._on_data
```

### v5.1 实际路径 (含 Qt 信号)

```
Agent -> WS -> ConnectionCore callback("on_data")
  -> NodeConnection._on_data()
  -> self.data_received.emit(frame, node_id)   # Qt 信号跨线程
  -> MainWindow._on_data(frame, node_id)        # signal->slot
```

### 审查结论

**v5.2 描述省略了 Qt 信号转发层**。实际路径:

1. WS 线程收到帧 -> ConnectionCore 回调
2. NodeConnection._on_data() 在 WS 线程执行
3. data_received.emit() 通过 Qt 事件循环跨线程
4. MainWindow._on_data() 在主线程执行

这个信号层是 Qt 跨线程安全的关键。v5.2 文档应明确标注，否则实现者可能绕过信号直接回调导致线程安全问题。

---

## 六、monitor_data 字段与组件映射

### v5.2 设计需要的字段

| 字段 | 组件 | v5.1 采集器 | 状态 |
|------|------|------------|------|
| cpu.total_usage | GaugeCard 环形 | cpu_collector.py | 匹配 |
| cpu.per_core_usage | 每核心条形图 | cpu_collector.py L88 | 匹配 |
| cpu.package_temp_c | GaugeCard 底部 | cpu_collector.py | 匹配 |
| gpu.usage_percent | GaugeCard 环形 | gpu_collector.py | 匹配 |
| gpu.core_temp_c | GaugeCard 底部 | gpu_collector.py | 匹配 |
| gpu.engine_usage | 引擎柱状图 | gpu_collector.py L108/178 | 匹配 |
| gpu.vram_used_mb | GaugeCard 底部 | gpu_collector.py | 匹配 |
| ram.usage_percent | GaugeCard 环形 | ram_collector.py | 匹配 |
| ram.used_gb / total_gb | GaugeCard 底部 | ram_collector.py | 匹配 |
| net.upload_mb_s | NetworkCard | net_collector.py | 匹配 |
| net.download_mb_s | NetworkCard | net_collector.py | 匹配 |
| net.link_speed_mbps | NetworkCard | net_collector.py | 匹配 |
| fps.fps | FpsCard 大号数字 | fps_collector.py | 匹配 |
| fps.frame_time_ms | FpsCard 底部 | fps_collector.py | 匹配 |
| fps.low_1_percent | FpsCard 底部 | fps_collector.py | 匹配 |
| fps.window_title | FpsCard 底部 | fps_collector.py | 匹配 |
| net_quality.quality_score | ScoreCard 径向仪表 | QualityScorer | 匹配 |
| net_quality.latency_to_client_ms | ScoreCard 底部 | NodeConnection.rtt | 匹配 |
| net_quality.packet_loss_percent | ScoreCard 底部 | NodeConnection.loss | 匹配 |
| disk[].read_mb_s / write_mb_s | 磁盘折线图 | disk_collector.py | 匹配 |
| disk[].queue_depth | 磁盘面板 | disk_collector.py L115/142 | 匹配 |
| processes.top_cpu / top_gpu | 进程柱状图 | proc_collector.py | 匹配 |

### 审查结论

**字段映射全部匹配**。v5.1 采集器产出的所有字段都能被 v5.2 组件使用。无缺失字段。

---

## 七、未来 v6 扩展兼容

### v5.2 设计预留

| v6 可能变更 | v5.2 预留 | 审查 |
|-------------|-----------|------|
| Agent 被 Electron 替代 | Host 仅 WS/REST | 合理 — Host 不依赖 Agent 内部 |
| PyQt5 -> Qt6 | UI 与业务分离 | 合理 — HostState 可复用 |
| 多用户权限 | State 扩展 role | 合理 — 但需提前定义权限模型 |
| 云端部署 | Agent TLS | 合理 — Host 需支持 wss:// |
| 插件系统 | AlertEngine 扩展 | 合理 — 规则引擎可扩展 |

### 审查结论

v6 兼容预留合理。但有一个遗漏:

**v6 可能引入 Electron 前端**。v5.2 的 PyQt5 图表组件 (GaugeCard/RadialGauge 等) 无法直接在 Electron 中复用。v6 迁移时这些组件需要用 Web 技术重写。建议 v5.2 将图表逻辑与渲染逻辑分离:
- 图表数据计算放在 common/ 或独立模块 (纯 Python)
- 渲染放在 host/gui/ (PyQt5)
- v6 时只需重写渲染层

---

## 八、额外发现的不匹配

### 8.1 遗漏: 系统托盘

v5.1 有完整的 SystemTrayIcon (init_tray + show_tray_alert + closeEvent hide)。v5.2 设计文档完全未提及托盘。Settings 页面提到「最小化到托盘」但 Dashboard/Alerts 页面未描述托盘交互。

建议: 在 MainWindow 架构中明确托盘集成点。

### 8.2 遗漏: scorers 字典

v5.1 HostMainWindow.scorers 是 dict[node_id -> QualityScorer]，每个节点独立评分器。v5.2 HostState 未包含 scorers，暗示评分可能移入 HostState。但 QualityScorer 是有状态的 (deque 滑动窗口)，不应作为纯数据放入 State。

建议: scorers 保留在 MainWindow 或拆分为独立的 ScoreManager。

### 8.3 遗漏: current_node

v5.1 HostMainWindow.current_node 记录当前选中节点。v5.2 未在 HostState 中体现。

建议: current_node 属于 UI 状态 (当前选中哪个)，应放在 MainWindow 层而非 HostState (数据层)。

### 8.4 遗漏: _alert_state 去重逻辑

v5.2 设计 30s 时间窗口去重。v5.1 实际是状态变化去重 (上一次 red/warn vs 本次)，无时间窗口。

建议: 如果 v5.2 要改为时间窗口去重，需要在 HostState 或 AlertEngine 中新增 _last_alert_time 字典。

### 8.5 不匹配: ConnectDialog 类名

v5.2 提到 "ConnectDialog" 复用。v5.1 实际是 ConnectCodeDialog / ClipboardDialog / OnboardingDialog 三个独立类，无 ConnectDialog。

建议: 修正文档引用为三个类名。

### 8.6 不匹配: OverviewGrid 重构

v5.2 Dashboard 页面的 NodeCard 与 v5.1 的 OverviewCard 布局不同:
- v5.1 OverviewCard: 3 列 2 行 grid (CPU/GPU/内存/温度/FPS/评分)
- v5.2 NodeCard: 6 项指标并排 + 状态行 + 颜色条

v5.1 的 OverviewCard 不能直接复用为 NodeCard，需要重写。

---

## 九、总结

### 匹配项 (5/10)

| 检查项 | 状态 |
|--------|------|
| monitor_data 字段映射 | 匹配 |
| LocalCollectorPack | 匹配 |
| QualityScorer | 匹配 |
| AlertEngine | 部分匹配 |
| v6 兼容预留 | 合理 |

### 不匹配项 (5/10)

| 检查项 | 状态 | 严重度 |
|--------|------|--------|
| SettingsManager | v5.1 无独立类 | 中 — 需决策 |
| HostState | v5.1 无此类，且遗漏 4 个状态 | 高 — 需补充 |
| QTimer 刷新 | v5.1 信号驱动，v5.2 轮询 | 高 — 建议改回信号驱动 |
| 数据路径描述 | 省略 Qt 信号层 | 低 — 文档修正 |
| ConnectDialog 类名 | 实际是 3 个独立类 | 低 — 文档修正 |

### 遗漏项 (3)

| 遗漏 | 严重度 |
|------|--------|
| 托盘 SystemTrayIcon | 中 — v5.1 已有完整实现 |
| scorers 字典 | 中 — 评分器状态管理 |
| _alert_state 去重逻辑差异 | 低 — 设计与实现不一致 |
