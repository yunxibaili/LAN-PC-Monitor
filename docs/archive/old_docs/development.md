# 开发指南

> **Version**: v5.0
> **Status**: Current
> **Compatibility**: 开发环境 Python 3.10+

## 1. 环境准备

- Python 3.10+
- 依赖安装（开发全装）

```bash
pip install -r requirements-agent.txt -r requirements-host.txt
```

## 2. 模块结构

```
agent/     副机端服务（采集 + API + 本机仪表盘）
host/      主机端 GUI（集中展示）
common/    公共模块（采集器/协议/工具/主题/日志）
tests/     测试
docs/      文档
```

## 3. 运行测试

```bash
python tests/test_api.py    # 主测试：Agent REST + WebSocket 端到端（14 项）
python tests/test_p0.py     # 协议/采集器/工具冒烟
```

> `test_connect.py` / `test_p4.py` 为 v4.0 遗留（基于已删除的 node/ TCP），运行即 SKIP，保留作历史参考。

## 4. 关键开发说明

### 采集器（common/collectors）

- 每个采集器继承 `BaseCollector`（独立线程、异常隔离、线程安全读取）
- `collect()` 返回 dict，失败降级为 N/A
- 新增采集器：在 `collectors/` 新建文件 + 在 `create_collectors()` 注册

### Agent 服务（agent/）

- `aggregator.py` 每秒组装 `monitor_data` 帧 → 线程安全最新帧缓存
- `websocket_server.py` 每秒向订阅者广播
- `http_server.py` REST API
- 注意：WS push_loop 必须在事件循环内启动（asyncio.ensure_future 需运行中 loop）

### Host 连接层（host/connection.py）

- `NodeConnection`（QObject）信号接口：`data_received/status_changed/rtt_updated/loss_updated`
- GUI 通过信号槽消费数据，网络层与 GUI 解耦

## 5. 新增后端模块（v6.0）

按第五篇设计，新增模块独立成包：

```
storage/      历史存储（SQLite）
event/        事件系统
history/      历史查询
manager/      节点状态 / watchdog / 自监控
```

**约束**：不得修改 `common/collectors` 接口、不得改变 `monitor_data` Schema、不得改动 WS 协议核心。

## 6. i18n

- 文案集中在 `i18n/zh_CN.json` + `i18n/en.json`
- 代码用 `tr("key")` 引用
- 新增文案需同步两份文件

## 7. 打包

```bash
pip install pyinstaller
python build_agent.py   # Agent exe
python build_host.py    # Host exe
```
