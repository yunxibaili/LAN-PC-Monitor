# 开发规范

> **Version**: v5.2
> **Status**: CURRENT

## 1. 环境

- Python 3.10+
- PyQt5
- pyqtgraph (可选, 图表)

```bash
pip install -r requirements-agent.txt -r requirements-host.txt
```

## 2. 目录规范

```
agent/        副机端服务
host/         主机端 GUI
common/       公共模块
tests/        测试
docs/         文档
```

## 3. 新增页面流程

```
1. 创建 Page (host/gui/pages/xxx_page.py)
   └── 继承 PageBase
   └── 实现 set_view_model() / on_show() / on_hide()

2. 创建/复用 ViewModel (host/viewmodels/xxx_vm.py)
   └── 不含 PyQt5
   └── 从 Store 提取数据
   └── 提供 Signal 通知页面

3. 创建/复用 Widget (host/gui/widgets/xxx.py)
   └── 只导入 Theme
   └── 纯 UI 组件

4. 注册到 MainWindow
   └── _init_viewmodels() 中创建 VM
   └── _init_ui() 中创建 Page
   └── VM 注入 Page

5. 添加测试
   └── tests/test_v52_xxx.py
```

## 4. 新增 Widget 流程

```
1. 创建 Widget (host/gui/widgets/xxx.py)
   └── 继承 QFrame / QWidget

2. 使用 Theme 系统
   └── from host.gui.theme.colors import ThemeColors as TC
   └── from host.gui.theme.spacing import ThemeSpacing as S

3. 禁止硬编码
   └── 不用 "#ffffff"
   └── 不用 "16px"
   └── 用 TC.TEXT_PRIMARY / S.LG

4. 添加测试
   └── tests/test_v52_widgets.py
```

## 5. 代码规范

### Python

- UTF-8 编码
- 类型注解
- docstring (中文)
- 日志: `logging.getLogger("host.gui.xxx")`

### PyQt5

- Signal 命名: `snake_case`
- Slot 命名: `_on_xxx`
- Widget 命名: `PascalCase`

### 测试

- 文件名: `test_v52_xxx.py`
- 结构: check(name, cond, detail)
- 每个测试函数: `test_xxx()`
- main() 汇总结果

## 6. 禁止事项

| 禁止 | 原因 |
|------|------|
| Page 直接访问 Store | 违反分层 |
| Widget 处理业务逻辑 | 职责混乱 |
| ViewModel 导入 PyQt5 | 耦合 UI |
| 硬编码颜色 | 破坏主题 |
| QTimer 轮询 | 性能浪费 |

## 7. 运行测试

```bash
# 全量测试
python tests/test_v52_*.py

# 单个测试
python tests/test_v52_dashboard_vm.py
```

## 8. 打包

```bash
pip install pyinstaller
python build_agent.py   # Agent exe
python build_host.py    # Host exe
```
