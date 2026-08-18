# AGENTS.md

> **本项目的 UI 设计规范基于 Gentelella v4**
> **所有新增页面和组件必须遵循 DESIGN.md 中的规范。**

---

## 项目概述

LAN-PC-Monitor：局域网远程电脑监控系统。

- **Agent**（被监控端）：Python 3.10+ / PyQt5，采集硬件数据并推送
- **Host**（监控端）：Python 3.10+ / PyQt5 / SQLite，集中展示所有节点状态

## 架构

```
Agent Collectors → Aggregator → WebSocket
  ↓
Host DataController → Store → ViewModel → Page → Widget
  ↓
Theme (基于 Gentelella v4 暗色模式)
```

## UI 设计规范

**所有 UI 开发必须遵循 [DESIGN.md](DESIGN.md)。**

核心规则：
1. 颜色/间距/字体走 Theme token（`ThemeColors` / `ThemeSpacing` / `ThemeTypography`）
2. 组件复用 `host/gui/widgets/` 现有组件
3. 新组件放 `host/gui/widgets/xxx.py`，只 import Theme
4. 页面放 `host/gui/pages/xxx_page.py`，继承 `PageBase`
5. 禁止硬编码颜色/字号/间距
6. 参考 [Gentelella v4](https://github.com/ColorlibHQ/gentelella) 暗色模式

## 开发规范

详见 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)。

核心约束：
- Page 不碰 Store / Config / Storage / sqlite3
- ViewModel 纯 Python，不碰 PyQt5 / sqlite3
- sqlite3 仅限 `host/storage/`
- Signal 驱动（不轮询）

## 测试

```bash
python logs/run_all_tests_v3.py  # 全量回归
```

基线：994/994 PASS

## 参考资源

- **UI 设计规范**: [DESIGN.md](DESIGN.md)
- **架构文档**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **开发规范**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **路线图**: [docs/ROADMAP.md](docs/ROADMAP.md)
- **Gentelella 参考**: `gentelella-master/`（已 gitignore，仅参考，不入库）
