# 安装部署

> **Version**: v5.0
> **Status**: Current
> **Compatibility**: Windows 10/11，Python 3.10+

## 1. 环境要求

- Windows 10/11
- Python 3.10+
- 管理员权限（Agent 温度/帧率采集、开机自启）

## 2. 安装依赖

依赖按角色拆分，见 `requirements-*.txt`：

```bash
# 一键全部（开发/调试）
pip install -r requirements-agent.txt -r requirements-host.txt

# 仅 Agent（被监控机）
pip install -r requirements-agent.txt

# 仅 Host（监控机）
pip install -r requirements-host.txt
```

可选依赖：

- `tools/PresentMon.exe`：精准帧率（需手动下载放入 tools/）
- LibreHardwareMonitor：温度/功耗采集

## 3. 防火墙

PowerShell（管理员）：

```powershell
New-NetFirewallRule -DisplayName "PC_Monitor_HTTP" -Direction Inbound -Protocol TCP -LocalPort 12345 -Action Allow -Profile Private
New-NetFirewallRule -DisplayName "PC_Monitor_UDP"  -Direction Inbound -Protocol UDP -LocalPort 12346 -Action Allow -Profile Private
```

## 4. 部署步骤

1. 装 Python 3.10+，按角色装依赖
2. （可选）下载 PresentMon.exe → `tools/`
3. 防火墙放行 12345/12346
4. **被监控机**：以管理员运行 `python -m agent`（或 `start_agent.bat`）
5. **监控机**：运行 `python -m host`（或 `start_host.bat`）
6. （可选）开机自启：`python -m agent --install-startup` / `python -m host --install-startup`

## 5. 权限说明

| 功能 | 需管理员 |
|------|---------|
| CPU/GPU 使用率、内存、磁盘、网络 | 否 |
| 温度/功耗（LibreHardwareMonitor） | 是 |
| PresentMon 帧率 | 是 |
| Agent 开机自启（schtasks） | 是 |
| Host 开机自启（注册表） | 否 |

## 6. 双端独立打包（v6.0）

Agent 与 Host 分别打包为独立 exe/安装包，独立安装目录、配置、日志，互不混装：

- `build_agent.py` + `agent.spec` → `PC-Monitor-Agent-v5.0-win-x64.exe`
- `build_host.py` + `host.spec` → `PC-Monitor-Host-v5.0-win-x64.exe`

```bash
pip install pyinstaller
python build_agent.py
python build_host.py
```
