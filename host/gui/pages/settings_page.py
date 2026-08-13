# -*- coding: utf-8 -*-
"""
SettingsPage —— 设置页（v5.2 Phase 3-6B）。

数据流：
  SettingsFacade → SettingsViewModel → SettingsPage → 控件
  控件值变化 → vm.set() → Facade 写入 + 磁盘持久化

约束：
  - 不访问 ConfigManager / json 文件
  - 通过 SettingsViewModel 间接访问
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QGroupBox, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.pages.base_page import PageBase

log = logging.getLogger("host.gui.settings_page")


class SettingsPage(PageBase):
    """设置页：5 个标签页 + 保存按钮。"""

    PAGE_ID = "settings"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vm = None
        self._widgets = {}
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        # 标题
        header = QHBoxLayout()
        title = QLabel("⚙ 设置")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {TC.TEXT_PRIMARY};")
        header.addWidget(title)
        header.addStretch(1)
        root.addLayout(header)

        # 标签页
        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_general_tab(), "通用")
        self._tabs.addTab(self._build_alerts_tab(), "告警")
        self._tabs.addTab(self._build_nodes_tab(), "节点")
        self._tabs.addTab(self._build_advanced_tab(), "高级")
        root.addWidget(self._tabs, 1)

        # 保存按钮
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        save_btn = QPushButton("保存设置")
        save_btn.setFixedHeight(36)
        save_btn.setFixedWidth(120)
        save_btn.clicked.connect(self._on_save)
        bottom.addWidget(save_btn)
        root.addLayout(bottom)

    # ---------- Tab 0: 通用 ----------

    def _build_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        # 语言
        row = QHBoxLayout()
        row.addWidget(QLabel("语言:"))
        self._lang_combo = QComboBox()
        self._lang_combo.addItem("中文", "zh_CN")
        self._lang_combo.addItem("English", "en")
        row.addWidget(self._lang_combo, 1)
        row.addStretch(1)
        layout.addLayout(row)

        # UI 缩放
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("UI 缩放:"))
        self._scale_spin = QDoubleSpinBox()
        self._scale_spin.setRange(0.5, 2.0)
        self._scale_spin.setSingleStep(0.1)
        self._scale_spin.setSuffix("x")
        row2.addWidget(self._scale_spin, 1)
        row2.addStretch(1)
        layout.addLayout(row2)

        layout.addStretch(1)
        return tab

    # ---------- Tab 1: 告警 ----------

    def _build_alerts_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        # 告警弹窗开关
        self._alert_popup_check = QCheckBox("启用告警弹窗通知")
        layout.addWidget(self._alert_popup_check)

        # CPU 红线
        row = QHBoxLayout()
        row.addWidget(QLabel("CPU 使用率红线:"))
        self._cpu_red_spin = QSpinBox()
        self._cpu_red_spin.setRange(50, 100)
        self._cpu_red_spin.setSuffix("%")
        row.addWidget(self._cpu_red_spin)
        row.addStretch(1)
        layout.addLayout(row)

        # GPU 温度红线
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("GPU 温度红线:"))
        self._gpu_temp_spin = QSpinBox()
        self._gpu_temp_spin.setRange(60, 110)
        self._gpu_temp_spin.setSuffix("°C")
        row2.addWidget(self._gpu_temp_spin)
        row2.addStretch(1)
        layout.addLayout(row2)

        # 内存红线
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("内存红线:"))
        self._ram_red_spin = QSpinBox()
        self._ram_red_spin.setRange(50, 100)
        self._ram_red_spin.setSuffix("%")
        row3.addWidget(self._ram_red_spin)
        row3.addStretch(1)
        layout.addLayout(row3)

        # FPS 最低阈值
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("FPS 最低阈值:"))
        self._fps_min_spin = QSpinBox()
        self._fps_min_spin.setRange(1, 300)
        self._fps_min_spin.setSuffix(" FPS")
        row4.addWidget(self._fps_min_spin)
        row4.addStretch(1)
        layout.addLayout(row4)

        layout.addStretch(1)
        return tab

    # ---------- Tab 2: 节点 ----------

    def _build_nodes_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        self._auto_disc_check = QCheckBox("自动发现节点 (UDP 广播 + mDNS)")
        layout.addWidget(self._auto_disc_check)

        self._auto_conn_check = QCheckBox("发现节点后自动连接")
        layout.addWidget(self._auto_conn_check)

        row = QHBoxLayout()
        row.addWidget(QLabel("UDP 监听端口:"))
        self._udp_spin = QSpinBox()
        self._udp_spin.setRange(1024, 65535)
        row.addWidget(self._udp_spin)
        row.addStretch(1)
        layout.addLayout(row)

        layout.addStretch(1)
        return tab

    # ---------- Tab 3: 高级 ----------

    def _build_advanced_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        row = QHBoxLayout()
        row.addWidget(QLabel("日志级别:"))
        self._log_combo = QComboBox()
        for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
            self._log_combo.addItem(level, level)
        row.addWidget(self._log_combo)
        row.addStretch(1)
        layout.addLayout(row)

        self._debug_check = QCheckBox("调试模式")
        layout.addWidget(self._debug_check)

        layout.addStretch(1)
        return tab

    # ---------- ViewModel 注入 ----------

    def set_view_model(self, vm) -> None:
        self._vm = vm

    # ---------- 生命周期 ----------

    def on_show(self) -> None:
        super().on_show()
        self._load_all()

    def on_hide(self) -> None:
        super().on_hide()

    # ---------- 数据加载/保存 ----------

    def _load_all(self) -> None:
        """从 VM 读取并填充控件。"""
        if not self._vm:
            return
        vm = self._vm
        self._lang_combo.setCurrentIndex(
            0 if vm.get("language") == "zh_CN" else 1)
        self._scale_spin.setValue(vm.get("ui_scale", 1.0))
        self._alert_popup_check.setChecked(vm.get("alert_popup", True))
        self._cpu_red_spin.setValue(vm.get("cpu_red", 95))
        self._gpu_temp_spin.setValue(vm.get("gpu_temp_red", 90))
        self._ram_red_spin.setValue(vm.get("ram_red", 90))
        self._fps_min_spin.setValue(vm.get("fps_red_min", 30))
        self._auto_disc_check.setChecked(vm.get("auto_discovery", True))
        self._auto_conn_check.setChecked(vm.get("auto_connect", True))
        self._udp_spin.setValue(vm.get("udp_port", 12346))
        self._log_combo.setCurrentIndex(
            max(0, self._log_combo.findData(vm.get("log_level", "INFO"))))
        self._debug_check.setChecked(vm.get("debug_mode", False))

    def _on_save(self) -> None:
        """保存所有控件值到 VM。"""
        if not self._vm:
            return
        vm = self._vm
        vm.set("language", self._lang_combo.currentData())
        vm.set("ui_scale", self._scale_spin.value())
        vm.set("alert_popup", self._alert_popup_check.isChecked())
        vm.set("auto_discovery", self._auto_disc_check.isChecked())
        vm.set("auto_connect", self._auto_conn_check.isChecked())
        vm.set("udp_port", self._udp_spin.value())
        vm.set("log_level", self._log_combo.currentData())
        vm.set("debug_mode", self._debug_check.isChecked())
        vm.facade.save()
        log.info("设置已保存")
