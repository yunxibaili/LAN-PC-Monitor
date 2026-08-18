# Phase 5.3-1 — Runtime Reliability（已实施）

> **版本**: v5.3.1
> **分支**: v5.3-dev
> **状态**: ✅ DONE（2026-08-18，一个 commit：`v5.3.1: fix runtime path and remove netifaces`）
> **原则**: 只做两个实际修复，不做迁移/多用户/Release 流程等工程化负担。

---

## 一、本次改动（只此两件）

| # | 修复 | 改动文件 | 说明 |
|---|------|----------|------|
| 1 | history.db 路径统一 | `host/service/storage_service.py`、`host/gui/main_window.py` | 不再依赖进程 CWD |
| 2 | netifaces 替换为 psutil | `common/utils.py`、`requirements-common.txt`、`requirements.txt` | 消除 Python 3.12 安装隐患 |

---

## 二、1. history.db 路径

### 修复前（问题）

- `StorageService("history.db")` 硬编码相对路径 → 数据库落在进程 CWD
- 换启动方式 = 换数据库：桌面启动/CMD 启动/IDE 启动各自生成一个库，数据割裂

### 修复后

```
%APPDATA%/LAN-PC-Monitor/data/history.db     # Windows
~/.config/LAN-PC-Monitor/data/history.db     # 其它
```

- `storage_service.py` 新增 `get_default_db_path()`：自动读 `%APPDATA%`（fallback `~/.config`）、拼接、`makedirs(exist_ok=True)`
- `StorageService()` 无参时走 `get_default_db_path()`；`:memory:` 与显式路径行为不变（测试兼容）
- 不做：MigrationService / 数据迁移 / 多用户设计

### 验收

- [x] 无参构造 DB 落在 `%APPDATA%/LAN-PC-Monitor/data/history.db`，目录自动创建
- [x] `:memory:` 测试路径不变
- [x] 全量回归通过（见下）

---

## 三、2. netifaces 替换

### 修复前（隐患）

- netifaces 0.11 停更，PyPI wheel 仅到 cp39
- Python 3.12+ 全新安装因 distutils 移除直接失败；3.10/3.11 CI 需 sdist 编译（约 40s）

### 修复后（无新增依赖）

| 函数 | 原来 | 现在 |
|------|------|------|
| `get_lan_ip()` | netifaces.interfaces()/ifaddresses() | `psutil.net_if_addrs()`（psutil ≥5.9 已在依赖树） |
| `get_default_gateway()` | netifaces.gateways() + route print 兜底 | 只留 route print（兼容中英文） |

- 网卡过滤逻辑（私网段 → 排除虚拟 → 有线优先）原样保留，仅换数据源
- 不改 `zeroconf`/`ifaddr`，不做 B2/B3 方案

### 验收

- [x] `get_lan_ip()` 返回正确私网 IP（同一网络原 netifaces 也返回 192.168.1.124）
- [x] `get_default_gateway()` 返回 192.168.1.1（route print 主路径）
- [x] psutil 未安装时优雅降级 socket 探测（`try/except ImportError` 保留）
- [x] requirements 两处 netifaces 声明已移除

---

## 四、测试

- 全量回归：见基线（v5.2.3 988/988 不降基线）
- 网络行为：`get_lan_ip` / `get_default_gateway` / `get_local_node_info` 实测通过
- 端到端：`tests/test_api.py`（network discovery 相关）

---

## 五、路线衔接（后续）

```
v5.3-2 Product UI Expansion（Dashboard 美化 / 历史曲线 / 状态卡片 / 设备列表）
v5.3-3 Play Features（告警声音 / 微信·Telegram 通知 / 自动发现 / 远程控制）
v5.4   Agent UI / Multi-node / Advanced monitoring
```

> 小功能直接 commit，不再每改动走 release note / audit / baseline / PR template 全流程。