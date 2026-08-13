# v5.2 Host UI 重构技术方案

版本: v5.2 设计稿 (基于 v5.1 已实现状态)
日期: 2026-08-11
目标: 将 Host 前端从 v5.1 纯文字面板重构为 Grafana/Netdata 风格的可视化监控大屏

---

## 一、MainWindow 架构

### 1.1 窗口结构

保留 HostMainWindow (QMainWindow) 为顶层窗口，新增 SideNav + contentStack 替换原有 splitter 布局。

```
HostMainWindow (QMainWindow)           <- 保留 v5.1 实例属性
+-- QMenuBar (菜单栏)
+-- centralWidget: QWidget
|   +-- QHBoxLayout (root)
|       +-- SideNav (200px)           <- 新增: 侧边导航栏
|       +-- contentStack              <- 新增: QStackedWidget 5页面
|           +-- [0] DashboardPage
|           +-- [1] NodesPage         <- 保留 v5.1 NodeList + DetailPanel
|           +-- [2] MonitorPage       <- 新增: 单节点深度监控
|           +-- [3] AlertsPage        <- 新增: 告警中心
|           +-- [4] SettingsPage      <- 新增: SettingsFacade 包装
+-- QStatusBar (底部: RTT/丢包/评分/Agent版本)
+-- TrayManager                       <- 新增: 包装 v5.1 _tray
```

HostMainWindow 保留 v5.1 所有实例属性 (nodes/frames/statuses/rtts/losses/scores/scorers/local_pack/alert_engine/_tray 等)。新增 UIState 和 ViewModel 层读取这些属性供页面渲染。

### 1.2 侧边导航栏 (SideNav)

5 个导航项 + 底部分隔 + 节点快速列表:
- Dashboard / Nodes / Monitor / Alerts / Settings
- 选中态: 左侧 3px 蓝条 #007acc + #2d2d30 背景
- 未读告警数徽标 (红色圆点 + 数字)
- 节点列表固定高度, 超出滚动
- 点击节点 -> 跳转 Monitor 页

### 1.3 内容区 (contentStack)

QStackedWidget 包含 5 个页面:
- [0] DashboardPage
- [1] NodesPage         <- 保留 v5.1 布局 (NodeList + DetailPanel)
- [2] MonitorPage       <- 新增
- [3] AlertsPage        <- 新增
- [4] SettingsPage      <- 新增

### 1.4 TrayManager (新增)

包装 v5.1 的 QSystemTrayIcon, 提供统一的托盘管理接口。

```python
class TrayManager:
    """包装 v5.1 MainWindow._tray, 提供告警气泡和状态更新。"""
    def __init__(self, tray: QSystemTrayIcon):
        self._tray = tray

    def show_alert(self, title: str, body: str, level: str = "warn"):
        """告警气泡: 红色=红线, 橙色=预警。"""
        self._tray.showMessage(title, body, QSystemTrayIcon.Warning, 2000)

    def update_status(self, connected: int, total: int):
        """更新托盘 tooltip。"""
        self._tray.setToolTip(f"PC Monitor: {connected}/{total} 节点在线")

    def hide(self):
        self._tray.hide()
```

v5.1 的 _init_tray() / _show_tray_alert() / closeEvent hide 逻辑保持不变, TrayManager 仅做接口封装。

---

## 二、页面导航结构

| 源 -> 目标 | 触发条件 |
|-----------|----------|
| 任意 -> Dashboard | 点击侧栏总览 |
| 任意 -> Nodes | 点击侧栏节点 |
| Dashboard -> Monitor | 点击总览卡片 |
| Nodes -> Monitor | 点击节点列表项 |
| Sidebar节点 -> Monitor | 点击侧栏节点 |
| Monitor -> Dashboard | 点击返回总览 |
| 任意 -> Alerts | 点击侧栏告警 |
| 任意 -> Settings | 点击侧栏设置 |

数据传递: HostMainWindow 保留 v5.1 所有实例属性。新增 UIState (页面视图状态) + ViewModel (数据转换层) 读取 HostMainWindow 属性。数据更新由 Qt Signal 驱动, 无 QTimer 轮询。

---

## 三、Dashboard 页面

### 3.1 布局

```
DashboardPage
+-- headerRow: 标题 + 节点统计 + 筛选(全部/异常/在线)
+-- nodeGrid: QScrollArea -> QGridLayout (自适应列数, min 320px/卡)
|   +-- NodeCard (本机)
|   +-- NodeCard (游戏主机)
|   +-- NodeCard (直播机)
|   +-- NodeCard (办公电脑 - 离线)
+-- bottomRow: 最近 3 条告警摘要
```

### 3.2 NodeCard 设计

每张卡片 = 一个节点的 6 项关键指标快照:

```
+---------------------------------------------+
| 游戏主机                       192.168.1.100 |  <- 头部
|   已连接  RTT 0.45ms        98 优秀          |  <- 状态行
+---------------------------------------------+
| CPU    GPU    内存      网络       FPS        |  <- 指标标签
| 45%    62%   14/32GB   up12/dn45   142       |  <- 数值
| [bar]  [bar]  [bar]     [lines]  [number]    |  <- 可视化
+---------------------------------------------+
```

卡片颜色条: 绿(正常)/橙(警告)/红(危险), 取所有指标中最差状态.

| 指标 | 可视化 | 颜色函数 |
|------|--------|----------|
| CPU | QProgressBar | usage_color() |
| GPU | QProgressBar | usage_color() |
| 内存 | QProgressBar | usage_color() |
| 网络 | 双行QLabel | COLOR_TEXT |
| FPS | 大号QLabel 24px | fps色彩 |
| 评分 | 径向圆环 36px | score_color() |

### 3.3 筛选按钮

全部 / 异常 (评分<80或离线) / 在线

---

## 四、Nodes 页面

### 4.1 布局

```
NodesPage
+-- headerRow: 标题 + 搜索框 + 添加/扫描/导入/导出
+-- bodySplitter (Horizontal)
    +-- [left] NodeList (280px, 含搜索过滤)
    +-- [right] NodeDetailPanel
        +-- [0] 空状态占位
        +-- [1] 节点详情
```

### 4.2 NodeDetailPanel

```
+----------------------------------------------------+
| 游戏主机 (192.168.1.100)   已连接  RTT 0.45ms     |
+----------------------------------------------------+
| 操作栏: [重连] [编辑别名] [移除] [复制连接信息]    |
+----------------------------------------------------+
| 信息区: IP/端口/Token/别名/连接码/状态/评分         |
+----------------------------------------------------+
| 最新数据快照: CPU/GPU/内存/网络/FPS/进程            |
+----------------------------------------------------+
| 历史趋势(5分钟): [CPU+GPU折线] [网络面积图]        |
+----------------------------------------------------+
```

每个节点维护 deque(maxlen=300) 历史帧缓存 (5分钟).

---

## 五、Monitor 页面

### 5.1 布局

```
MonitorPage
+-- headerRow: 返回按钮 + 节点名 + 状态徽标
+-- metricStrip: 6 个仪表卡片横排 (等宽)
|   +-- GaugeCard (CPU 环形 + 温度)
|   +-- GaugeCard (GPU 环形 + 温度)
|   +-- GaugeCard (内存 环形 + used/total)
|   +-- NetworkCard (双向流量 + 网卡)
|   +-- FpsCard (大号数字 + 帧时间 + 1%Low)
|   +-- ScoreCard (径向仪表 + RTT/丢包)
+-- chartRow1: [60%] CPU+GPU折线 [40%] 网络面积
+-- chartRow2: [50%] 温度折线 [50%] 进程柱状图
+-- bottomRow: [50%] 磁盘面板 [50%] 网络质量面板
```

### 5.2 GaugeCard

```
+---------------------+
|       CPU           |  标签12px灰色
|    [环形进度图]       |  中央环形80px
|      45.2%          |  环形内数值24px粗体
|    65C 正常          |  底部辅助指标
+---------------------+
```

环形图: QPaintEvent + QPainter.drawArc(), 270度弧度

### 5.3 图表规范

折线图 (pyqtgraph):
- 数据源: node_history[node_id] 最近60点
- X轴: 60秒, 每10秒刻度
- Y轴: 使用率0-100%; 温度/FPS自动
- 曲线: 2px #007acc蓝色
- 阈值: 1px虚线 橙(80%)+红(95%)

面积图: 蓝色半透明=下载, 橙色半透明=上传, 透明度15%

柱状图: 水平柱状图, 按CPU+GPU综合排序, 前3名高亮

---

## 六、Alerts 页面

### 6.1 AlertAdapter (新增)

包装 v5.1 的 AlertEngine, 补充 timestamp/node_alias 字段, 增加 30s 去重窗口。

```python
class AlertAdapter:
    """包装 v5.1 AlertEngine, 为 AlertsPage 提供增强告警数据。"""
    def __init__(self, engine: AlertEngine):
        self._engine = engine
        self._history: list[dict] = []       # 告警历史 (完整)
        self._last_time: dict[str, float] = {} # 去重: key -> 上次告警时间
        self._unread = 0

    def check(self, frame: dict, node_id: str, node_alias: str) -> list[dict]:
        """调用 AlertEngine.check(), 补充 timestamp/node_alias, 30s 去重。"""
        raw = self._engine.check(frame)
        alerts = []
        now = time.time()
        for r in raw:
            key = f"{node_id}:{r['path']}"
            last = self._last_time.get(key, 0)
            if now - last < 30:  # 30s 去重窗口
                continue
            entry = {
                "timestamp": now,
                "node_id": node_id,
                "node_alias": node_alias,
                **r,  # name, path, value, level, threshold
            }
            alerts.append(entry)
            self._history.append(entry)
            self._last_time[key] = now
            self._unread += 1
        return alerts

    def get_history(self, count: int = 100) -> list[dict]:
        return list(reversed(self._history[-count:]))

    def get_unread(self) -> int:
        return self._unread

    def clear_unread(self):
        self._unread = 0
```

在 MainWindow._check_alerts() 中: 原有 AlertEngine.check() 保留, AlertAdapter 做增强包装。

### 6.2 布局

```
AlertsPage
+-- headerRow: 标题 + 筛选(全部/红线/预警) + 清除 + 告警设置
+-- summaryRow: 3个统计卡片
|   +-- StatCard (红线, count, COLOR_DANGER)
|   +-- StatCard (预警, count, COLOR_WARN)
|   +-- StatCard (今日, count, COLOR_TEXT)
+-- alertTable: QTableWidget
    列: 时间 | 节点 | 指标 | 当前值 | 阈值 | 等级
```

### 6.3 告警数据结构

```python
{
    "timestamp": float,
    "node_id": str, "node_alias": str,
    "path": str, "name": str,
    "value": float, "threshold": float,
    "level": str   # "red" / "warn"
}
```

去重: 同一 (node_id, path) 30s内只记一次

---

## 七、Settings 页面

5个标签页:
- 通用: 语言/开机自启/最小化到托盘
- 告警: 开关/规则管理(QTableWidget+编辑/删除/添加)/恢复默认
- 节点: 自动发现/UDP端口/重连间隔/列表最大数
- 外观: 主题(深色/浅色预留)/缩放(100%/125%/150%)/卡片列数/最大卡片数
- 高级: 日志级别/调试模式/WS超时/丢包间隔

设置即时写入 host_config.json, 无需重启.

---

## 八、UI 组件库

| 组件 | 类名 | 状态 |
|------|------|------|
| 仪表卡片 | GaugeCard | 新增 |
| 网络卡片 | NetworkCard | 新增 |
| FPS卡片 | FpsCard | 新增 |
| 评分卡片 | ScoreCard | 新增 |
| 折线图 | LiveLineChart | 新增 |
| 面积图 | LiveAreaChart | 新增 |
| 柱状图 | HorizontalBarChart | 新增 |
| 径向仪表 | RadialGauge | 新增 |
| 节点卡片 | NodeCard | 重构 |
| 节点详情 | NodeDetailPanel | 新增 |
| 告警表格 | AlertTable | 新增 |
| 统计卡片 | StatCard | 新增 |

所有图表基于 pyqtgraph, 统一接口: push(value) / set_threshold() / clear_data()

复用 v5.1: NodeListWidget / NodeListItemWidget / DiscoveryDialog / ConnectCodeDialog + ClipboardDialog + OnboardingDialog / DetailPanel

---

## 九、状态管理设计

### 9.1 架构分层

```
HostMainWindow (保留 v5.1 所有属性)
    |
    v
UIState (页面视图状态: current_node, filter, selected_page)
    |
    v
ViewModel (数据转换层: 从 HostMainWindow 属性提取页面所需数据)
    |
    v
各 Page Widget (接收 ViewModel 数据, 渲染 UI)
```

### 9.2 HostMainWindow 保留属性

v5.1 HostMainWindow 的所有实例属性保持不变:
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

### 9.3 UIState (新增)

页面视图状态, 独立于数据层:
```python
class UIState:
    current_page: str = "dashboard"   # 当前页面 ID
    current_node: str = None          # 当前选中节点
    filter_mode: str = "all"          # all/abnormal/online
    alert_filter: str = "all"         # all/red/warn
    alert_unread: int = 0             # 未读告警数
```

### 9.4 ViewModel (新增)

从 HostMainWindow 属性提取页面所需数据, 避免页面直接访问 MainWindow 内部:
```python
class DashboardViewModel:
    def get_node_cards(self, state: UIState) -> list[dict]:
        """从 MainWindow.frames/scores/statuses 提取卡片数据"""
        ...

class MonitorViewModel:
    def get_metric_data(self, node_id: str) -> dict:
        """从 MainWindow.frames 提取单节点 6 项指标"""
        ...
    def get_history(self, node_id: str) -> list[dict]:
        """从 HistoryBuffer 提取趋势数据"""
        ...

class AlertViewModel:
    def get_recent(self, count: int) -> list[dict]:
        """从 MainWindow.alert_history 提取最近告警"""
        ...
```

### 9.5 HistoryBuffer (新增)

解决 Monitor 趋势图数据来源。每个节点维护 deque(maxlen=300) 存储 5 分钟历史帧。

```python
class HistoryBuffer:
    """每节点 5 分钟历史帧缓存, 供 Monitor/Nodes 页面趋势图使用。"""
    def __init__(self, maxlen: int = 300):
        self._buffers: dict[str, deque] = {}  # node_id -> deque
        self._maxlen = maxlen

    def push(self, node_id: str, frame: dict) -> None:
        """数据到达时调用, 追加一帧。"""
        if node_id not in self._buffers:
            self._buffers[node_id] = deque(maxlen=self._maxlen)
        self._buffers[node_id].append({
            "ts": frame.get("ts", time.time()),
            "cpu_usage": frame.get("cpu", {}).get("total_usage", 0),
            "gpu_usage": frame.get("gpu", {}).get("usage_percent", 0),
            "ram_usage": frame.get("ram", {}).get("usage_percent", 0),
            "cpu_temp": frame.get("cpu", {}).get("package_temp_c", 0),
            "gpu_temp": frame.get("gpu", {}).get("core_temp_c", 0),
            "net_up": frame.get("net", {}).get("upload_mb_s", 0),
            "net_down": frame.get("net", {}).get("download_mb_s", 0),
            "fps": frame.get("fps", {}).get("fps", 0),
            "score": frame.get("net_quality", {}).get("quality_score", 0),
        })

    def get(self, node_id: str) -> list[dict]:
        """返回最近 300 帧 (5 分钟)。"""
        return list(self._buffers.get(node_id, []))

    def remove(self, node_id: str) -> None:
        """节点移除时清理。"""
        self._buffers.pop(node_id, None)
```

在 MainWindow._on_data() 中调用 history_buffer.push()。

### 9.6 SettingsFacade (新增)

包装 v5.1 的 host/config.py 模块函数, 提供面向 Settings 页面的统一接口。底层仍是 load_config()/save_config() 函数。

```python
class SettingsFacade:
    """Settings 页面的配置接口, 包装 host/config.py。"""
    def __init__(self):
        self._cfg = host_config.load_config()
        self._alerts = host_config.load_alerts(self._cfg)

    def get(self, key: str, default=None):
        return self._cfg.get(key, default)

    def set(self, key: str, value):
        self._cfg[key] = value
        host_config.save_config(self._cfg)

    def get_alerts(self) -> list[dict]:
        return list(self._alerts)

    def set_alerts(self, rules: list[dict]):
        self._alerts = rules
        self._cfg["alerts"] = rules
        host_config.save_config(self._cfg)

    def reset_alerts(self):
        self._alerts = list(host_config.DEFAULT_ALERTS)
        self._cfg.pop("alerts", None)
        host_config.save_config(self._cfg)
```

v5.1 的 host_config.load_config()/save_config() 函数继续存在, SettingsFacade 不替换它们。

---

## 十、数据流设计

### 10.1 完整数据路径

```
Agent (采集+推送)
    |
    | WebSocket monitor_data (每1秒)
    v
ConnectionCore (WS 线程, 纯 Python socket)
    |
    | callback("on_data", frame)
    v
NodeConnection._on_data(frame, node_id)      <- WS 线程
    |
    | self.data_received.emit(frame, node_id) <- Qt Signal 跨线程
    v
MainWindow._on_data(frame, node_id)          <- 主线程 slot
    |
    +-- self.frames[node_id] = frame          <- 更新 v5.1 属性
    +-- history_buffer.push(node_id, frame)   <- 追加历史 (v5.2 新增)
    +-- _inject_net_quality(frame, node_id)   <- 注入 RTT/丢包/评分
    +-- _check_alerts(frame, node_id)         <- 告警检测
    +-- dashboard_vm.update()                 <- ViewModel 通知 (v5.2 新增)
    +-- monitor_vm.update()                   <- ViewModel 通知 (v5.2 新增)
    v
各 Page Widget
    |
    | ViewModel.get_xxx_data() -> 提取渲染数据
    | Widget.update()          -> 渲染
    v
QPainter / pyqtgraph 绘制
```

### 10.2 信号驱动 (非 QTimer)

v5.1 的信号连接保持不变:
- NodeConnection.data_received -> MainWindow._on_data
- NodeConnection.status_changed -> MainWindow._on_status
- NodeConnection.rtt_updated -> MainWindow._on_rtt
- NodeConnection.loss_updated -> MainWindow._on_loss
- LocalCollectorPack.local_data -> MainWindow._on_data

v5.2 新增: MainWindow._on_data() 内部调用 ViewModel.update() 和 HistoryBuffer.push(), 不引入 QTimer。数据到达即更新, 零延迟。

### 10.3 数据协议 (不变)

| 字段 | 方向 | 频率 | v5.1/v5.2 变更 |
|------|------|------|----------------|
| agent_heartbeat | Agent->Host | 每2s UDP | 不变 |
| monitor_data | Agent->Host | 每1s WS | 不变 |
| auth_result | Agent->Host | 连接时 | 不变 |
| loss_pong | Agent->Host | 每10s | 不变 |

---

## 十一、异常状态设计

- 节点离线: 卡片灰化+红色 / Sidebar红点 / Monitor图表冻结
- 连接失败: 指数退避重连(1s->60s) / 橙色重连中 / 红色鉴权失败
- 全部离线: Dashboard空状态插图 / Sidebar空 / Monitor占位
- 网络断开: StatusBar红色 / 全部节点离线 / 恢复后自动重连
- Agent崩溃: 等30s判定离线 / 30s内等待重连 / 超时后离线
- 数据异常: 缺失字段N/A / 类型异常静默跳过
- 性能兜底: v5.1 SelfMonitor 保持不变, Host CPU>5%连续2次 -> 降级
- 告警风暴: 同一指标30s去重 / 托盘合并显示 / 历史完整

---

## 十二、未来 v6 兼容预留

| v6 可能变更 | v5.2 预留 |
|-------------|-----------|
| Agent被Electron替代 | Host仅WS/REST通信 |
| PyQt5->Electron/Qt6 | UI与业务分离, State可复用 |
| 多用户权限 | State扩展role |
| 云端部署 | Agent支持TLS, Host支持远程 |
| 插件系统 | AlertEngine规则可扩展 |

配置预留: theme/ui_scale/chart_refresh_ms/history_minutes/alert_dedup_seconds/ws_read_timeout/reconnect_interval
协议兼容: monitor_data格式不变, 新增字段只追加不修改

---

## 十三、v5.1 代码映射

### 13.1 保留不变的模块

| 模块 | 文件 | v5.2 状态 |
|------|------|-----------|
| NodeConnection | host/connection.py | 不变, 信号驱动 |
| ConnectionCore | host/connection_core.py | 不变 |
| AlertEngine | host/alerts.py | 不变, AlertAdapter 包装 |
| QualityScorer | common/quality.py | 不变 |
| SelfMonitor | common/self_monitor.py | 不变 |
| LocalCollectorPack | host/local_node.py | 不变 |
| host_config | host/config.py | 不变, SettingsFacade 包装 |
| theme | common/theme.py | 不变 |

### 13.2 包装适配的模块

| v5.1 模块 | v5.2 适配层 | 包装方式 |
|-----------|-------------|----------|
| host_config (load/save) | SettingsFacade | 包装函数调用, 提供 get/set/get_alerts 接口 |
| AlertEngine.check() | AlertAdapter | 包装调用, 补充 timestamp/node_alias, 增加 30s 去重 |
| _tray (QSystemTrayIcon) | TrayManager | 包装 showMessage/updateStatus |
| NodeListWidget | 保留 | NodesPage 直接使用 |
| NodeListItemWidget | 保留 | NodeList 直接使用 |
| DiscoveryDialog | 保留 | NodesPage 直接使用 |
| ConnectCodeDialog/ClipboardDialog/OnboardingDialog | 保留 | NodesPage 直接使用 |
| DetailPanel | 保留 | NodesPage 详情面板 |

### 13.3 新增的模块

| 模块 | 文件 | 职责 |
|------|------|------|
| UIState | host/gui/ui_state.py | 页面视图状态 (current_page/filter) |
| DashboardViewModel | host/gui/view_models.py | Dashboard 数据提取 |
| MonitorViewModel | host/gui/view_models.py | Monitor 数据提取 |
| AlertViewModel | host/gui/view_models.py | Alert 数据提取 |
| HistoryBuffer | host/gui/history_buffer.py | 5 分钟帧历史缓存 |
| TrayManager | host/gui/tray_manager.py | 托盘管理 |
| SideNav | host/gui/side_nav.py | 侧边导航栏 |
| DashboardPage | host/gui/dashboard_page.py | 总览页 |
| NodesPage | host/gui/nodes_page.py | 节点管理页 (重构) |
| MonitorPage | host/gui/monitor_page.py | 单节点监控页 |
| AlertsPage | host/gui/alerts_page.py | 告警中心页 |
| SettingsPage | host/gui/settings_page.py | 设置页 |
| GaugeCard | host/gui/widgets/gauge_card.py | 环形仪表 |
| NetworkCard | host/gui/widgets/network_card.py | 网络卡片 |
| FpsCard | host/gui/widgets/fps_card.py | FPS 卡片 |
| ScoreCard | host/gui/widgets/score_card.py | 评分卡片 |
| LiveLineChart | host/gui/widgets/line_chart.py | 实时折线图 |
| LiveAreaChart | host/gui/widgets/area_chart.py | 面积图 |
| HorizontalBarChart | host/gui/widgets/bar_chart.py | 柱状图 |
| RadialGauge | host/gui/widgets/radial_gauge.py | 径向仪表 |
| NodeCard | host/gui/widgets/node_card.py | 总览节点卡片 |
| StatCard | host/gui/widgets/stat_card.py | 统计卡片 |

### 13.4 删除的模块

| v5.1 模块 | 原因 |
|-----------|------|
| host/gui/overview_grid.py | 被 DashboardPage + NodeCard 替代 |

### 13.5 HostMainWindow 改动

v5.1 的 HostMainWindow 保持所有实例属性不变。仅修改:
1. _build_ui() 方法: 替换原有 splitter 布局为 SideNav + contentStack
2. 新增 _init_view_models(): 创建 ViewModel 实例
3. 新增 _init_history_buffer(): 创建 HistoryBuffer
4. _on_data() 方法: 内部调用 history_buffer.push() 和 ViewModel 更新
5. _check_alerts() 方法: 内部调用 AlertAdapter 包装

---

## 十四、实施计划

Phase 1 基础层 (Week 1):
  UIState / ViewModel / HistoryBuffer / AlertAdapter / TrayManager / SettingsFacade
  + GaugeCard/NetworkCard/FpsCard/ScoreCard/RadialGauge 单元测试

Phase 2 Dashboard (Week 2):
  SideNav + DashboardPage + NodeCard 网格 + 筛选 + 告警摘要

Phase 3 Monitor (Week 2-3):
  MonitorPage + 6 个仪表卡 + 折线/面积/柱状图 + 磁盘/网络面板

Phase 4 Nodes+Alerts+Settings (Week 3):
  NodesPage 增强 (搜索/详情) + AlertsPage + SettingsPage 5 标签

Phase 5 集成+性能 (Week 4):
  全链路测试 + 16 节点性能基准 + 内存泄漏检测 + 响应式 (1024~4K)
