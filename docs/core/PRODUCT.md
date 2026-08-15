# 产品定位与功能说明

> **Version**: v5.2.3
> **Status**: CURRENT

## 1. 产品定位

PC Monitor 是一套**局域网远程电脑监控系统**，用于实时监控多台电脑的硬件状态。

### 核心价值

- **实时监控**：CPU/GPU/内存/磁盘/网络/FPS 等关键指标
- **集中管理**：一台 Host 同时监控多台 Agent
- **红线告警**：指标超阈值自动告警（托盘弹窗 + 日志）
- **零配置发现**：局域网自动发现 Agent

## 2. 双角色架构

| 角色 | 程序 | 网络角色 | GUI | 职责 |
|------|------|----------|-----|------|
| **Agent** | `python -m agent` | WS Server (12345) | 可选本机仪表盘 | 采集 + 推送 |
| **Host** | `python -m host` | WS Client（多连接） | 集中监控大屏 | 订阅 + 展示 |

## 3. Host 5 个页面

### Dashboard（总览页）

- 节点卡片网格（CPU/GPU/内存/网络/FPS/评分）
- KPI 统计（节点总数/在线数/平均 CPU/告警数）
- 筛选（全部/异常/在线）
- 最近告警摘要

### Nodes（节点管理页）

- 左侧：NodeExplorer（搜索 + 节点列表）
- 右侧：DetailDashboard（ResourceCards + 详情面板）
- 支持添加/删除/重连节点

### Monitor（实时监控页）

- MonitorHeader（节点名 + 状态 + 统计）
- MetricSelector（CPU/GPU/RAM/Network/FPS）
- ChartPanel（大面积折线图 + 汇总卡片）

### Alerts（告警中心）

- 统计卡片（Critical/Warning/Total）
- 告警列表（时间/节点/指标/值/阈值/等级）
- 筛选过滤

### Settings（设置页）

- General / Alerts / Nodes / Appearance / Advanced
- 即时写入 host_config.json

## 4. 支持的监控指标

| 指标 | 数据来源 | 单位 |
|------|----------|------|
| CPU 使用率 | cpu.total_usage | % |
| CPU 温度 | cpu.package_temp_c | °C |
| GPU 使用率 | gpu.usage_percent | % |
| GPU 温度 | gpu.core_temp_c | °C |
| 内存使用率 | ram.usage_percent | % |
| 磁盘读写 | disk[].read/write_mb_s | MB/s |
| 网络上传 | net.upload_mb_s | MB/s |
| 网络下载 | net.download_mb_s | MB/s |
| 网络评分 | net_quality.quality_score | 0-100 |
| FPS | fps.fps | 帧/秒 |
| 帧时间 | fps.frame_time_ms | ms |

## 5. 部署方式

```bash
# Agent（每台被监控电脑）
python -m agent              # 后台服务
python -m agent --gui        # 带本机仪表盘

# Host（监控电脑）
python -m host               # 集中监控大屏
```

## 6. 配置

### Agent 配置 (agent_config.json)

| 字段 | 说明 | 默认值 |
|------|------|--------|
| http_port | HTTP/WS 端口 | 12345 |
| udp_port | 自动发现端口 | 12346 |
| token | 鉴权 token | 自动生成 |
| collectors | 采集开关 | 全开 |

### Host 配置 (host_config.json)

| 字段 | 说明 |
|------|------|
| hosts | 已配置 Agent 列表 |
| udp_port | 心跳监听端口 |
| alerts | 红线告警规则 |
| language | 界面语言 |
