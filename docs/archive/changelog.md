# 更新日志

> **Version**: v5.1
> **Status**: Current
> **Compatibility**: 完整更新记录，最新版本在上方

## v5.1 (当前)

**Desktop Experience 优化**

- 设置中心：新增 SettingsManager（language/theme/alert/collector/network/startup 六类），Dashboard 右上角 ⚙ 齿轮入口
- 取消启动语言弹窗与节点连接弹窗；首次启动后台自动发现，语言/主题在设置中心管理
- Agent 托盘模式：`--tray` 后台 + 系统托盘（可打开仪表盘/退出）；`--gui` 保留管理员模式
- 打包禁 console 窗口（agent/host spec console=False）
- WebSocket 认证状态机：connecting → authenticating → connected/auth_failed，错误 token 停止重连
- host 网络核心拆分（connection_core 无 PyQt5 可测）
- `/api/health` uptime 拆分 agent_uptime / system_uptime

## v6.0 (规划中)

**平台化增强（设计稿）**

- [ ] 历史数据存储（SQLite 时间序列 + 保留策略）
- [ ] 历史趋势查询 API（`/api/history`）
- [ ] WebSocket 订阅模式（full / lite）
- [ ] 节点状态管理（NodeManager）
- [ ] Agent 自监控（agent_metrics）
- [ ] 采集器健康检测（collector watchdog）
- [ ] 事件系统（event_manager）
- [ ] 配置热更新（`/api/config/reload`）
- [ ] 版本管理 / 批量摘要 / 日志查询 API
- [ ] 安全增强（token 过期 / 权限分级）
- [ ] 50+ 节点性能优化（压缩 / 变化推送）

## v5.0 (当前)

**前后端分离重构**

- 取消独立采集节点（Node），采集能力并入 Agent
- 通信从 TCP 自定义协议升级为 HTTP/REST + WebSocket
- Agent：采集 + WS/REST 服务 + 可选本机仪表盘（`--gui`）
- Host：PyQt5 集中监控大屏，WebSocket 订阅
- 采集器迁移至 `common/collectors/`；SelfMonitor 提升至 `common/`
- 双端独立打包（PyInstaller）
- 新增 `tests/test_api.py` 端到端测试

## v4.0 (历史)

- 三角色架构（采集节点/副机端/主机端），TCP + UDP/mDNS
- P0-P5 全阶段完成，i18n 中英双语、自定义红线告警
