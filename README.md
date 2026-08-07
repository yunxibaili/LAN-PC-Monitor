# 局域网多级硬件监控系统 — v4.0（三角色架构）

对应《技术文档.md》v4.0：**采集节点（无界面后台）+ 副机端（本机仪表盘 + 节点管理）+ 监控主机（集中监控大屏）** 架构。

## 架构

| 角色 | 程序 | TCP 角色 | UDP | GUI | 说明 |
|------|------|----------|-----|-----|------|
| **采集节点 Node** | `node_main.py` | **Server (12345)** | 广播心跳 (12346) | 无界面 | 纯后台采集 + 推送 |
| **副机端 Client** | `client_main.py` | **Client (多连接)** | 监听心跳 (12346) | 本机仪表盘 + 节点管理 | 显示本机数据 + 管理接入节点（仅摘要） |
| **监控主机 Host** | `host_main.py` | **Client (多连接)** | 监听心跳 (12346) | 集中监控大屏 | 显示所有节点详细数据 |

- **数据最终汇聚到主机端集中显示**；副机端仅显示本机详情 + 其他节点摘要列表（IP/别名/状态/RTT/评分）。
- **本机节点**：副机端/主机端启动自动在列表顶部添加"本机 (localhost)"，本地采集器直供 GUI，RTT 0.00ms，始终在线。
- **多显示端**：同一采集节点可被多台副机端和主机端同时连接。

## 已实现（P0-P3）

| 阶段 | 内容 |
|------|------|
| **P0 骨架** | common/protocol 帧协议、node TCP Server（鉴权+去重）、node 聚合器、host 连接骨架、本机节点置顶 |
| **P1 基础采集** | CPU/内存/磁盘/网络/进程/uptime 采集器 + host 集中 GUI 分区 + 阈值变色 |
| **P2 多节点管理** | host 多节点连接（独立重连）、自适应三模式、自动发现弹窗、持久化、右键菜单 |
| **P3 进阶采集** | GPU(pynvml 全指标，含 usedGpuMemory 判空；热点温度 NVML getattr fallback → LHM 补读 → N/A；AMD pyadl getName 防御)、温度(LibreHardwareMonitor 共享 common/lhm.py)、网络质量评分（滑动平均，系数 *5）、磁盘盘符 WMI 映射 + 队列深度(raw string)、丢包测量 |

## 快速开始

1. 安装依赖：

   ```
   pip install -r requirements.txt
   ```

2. 启动**采集节点**（被监控端，**建议管理员运行**，温度/GPU 需提权）：

   ```
   python node_main.py
   ```
   或双击 `start_node.bat` 选「1」。

   首次启动生成 `node_config.json`（含随机 token）。

3. 启动**副机端**（本机仪表盘 + 节点管理）：

   ```
   python client_main.py
   ```
   或双击 `start_client.bat` 选「1」。

   副机端窗口：
   - 顶部显示本机主机名/IP/uptime/"本机模式"；中部按分区显示本机全部数据
   - 节点管理器（侧边栏/标签页）：显示已接入节点摘要（状态/RTT/评分），含本机
   - 点「添加节点」手动填 IP/端口/别名/token，或点「扫描」自动发现批量添加
   - 节点列表右键：移除 / 改别名 / 手动重连

   节点列表保存在 `client_config.json`，重启自动重连。

4. 启动**监控主机**（集中监控大屏）：

   ```
   python host_main.py
   ```
   或双击 `start_host.bat` 选「1」。

   监控主机窗口：
   - 顶部自动有"本机 (localhost)"节点（本地数据）
   - 左侧节点列表（别名/IP/状态/RTT/评分），右侧详情面板显示该节点全部指标
   - 点「添加节点」手动填 IP/端口/token，或点「扫描」自动发现批量添加
   - 节点列表右键：移除 / 改别名 / 手动重连
   - 「概览」按钮切换网格卡片视图

   节点列表保存在 `host_config.json`，重启自动重连。

## 自检脚本

无 GUI 验证数据链路（帧协议 / 鉴权 / 完整链路 / RTT / 退出无噪声 / 配置持久化 / 采集器 / UDP 发现 / 评分器）：

```
python test_p0.py
```

演示模式（一条命令启动采集节点 + 监控主机）：

```
python test_p0.py --demo
```

## 目录结构

```
远程监控电脑状态/
├── 技术文档.md / 需求增强说明.md
├── requirements.txt
├── node_main.py                 # 采集节点入口（无界面）
├── client_main.py               # 副机端入口（本机仪表盘 + 节点管理）
├── host_main.py                 # 监控主机入口（集中监控大屏）
├── start_node.bat / start_client.bat / start_host.bat
├── test_p0.py                   # 自检 + 演示
├── common/                      # 协议/工具/日志/主题/评分/LHM/单实例/自启
├── node/                        # 采集节点
│   ├── config.py / tcp_server.py / discovery.py / aggregator.py / fake_data.py
│   └── collectors/              # base/cpu/ram/gpu/disk/net/net_quality/proc/sys/fps
├── client/                      # 副机端（待实现）
│   ├── config.py / connection.py / discovery.py / local_node.py
│   └── gui/                     # main_window/local_panel/node_manager/discovery_dialog
├── host/                        # 监控主机
│   ├── config.py / connection.py / discovery.py / local_node.py / self_monitor.py
│   └── gui/                     # main_window/node_list/detail_panel/overview_grid/discovery_dialog
└── logs/                        # node.log / client.log / host.log
```

## 下一步（P4）

帧率(PresentMon CLI 主 + DXGI 降级 + 前台窗口动态绑定) + 单实例互斥 + 开机自启(node schtasks / client+host 注册表) + 性能兜底 + 实现副机端 client。

详见《技术文档.md》§21 实现优先级。
