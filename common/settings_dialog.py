# -*- coding: utf-8 -*-
"""
设置中心对话框（SettingsDialog）—— 类似 OBS / VS Code 的设置中心。

v5.0 配置体系优化：
- 取代启动阶段的语言/节点连接弹窗，改为设置中心统一管理。
- 五个分类 Tab：通用 / 告警 / 采集 / 节点 / 高级。
- 通过 common.config_manager 读写两端配置，保存后持久化。

入口：Dashboard 右上角齿轮按钮（host/gui/main_window.py、agent/gui/main_window.py）。
"""
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                             QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QMessageBox, QSpinBox,
                             QTabWidget, QVBoxLayout, QWidget)

from common import theme
from common.config_manager import get_config_manager
from common.i18n import load_language, tr
from common.theme import remove_help_button

log = logging.getLogger("common.settings")


class SettingsDialog(QDialog):
    """设置中心对话框（Host 端）。"""

    def __init__(self, parent=None, on_applied=None):
        """
        :param parent:     父窗口
        :param on_applied: 应用设置后的回调（如刷新语言/主题/告警）
        """
        super().__init__(parent)
        self.cm = get_config_manager()
        self._on_applied = on_applied
        self._changed = False
        self.setWindowTitle(tr("settings.title"))
        self.setMinimumSize(560, 460)
        remove_help_button(self)
        self._build_ui()
        self._load_values()

    # ---------- UI ----------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self._build_general_tab()
        self._build_alerts_tab()
        self._build_collector_tab()
        self._build_nodes_tab()
        self._build_advanced_tab()
        root.addWidget(self.tabs)

        btns = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._on_save)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _build_general_tab(self) -> None:
        tab = QWidget()
        form = QFormLayout(tab)

        # 语言
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("中文", "zh_CN")
        self.lang_combo.addItem("English", "en")
        form.addRow(tr("settings.language"), self.lang_combo)

        # 主题
        self.theme_combo = QComboBox()
        self.theme_combo.addItem(tr("settings.theme.dark"), "dark")
        self.theme_combo.addItem(tr("settings.theme.light"), "light")
        form.addRow(tr("settings.theme"), self.theme_combo)

        # UI 缩放
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.5, 2.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setDecimals(1)
        form.addRow(tr("settings.ui_scale"), self.scale_spin)

        self.tabs.addTab(tab, tr("settings.tab.general"))

    def _build_alerts_tab(self) -> None:
        tab = QWidget()
        form = QFormLayout(tab)

        # CPU 红线
        self.cpu_red_spin = QSpinBox()
        self.cpu_red_spin.setRange(0, 100)
        self.cpu_red_spin.setSuffix("%")
        form.addRow(tr("settings.alert.cpu_red"), self.cpu_red_spin)

        # GPU 温度红线
        self.gpu_temp_spin = QSpinBox()
        self.gpu_temp_spin.setRange(40, 110)
        self.gpu_temp_spin.setSuffix("°C")
        form.addRow(tr("settings.alert.gpu_temp"), self.gpu_temp_spin)

        # 内存红线
        self.ram_red_spin = QSpinBox()
        self.ram_red_spin.setRange(0, 100)
        self.ram_red_spin.setSuffix("%")
        form.addRow(tr("settings.alert.ram_red"), self.ram_red_spin)

        # FPS 告警（下限）
        self.fps_min_spin = QSpinBox()
        self.fps_min_spin.setRange(1, 300)
        form.addRow(tr("settings.alert.fps_min"), self.fps_min_spin)

        # 告警弹窗
        self.alert_popup_check = QCheckBox()
        form.addRow(tr("settings.alert.popup"), self.alert_popup_check)

        self.tabs.addTab(tab, tr("settings.tab.alerts"))

    def _build_collector_tab(self) -> None:
        tab = QWidget()
        form = QFormLayout(tab)

        # 采样频率
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.2, 10.0)
        self.interval_spin.setSingleStep(0.2)
        self.interval_spin.setSuffix(" s")
        form.addRow(tr("settings.collector.interval"), self.interval_spin)

        # GPU 采集开关
        self.gpu_check = QCheckBox()
        form.addRow(tr("settings.collector.gpu"), self.gpu_check)

        # FPS 采集开关
        self.fps_check = QCheckBox()
        form.addRow(tr("settings.collector.fps"), self.fps_check)

        # 进程采集开关
        self.proc_check = QCheckBox()
        form.addRow(tr("settings.collector.process"), self.proc_check)

        self.tabs.addTab(tab, tr("settings.tab.collector"))

    def _build_nodes_tab(self) -> None:
        tab = QWidget()
        root = QVBoxLayout(tab)

        # 自动发现 / 自动连接
        top = QHBoxLayout()
        self.auto_disc_check = QCheckBox(tr("settings.node.auto_discovery"))
        top.addWidget(self.auto_disc_check)
        self.auto_conn_check = QCheckBox(tr("settings.node.auto_connect"))
        top.addWidget(self.auto_conn_check)
        top.addStretch(1)
        root.addLayout(top)

        # 节点列表（只读展示，管理在 Dashboard 节点列表）
        lbl = QLabel(tr("settings.node.list_hint"))
        lbl.setStyleSheet(f"color: {theme.COLOR_NA};")
        root.addWidget(lbl)
        self.nodes_list = QListWidget()
        root.addWidget(self.nodes_list)

        self.tabs.addTab(tab, tr("settings.tab.nodes"))

    def _build_advanced_tab(self) -> None:
        tab = QWidget()
        form = QFormLayout(tab)

        # 日志等级
        self.log_level_combo = QComboBox()
        for lv in ("DEBUG", "INFO", "WARNING", "ERROR"):
            self.log_level_combo.addItem(lv, lv)
        form.addRow(tr("settings.log_level"), self.log_level_combo)

        # 调试模式
        self.debug_check = QCheckBox()
        form.addRow(tr("settings.debug_mode"), self.debug_check)

        self.tabs.addTab(tab, tr("settings.tab.advanced"))

    # ---------- 加载 / 保存 ----------

    def _load_values(self) -> None:
        cm = self.cm
        # 通用
        idx = self.lang_combo.findData(cm.get_language())
        self.lang_combo.setCurrentIndex(max(0, idx))
        idx = self.theme_combo.findData(cm.get_theme())
        self.theme_combo.setCurrentIndex(max(0, idx))
        self.scale_spin.setValue(cm.get_ui_scale())
        # 告警
        cpu = cm.get_alert("cpu.total_usage") or {}
        self.cpu_red_spin.setValue(int(cpu.get("red", 95)))
        gpu = cm.get_alert("gpu.core_temp_c") or {}
        self.gpu_temp_spin.setValue(int(gpu.get("red", 90)))
        ram = cm.get_alert("ram.usage_percent") or {}
        self.ram_red_spin.setValue(int(ram.get("red", 90)))
        fps = cm.get_alert("fps.fps") or {}
        self.fps_min_spin.setValue(int(fps.get("red_min", 30)))
        self.alert_popup_check.setChecked(
            bool(cm.host_cfg.get("alert_popup", True)))
        # 采集
        self.interval_spin.setValue(cm.get_collector_interval())
        self.gpu_check.setChecked(bool(cm.get_collector("gpu")))
        fps_mode = cm.get_collector("fps")
        self.fps_check.setChecked(fps_mode not in (False, "none"))
        self.proc_check.setChecked(bool(cm.get_collector("process", True)))
        # 节点
        self.auto_disc_check.setChecked(cm.get_auto_discovery())
        self.auto_conn_check.setChecked(cm.get_auto_connect())
        for h in cm.get_hosts():
            self.nodes_list.addItem(
                f"{h.get('alias','?')}  {h.get('ip','')}:{h.get('port','')}")
        # 高级
        idx = self.log_level_combo.findData(cm.get_log_level())
        self.log_level_combo.setCurrentIndex(max(0, idx))
        self.debug_check.setChecked(cm.get_debug_mode())

    def _on_save(self) -> None:
        cm = self.cm
        # 通用
        cm.set_language(self.lang_combo.currentData())
        cm.set_theme(self.theme_combo.currentData())
        cm.set_ui_scale(self.scale_spin.value())
        # 告警
        cm.set_alert("cpu.total_usage", red=self.cpu_red_spin.value())
        cm.set_alert("gpu.core_temp_c", red=self.gpu_temp_spin.value())
        cm.set_alert("ram.usage_percent", red=self.ram_red_spin.value())
        cm.set_alert("fps.fps", red_min=self.fps_min_spin.value())
        cm.host_cfg["alert_popup"] = self.alert_popup_check.isChecked()
        # 采集
        cm.set_collector_interval(self.interval_spin.value())
        cm.set_collector("gpu", self.gpu_check.isChecked())
        cm.set_collector("fps", "presentmon" if self.fps_check.isChecked() else "none")
        cm.set_collector("process", self.proc_check.isChecked())
        # 节点
        cm.set_auto_discovery(self.auto_disc_check.isChecked())
        cm.set_auto_connect(self.auto_conn_check.isChecked())
        # 高级
        cm.set_log_level(self.log_level_combo.currentData())
        cm.set_debug_mode(self.debug_check.isChecked())

        cm.save_all()
        # 语言即时生效
        load_language(cm.get_language())
        self._changed = True
        if self._on_applied:
            try:
                self._on_applied()
            except Exception:
                pass
        QMessageBox.information(self, tr("settings.saved_title"),
                                tr("settings.saved_msg"))
        self.accept()
