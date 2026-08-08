# 局域网多级硬件监控系统（LAN PC Monitor）

基于 **TCP + UDP/mDNS 零配置发现** 的局域网硬件实时监控系统，Windows 10/11，Python 3.10+。

**v4.0 三角色架构**：采集节点（纯后台）＋ 副机端（本机仪表盘 + 节点管理）＋ 主机端（集中监控大屏）。

详细设计文档见 [`docs/技术文档.md`](docs/技术文档.md)（架构 / 协议 / 数据格式 / 实现优先级全量规格）与 [`docs/需求增强说明.md`](docs/需求增强说明.md)。

## 架构

| 角色 | 启动方式 | TCP | UDP | GUI | 说明 |
|------|----------|-----|-----|-----|------|
| **采集节点 Node** | `python -m node` | Server (12345) | 广播心跳 (12346) | 无 | 纯后台采集 + 推送，每台被监控电脑运行 |
| **副机端 Client** | `python -m client` | Client (多连接) | 监听 | 本机仪表盘 | 本机全量数据 + 远程节点摘要管理 |
| **主机端 Host** | `python -m host` | Client (多连接) | 监听 | 集中大屏 | 所有节点完整详情 + 本机节点 |

- 同一采集节点可被多台副机端/主机端同时连接（按 IP 去重计数）。
- 副机端仅显示本机详情 + 其他节点摘要（IP/别名/状态/RTT/评分），详情归集到主机端。

## 功能特性

- **实时采集**：CPU / 内存 / 磁盘（含队列深度）/ 网络速率 / 进程 TOP / 系统信息 / GPU（NVML 全指标，AMD pyadl 可选）/ 温度（LibreHardwareMonitor）
- **网络质量**：RTT 实测 + 丢包测量 + 滑动平均评分（阈值变色）
- **帧率采集**：PresentMon CLI 主方案（前台窗口动态绑定 + 1% Low），无工具时自动降级 DXGI 截帧（缺失自动提示）
- **零配置连接（§2.5）**：mDNS 自动发现（`_pcmonitor._tcp.local.`）＋ UDP 广播互为备份；6 位数字连接码/二维码；`.pcm` 配置一键导入导出；`pcmonitor://` 剪贴板连接串；首屏引导一键接入
- **运维能力**：鉴权（token）、自动重连（指数退避）、单实例互斥、端口占用检测、日志轮转、开机自启（节点服务化/两端注册表）、性能兜底（CPU 超限自动降级频率）
- **深色主题**：集中大屏自适应三模式（概览/详情/自动），阈值三级变色

## 快速开始

```bash
pip install -r requirements.txt

python -m node      # 1) 采集节点（被监控端，建议管理员运行）
python -m client    # 2) 副机端（本机仪表盘，无需提权）
python -m host      # 3) 主机端（集中监控大屏，无需提权）
```

首次启动自动生成 `node_config.json`（含随机 token）；副机/主机端首屏引导自动发现节点，一键接入。

防火墙需放行 TCP 12345 与 UDP 12346（`docs/技术文档.md` §17.2）。

## 测试

```bash
python tests/test_connect.py   # 双端连接端到端（鉴权/数据帧/RTT/丢包/断线清理） 18 项
python tests/test_p0.py        # 协议/鉴权/链路/发现/评分器/采集器冒烟                 63 项
python tests/test_p4.py        # 真实进程双端集成（重连/多客户端/mDNS/降级链路）       44 项
```

## 目录结构

```
├── docs/                       # 技术文档.md / 需求增强说明.md（全量规格）
├── common/                     # 协议/工具/日志/主题/评分/LHM/单实例/自启/连接码/连接对话框
├── node/                       # 采集节点（config/tcp_server/discovery(UDP+mDNS)/aggregator/collectors*）
├── client/                     # 副机端（connection/discovery/local_node/gui*）
├── host/                       # 主机端（connection/discovery/local_node/self_monitor/gui*）
├── tests/                      # test_connect / test_p0 / test_p4
├── tools/PresentMon.exe        # 帧率工具（需手动下载）
└── logs/                       # 运行日志（自动创建）
```

## 实现进度

P0 骨架 → P1 基础采集 → P2 多节点管理（含副机端）→ P3 进阶采集（GPU/温度/质量评分）→ P4 帧率 + 性能兜底 + mDNS 便捷连接（进行中）。详见 `docs/技术文档.md` §21。
