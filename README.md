# 局域网集中式硬件监控系统 — v3.0（集中式架构）

对应《技术文档.md》v3.0：**采集节点（无界面后台）+ 监控主机（集中显示 GUI）** 架构，
已实现至 **P3（进阶采集）**。

## 架构

| 角色 | 程序 | TCP 角色 | GUI | 说明 |
|------|------|----------|-----|------|
| **采集节点 Node** | `node_main.py` | **Server (12345)** | 无界面 | 纯后台采集 + 推送，广播 node_heartbeat (12346) |
| **监控主机 Host** | `host_main.py` | **Client (多连接)** | 集中显示 | 显示所有节点 + 本机节点，监听心跳自动发现 |

- **本机节点**：监控主机启动自动在列表顶部添加"本机 (localhost)"，本地采集器直供 GUI，RTT 0.00ms，始终在线。
- **多主控**：同一采集节点可被多台监控主机同时连接。

## 已实现（P0-P3）

| 阶段 | 内容 |
|------|------|
| **P0 骨架** | common/protocol 帧协议、node TCP Server（鉴权+去重）、node 聚合器、host 连接骨架、本机节点置顶 |
| **P1 基础采集** | CPU/内存/磁盘/网络/进程/uptime 采集器 + host 集中 GUI 分区 + 阈值变色 |
| **P2 多节点管理** | host 多节点连接（独立重连）、自适应三模式、自动发现弹窗、持久化、右键菜单 |
| **P3 进阶采集** | GPU(pynvml 全指标，含 usedGpuMemory 判空)、温度(LibreHardwareMonitor)、网络质量评分（滑动平均，系数 *15）、磁盘盘符 WMI 映射 + 队列深度、丢包测量 |

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

3. 启动**监控主机**（显示端）：

   ```
   python host_main.py
   ```
   或双击 `start_host.bat` 选「1」。

   监控主机窗口：
   - 顶部自动有"本机 (localhost)"节点（本地数据）
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
├── host_main.py                 # 监控主机入口（GUI）
├── start_node.bat / start_host.bat
├── test_p0.py                   # 自检 + 演示
├── common/                      # 协议/工具/日志/主题/评分/LHM/单实例/自启
├── node/                        # 采集节点
│   ├── config.py / tcp_server.py / discovery.py / aggregator.py / fake_data.py
│   └── collectors/              # base/cpu/ram/gpu/disk/net/net_quality/proc/sys/fps
├── host/                        # 监控主机
│   ├── config.py / connection.py / discovery.py / local_node.py / self_monitor.py
│   └── gui/                     # main_window/node_list/detail_panel/overview_grid/discovery_dialog
├── client/                      # （v2.0 旧副机端，待清理）
├── client_main.py               # （v2.0 旧副机入口，待清理）
└── logs/
```

## 下一步（P4）

帧率(PresentMon CLI 主 + DXGI 降级 + 前台窗口动态绑定) + 单实例互斥 + 开机自启(node schtasks / host 注册表) + 性能兜底 + 清理 v2.0 旧代码。

详见《技术文档.md》§19 实现优先级。
