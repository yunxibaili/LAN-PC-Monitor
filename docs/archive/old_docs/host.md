# Host 说明

> **Version**: v5.2 (Phase 4)
> **Status**: CURRENT
> **Compatibility**: 主机端（集中监控大屏），连接 Agent v5.0

## 1. 定位

Host 是运行在**监控电脑**上的桌面应用（PyQt5），通过 WebSocket 连接所有 Agent，集中展示所有节点的实时数据，并负责节点管理、红线告警。

## 2. 模块结构

```
host/
 ├── __init__.py / __main__.py / main.py   # python -m host 入口
 ├── config.py            # host_config.json 读写
 ├── connection.py        # NodeConnection（WebSocket 客户端）
 ├── discovery.py         # UDP/mDNS 监听与发现
 ├── local_node.py        # 本机节点（可选，本地采集器直供)
 ├── self_monitor.py      # 性能兜底（转发 common.self_monitor）
 ├── alerts.py            # 红线告警引擎
 ├── facade/
 │   └── settings_facade.py   # Settings 门面
 ├── store/
 │   ├── frame_store.py       # 帧数据存储
 │   ├── node_store.py        # 节点状态存储
 │   ├── history_store.py     # 历史数据存储
 │   └── alert_store.py       # 告警存储
 ├── service/
 │   ├── alert_service.py     # 告警服务
 │   └── discovery_service.py # 发现服务
 ├── viewmodels/
 │   ├── dashboard_vm.py      # Dashboard 数据转换
 │   ├── node_detail_vm.py    # 节点详情数据转换
 │   ├── monitor_vm.py        # Monitor 数据转换
 │   ├── alert_vm.py          # Alert 数据转换
 │   └── settings_vm.py       # Settings 数据转换
 ├── manager/
 │   └── tray_manager.py      # 托盘管理
 ├── gui/
 │   ├── main_window.py       # 主窗口 (300行)
 │   ├── discovery_dialog.py  # 自动发现弹窗
 │   ├── controllers/
 │   │   ├── navigation_controller.py  # 导航控制
 │   │   ├── data_controller.py        # 数据流控制
 │   │   ├── alert_controller.py       # 告警控制
 │   │   └── window_controller.py      # 窗口控制
 │   ├── navigation/
 │   │   └── side_nav.py      # 侧边导航栏
 │   ├── theme/               # 设计系统
 │   │   ├── colors.py        # ThemeColors
 │   │   ├── spacing.py       # ThemeSpacing
 │   │   ├── typography.py    # ThemeTypography
 │   │   ├── style.py         # QSS 样式
 │   │   ├── components.py    # 组件样式
 │   │   ├── layout.py        # 布局常量
 │   │   ├── icons.py         # 图标
 │   │   └── animation.py     # 动画常量
 │   ├── pages/
 │   │   ├── base_page.py     # 页面基类
 │   │   ├── dashboard_page.py    # 总览页
 │   │   ├── nodes_page.py        # 节点管理页
 │   │   ├── monitor_page.py      # 实时监控页
 │   │   ├── alerts_page.py       # 告警中心
 │   │   └── settings_page.py     # 设置页
 │   └── widgets/
 │       ├── app_card.py          # 基础容器卡
 │       ├── node_card.py         # 节点概览卡
 │       ├── resource_card.py     # 资源圆环卡
 │       ├── metric_card.py       # 单指标卡
 │       ├── metric_bar.py        # 进度条
 │       ├── chart_widget.py      # 折线图
 │       ├── chart_panel.py       # 图表面板
 │       ├── status_badge.py      # 状态徽章
 │       ├── quality_badge.py     # 网络质量徽章
 │       ├── node_explorer.py     # 节点探索面板
 │       ├── detail_dashboard.py  # 节点详情仪表盘
 │       ├── detail_panel.py      # 详情面板 (v5.1)
 │       ├── monitor_header.py    # 监控页头部
 │       ├── metric_selector.py   # 指标选择器
 │       ├── header_bar.py        # 顶部导航栏
 │       ├── page_header.py       # 页面头部
 │       ├── section_title.py     # 区块标题
 │       ├── empty_state.py       # 空状态占位
 │       ├── node_list.py         # 节点列表 (兼容层)
 │       └── card_widget.py       # (deprecated)
 └── local_node.py        # 本机采集器
```

## 3. 启动方式

```bash
python -m host             # 启动监控大屏
python -m host --install-startup   # 装开机自启（注册表 Run）
python -m host --remove-startup    # 卸开机自启
```

## 4. 架构分层

```
Agent (采集+推送)
  ↓ WebSocket
Connection (WS 客户端, Signal 驱动)
  ↓
Store (FrameStore / NodeStore / HistoryStore / AlertStore)
  ↓
ViewModel (数据转换层, 不含 PyQt5)
  ↓
Page (页面容器, 只导入 Widget + ViewModel)
  ↓
Widget (UI 组件, 只导入 Theme)
  ↓
Theme (ThemeColors / ThemeSpacing / ThemeTypography)
```

**约束**：
- Page 禁止直接访问 Store / Connection / ConfigManager
- ViewModel 禁止导入 PyQt5
- 所有颜色通过 ThemeColors 引用

## 5. GUI 功能

| 页面 | 功能 |
|------|------|
| Dashboard | 节点总览、KPI 统计、趋势图、告警摘要 |
| Nodes | 节点管理、搜索过滤、详情仪表盘 |
| Monitor | 单节点深度监控、指标选择、实时图表 |
| Alerts | 告警列表、筛选过滤、统计汇总 |
| Settings | 通用/告警/节点/外观/高级 5 标签 |

## 6. 配置

`host_config.json` 字段：

| 字段 | 说明 |
|------|------|
| `hosts` | 已配置 Agent 列表 |
| `window_geometry` | 窗口位置大小 |
| `udp_port` | 心跳监听端口 |
| `alerts` | 红线告警规则 |
| `language` | 界面语言 |
| `auto_discovery` | 自动发现开关 |
