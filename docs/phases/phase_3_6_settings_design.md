# Phase 3-6：SettingsPage 迁移设计文档

> **Status**: COMPLETE
> **Date**: 2026-08-11
> **Result**: SettingsPage + SettingsViewModel 实现完成，30 项测试全通过
> **Implementation**: `host/gui/pages/settings_page.py`, `host/viewmodels/settings_vm.py`
> **Tests**: `test_v52_settings_vm.py`

## 一、现有设置架构分析

### 1.1 配置层次

```
host_config.json (磁盘持久化)
  ↕ load_config / save_config
host/config.py DEFAULT_CONFIG (10 基础字段)
  ↕ 包装
SettingsFacade (统一入口, 14 个 getter_map + 8 个 V52_DEFAULTS)
  ↕ 底层
ConfigManager (单例, host_cfg + agent_cfg 双配置)
```

### 1.2 字段清单（DEFAULT_CONFIG + V52_DEFAULTS）

**DEFAULT_CONFIG (10 字段，持久化)**：

| 字段 | 类型 | 默认值 |
|------|------|--------|
| hosts | list | [] |
| udp_port | int | 12346 |
| window_geometry | dict | {x,y,w,h} |
| view_mode | str | "auto" |
| max_overview_cards | int | 16 |
| max_cards_per_row | int | 4 |
| last_selected_node | str | "" |
| alert_popup | bool | True |
| language | str | "" |
| onboarded | bool | False |

**V52_DEFAULTS (8 字段，v5.2 新增)**：

| 字段 | 类型 | 默认值 |
|------|------|--------|
| theme | str | "dark" |
| ui_scale | float | 1.0 |
| chart_refresh_ms | int | 500 |
| history_minutes | int | 5 |
| alert_dedup_seconds | int | 30 |
| ws_read_timeout | int | 30 |
| reconnect_interval | int | 60 |
| language | str | "zh_CN" |

**ConfigManager getter_map (14 个专用 key)**：

| key | 来源 | 类型 |
|-----|------|------|
| language | host_cfg | str |
| theme | host_cfg | str |
| ui_scale | host_cfg | float |
| log_level | host_cfg | str |
| debug_mode | host_cfg | bool |
| http_port | agent_cfg | int |
| udp_port | agent_cfg | int |
| use_multicast | agent_cfg | bool |
| preferred_iface | agent_cfg | str |
| auto_discovery | host_cfg | bool |
| auto_connect | host_cfg | bool |
| agent_auto_start | agent_cfg | bool |
| host_auto_start | host_cfg | bool |
| onboarded | host_cfg | bool |

### 1.3 现有 SettingsDialog（5 标签页）

| Tab | 字段 |
|-----|------|
| 通用 | language, theme, ui_scale |
| 告警 | cpu.red, gpu_temp.red, ram.red, fps.red_min, alert_popup |
| 采集 | collector_interval, gpu, fps, process |
| 节点 | auto_discovery, auto_connect, hosts（只读列表） |
| 高级 | log_level, debug_mode |

### 1.4 SettingsFacade 已有接口

- `get(key)` / `set(key, value)` / `save()` / `reset(key)`
- `get_alert(path)` / `set_alert(path, red, warn, ...)`
- `get_hosts()` / `add_host()` / `remove_host()`
- `settings_changed` Signal

### 1.5 问题

- SettingsDialog 直接调用 ConfigManager，绕过 Facade
- SettingsPage 是空壳
- 告警规则（8 条）无 UI 管理入口
- 部分字段（collector_interval/gpu/fps/process）在 ConfigManager 中无直接 getter

---

## 二、迁移目标

### 目标架构

```
SettingsFacade (唯一入口, 不变)
  ↕ get/set/save/reset
SettingsViewModel (新增, UI ↔ Facade 桥接)
  ↕ settings_changed signal
SettingsPage (新增, 表单 UI)
  ↕ 控件值绑定
QComboBox / QSpinBox / QCheckBox 等
```

### SettingsPage 约束

| 约束 | 说明 |
|------|------|
| 禁止 import ConfigManager | 通过 Facade 访问 |
| 禁止 import json | 配置读写由 Facade 处理 |
| 禁止读配置文件 | Facade.get() 读取 |
| 不持有 UI 状态 | 纯被动接收 Facade 通知 |

### SettingsFacade 保持不变

v5.2 已完成的 Facade 层不做修改。只在其上新增 SettingsViewModel 作为 UI 桥接。

---

## 三、SettingsViewModel 设计

### 3.1 信号

```python
class SettingsViewModel:
    settings_changed = Signal(str)  # key（单个字段变更）
    settings_reset = Signal()       # 全量重置
```

### 3.2 方法

```python
class SettingsViewModel:
    def __init__(self, facade: SettingsFacade)

    # 读取
    def get(self, key: str, default=None)
    def get_all(self) -> dict         # 返回当前配置快照

    # 写入（即时生效 + 保存）
    def set(self, key: str, value) -> None

    # 重置
    def reset(self, key: str | None = None) -> None

    # 告警规则
    def get_alerts(self) -> list[dict]
    def set_alert(self, path, red=None, warn=None, name=None)
    def reset_alerts(self) -> None

    # 节点管理
    def get_hosts(self) -> list
    def add_host(self, node_id, ip, port, token, alias="")
    def remove_host(self, node_id)
```

### 3.3 数据流

```
SettingsPage 控件值变化
  → vm.set(key, value)
  → facade.set(key, value) → 立即写入
  → facade.save()          → 磁盘持久化
  → vm.settings_changed.emit(key)
  → SettingsPage 刷新对应控件
  → MainWindow（如需：重建 AlertService / 刷新 SideNav）
```

### 3.4 不保存 UI 状态

SettingsVM 不保存 current_tab / scroll_position 等 UI 状态。纯配置读写层。

---

## 四、SettingsPage UI 设计

### 4.1 页面结构

```
SettingsPage(PageBase)
├── headerRow: QHBoxLayout
│   ├── title: QLabel("设置")
│   └── stretch
│
├── tabWidget: QTabWidget
│   ├── Tab 0: 通用 (General)
│   │   ├── 语言 (QComboBox: zh_CN / en)
│   │   ├── 主题 (QComboBox: dark / light)
│   │   └── UI 缩放 (QDoubleSpinBox: 0.5~2.0)
│   │
│   ├── Tab 1: 告警 (Alerts)
│   │   ├── 告警弹窗开关 (QCheckBox)
│   │   ├── CPU 使用率红线 (QSpinBox: 80~100)
│   │   ├── GPU 温度红线 (QSpinBox: 80~110)
│   │   ├── 内存红线 (QSpinBox: 80~100)
│   │   └── FPS 最低阈值 (QSpinBox: 1~300)
│   │
│   ├── Tab 2: 节点 (Nodes)
│   │   ├── 自动发现 (QCheckBox)
│   │   ├── 自动连接 (QCheckBox)
│   │   ├── UDP 端口 (QSpinBox: 1024~65535)
│   │   └── 已保存节点 (QListWidget, 只读)
│   │
│   ├── Tab 3: 外观 (Appearance)
│   │   ├── 主题 (QComboBox: dark / light)
│   │   └── UI 缩放 (QDoubleSpinBox: 0.5~2.0)
│   │
│   └── Tab 4: 高级 (Advanced)
│       ├── 日志级别 (QComboBox: DEBUG/INFO/WARNING/ERROR)
│       └── 调试模式 (QCheckBox)
│
└── bottomRow: QHBoxLayout
    ├── stretch
    └── saveBtn: QPushButton("保存")
```

### 4.2 字段映射

| Tab | 控件 | Facade key | 类型 |
|-----|------|------------|------|
| 通用 | lang_combo | language | str |
| 通用 | scale_spin | ui_scale | float |
| 告警 | alert_popup_check | alert_popup | bool |
| 告警 | cpu_red_spin | alert:cpu.total_usage.red | int |
| 节点 | auto_disc_check | auto_discovery | bool |
| 节点 | auto_conn_check | auto_connect | bool |
| 节点 | udp_spin | udp_port | int |
| 外观 | theme_combo | theme | str |
| 外观 | scale_spin2 | ui_scale | float |
| 高级 | log_combo | log_level | str |
| 高级 | debug_check | debug_mode | bool |

### 4.3 保存流程

```
用户修改控件 → 实时写入 VM（即时反馈）
用户点击"保存" → vm.save() → facade.save() → 磁盘
```

即时写入：控件值变化时调用 `vm.set(key, value)` → Facade 立即更新内存 + 通知 MainWindow。

---

## 五、生命周期

```python
def on_show(self):
    vm.settings_changed.connect(self._on_settings_changed)
    self._load_all()   # 从 VM 读取并填充控件

def on_hide(self):
    vm.settings_changed.disconnect(self._on_settings_changed)

def cleanup(self):
    vm.settings_changed.disconnect(self._on_settings_changed)
```

---

## 六、异常设计

### 6.1 配置读取失败

Facade.get() 内部已有默认值兜底，VM/Page 不需要处理。

### 6.2 保存失败

Facade.save() 内部 try/except，失败时 log.warning。Page 不需要额外处理。

### 6.3 磁盘满

Facade.save() 抛异常被 catch，Page 不受影响（内存状态仍有效）。

---

## 七、测试规划

### SettingsViewModel (test_v52_settings_vm.py)

| 用例 | 验证 |
|------|------|
| get 基本 | get("language") 返回当前值 |
| set 基本 | set("language", "en") → get("language") == "en" |
| reset 单字段 | reset("language") → 恢复默认 |
| reset 全部 | reset(None) → 全部恢复默认 |
| settings_changed 信号 | set 后 emit key |
| get_all | 返回完整配置快照 |

### SettingsPage (test_v52_settings_page.py)

| 用例 | 验证 |
|------|------|
| VM 注入 | set_facade 正常 |
| 控件初始化 | on_show 后控件显示当前值 |
| 生命周期 | on_show/on_hide 不崩溃 |
| 源码扫描 | 无 ConfigManager / json import |

---

## 八、迁移步骤

### Phase 3-6A（当前）：设计文档
- 输出本设计文档

### Phase 3-6B：SettingsViewModel
- 新增 host/viewmodels/settings_vm.py
- 单元测试：test_v52_settings_vm.py

### Phase 3-6C：SettingsPage UI
- 重写 host/gui/pages/settings_page.py
- 5 标签页 + 保存按钮
- 单元测试：test_v52_settings_page.py
- 全量回归

---

## 九、禁止事项

| 禁止项 | 原因 |
|--------|------|
| SettingsPage import ConfigManager | Facade 唯一入口 |
| SettingsPage import json | 配置读写由 Facade 处理 |
| SettingsPage 读配置文件 | Facade.get() |
| 修改 ConfigManager / host/config.py | 底层不变 |
| 修改 SettingsFacade | Phase 2 已完成 |
| 引入 QTimer | Signal 驱动架构 |
