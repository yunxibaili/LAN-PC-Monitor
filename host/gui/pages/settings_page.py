# -*- coding: utf-8 -*-
"""
SettingsPage —— 设置页（v5.2 Phase 4-6B Redesign）。

布局：
  Sidebar (5 sections) + ContentStack

数据流：
  SettingsVM → SettingsPage → 控件
  控件值变化 → vm.set() (内存) → dirty=True
  保存按钮 → vm.save() → 一次写盘

约束：
  - 不访问 ConfigManager / Facade
  - 只调用 VM public API
  - UI 不直接映射 Config Key
"""
import logging

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFrame, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QSpinBox, QStackedWidget,
    QVBoxLayout, QWidget,
)

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.typography import ThemeTypography as TT
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.pages.base_page import PageBase
from common.i18n import tr

log = logging.getLogger("host.gui.settings_page")


class _SidebarItem(QFrame):
    """侧边栏导航项。"""
    clicked = pyqtSignal()

    def __init__(self, label, parent=None):
        super().__init__(parent)
        self._label_text = label
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            _SidebarItem {{
                background: transparent;
                border-radius: 8px;
                padding: 0 12px;
            }}
            _SidebarItem:hover {{
                background: {TC.BG_HOVER};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: TT.BODY['size']px; background: transparent;")
        layout.addWidget(self._lbl)

    def set_active(self, active):
        if active:
            self.setStyleSheet(f"""
                _SidebarItem {{
                    background: {TC.BG_CARD};
                    border: 1px solid {TC.ACCENT_PRIMARY};
                    border-radius: 8px;
                }}
            """)
            self._lbl.setStyleSheet(
                f"color: {TC.TEXT_PRIMARY}; font-size: TT.BODY['size']px; font-weight: 600; background: transparent;")
        else:
            self.setStyleSheet(f"""
                _SidebarItem {{
                    background: transparent;
                    border-radius: 8px;
                }}
                _SidebarItem:hover {{
                    background: {TC.BG_HOVER};
                }}
            """)
            self._lbl.setStyleSheet(
                f"color: {TC.TEXT_SECONDARY}; font-size: TT.BODY['size']px; background: transparent;")

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class SettingsPage(PageBase):
    """设置页：Sidebar + ContentStack + Save/Status。"""

    PAGE_ID = "settings"

    _SECTIONS = ["General", "Connection", "Monitoring", "Appearance", "Alerts"]

    _SECTION_DISPLAY = {
        "General": tr("settings.tab.general"),
        "Connection": tr("settings.tab.nodes"),
        "Monitoring": tr("settings.tab.collector"),
        "Appearance": tr("settings.theme"),
        "Alerts": tr("settings.tab.alerts"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vm = None
        self._section_widgets = {}
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Header ----
        header = QHBoxLayout()
        header.setContentsMargins(S.LG, S.SM, S.LG, S.SM)
        title = QLabel(tr("settings.title_nav"))
        title.setStyleSheet(
            f"font-size: TT.TITLE_MEDIUM['size']px; font-weight: bold; color: {TC.TEXT_PRIMARY}; background: transparent;")
        header.addWidget(title)
        header.addStretch(1)
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(
            f"color: {TC.TEXT_DISABLED}; font-size: TT.BODY_SMALL['size']px; background: transparent;")
        header.addWidget(self._status_lbl)
        root.addLayout(header)

        # ---- Body: Sidebar + ContentStack ----
        body = QHBoxLayout()
        body.setContentsMargins(S.LG, 0, S.LG, 0)
        body.setSpacing(S.LG)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {TC.BG_CARD};
                border: 1px solid {TC.BORDER_DEFAULT};
                border-radius: 12px;
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(S.SM, S.SM, S.SM, S.SM)
        sidebar_layout.setSpacing(S.XS)

        self._sidebar_items = {}
        for section in self._SECTIONS:
            display = self._SECTION_DISPLAY.get(section, section)
            item = _SidebarItem(display)
            item.clicked.connect(lambda s=section: self._switch_section(s))
            sidebar_layout.addWidget(item)
            self._sidebar_items[section] = item

        sidebar_layout.addStretch(1)
        body.addWidget(sidebar)

        # Content Stack
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"""
            QStackedWidget {{
                background: transparent;
            }}
        """)
        self._build_sections()
        body.addWidget(self._stack, 1)

        root.addLayout(body, 1)

        # ---- Bottom: Save + Status ----
        bottom = QHBoxLayout()
        bottom.setContentsMargins(S.LG, S.SM, S.LG, S.SM)
        self._dirty_lbl = QLabel("")
        self._dirty_lbl.setStyleSheet(
            f"color: {TC.STATUS_WARNING}; font-size: TT.BODY_SMALL['size']px; background: transparent;")
        bottom.addWidget(self._dirty_lbl)
        bottom.addStretch(1)
        self._save_btn = QPushButton("Save")
        self._save_btn.setFixedHeight(36)
        self._save_btn.setFixedWidth(120)
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._on_save)
        bottom.addWidget(self._save_btn)
        root.addLayout(bottom)

        # 默认选中 General
        self._switch_section("General")

    # ---------- Section 构建 ----------

    def _build_sections(self):
        self._section_widgets["General"] = self._build_general()
        self._section_widgets["Connection"] = self._build_connection()
        self._section_widgets["Monitoring"] = self._build_monitoring()
        self._section_widgets["Appearance"] = self._build_appearance()
        self._section_widgets["Alerts"] = self._build_alerts()
        for section, widget in self._section_widgets.items():
            self._stack.addWidget(widget)

    def _build_general(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(S.LG, S.LG, S.LG, S.LG)
        layout.setSpacing(S.MD)

        self._add_section_title(layout, "General")

        # Language
        row = self._add_form_row(layout, "Language")
        self._lang_combo = QComboBox()
        self._lang_combo.addItem("中文", "zh_CN")
        self._lang_combo.addItem("English", "en")
        self._lang_combo.currentIndexChanged.connect(self._mark_dirty)
        row.addWidget(self._lang_combo, 1)

        # Log Level
        row2 = self._add_form_row(layout, "Log Level")
        self._log_combo = QComboBox()
        for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
            self._log_combo.addItem(level, level)
        self._log_combo.currentIndexChanged.connect(self._mark_dirty)
        row2.addWidget(self._log_combo, 1)

        # Debug Mode
        self._debug_check = QCheckBox("Debug mode")
        self._debug_check.stateChanged.connect(self._mark_dirty)
        layout.addWidget(self._debug_check)

        layout.addStretch(1)
        return w

    def _build_connection(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(S.LG, S.LG, S.LG, S.LG)
        layout.setSpacing(S.MD)

        self._add_section_title(layout, "Connection")

        self._auto_disc_check = QCheckBox("Auto-discover nodes (UDP broadcast + mDNS)")
        self._auto_disc_check.stateChanged.connect(self._mark_dirty)
        layout.addWidget(self._auto_disc_check)

        self._auto_conn_check = QCheckBox("Auto-connect discovered nodes")
        self._auto_conn_check.stateChanged.connect(self._mark_dirty)
        layout.addWidget(self._auto_conn_check)

        row = self._add_form_row(layout, "UDP Port")
        self._udp_spin = QSpinBox()
        self._udp_spin.setRange(1024, 65535)
        self._udp_spin.valueChanged.connect(self._mark_dirty)
        row.addWidget(self._udp_spin, 1)

        layout.addStretch(1)
        return w

    def _build_monitoring(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(S.LG, S.LG, S.LG, S.LG)
        layout.setSpacing(S.MD)

        self._add_section_title(layout, "Monitoring")
        sub = QLabel("Data retention policy (days)")
        sub.setStyleSheet(f"color: {TC.TEXT_SECONDARY}; font-size: TT.BODY_SMALL['size']px; background: transparent;")
        layout.addWidget(sub)

        row1 = self._add_form_row(layout, "Metrics retention")
        self._ret_metrics = QSpinBox()
        self._ret_metrics.setRange(1, 365)
        self._ret_metrics.setValue(30)
        self._ret_metrics.setSuffix(" days")
        self._ret_metrics.valueChanged.connect(self._mark_dirty)
        row1.addWidget(self._ret_metrics, 1)

        row2 = self._add_form_row(layout, "Alerts retention")
        self._ret_alerts = QSpinBox()
        self._ret_alerts.setRange(1, 365)
        self._ret_alerts.setValue(90)
        self._ret_alerts.setSuffix(" days")
        self._ret_alerts.valueChanged.connect(self._mark_dirty)
        row2.addWidget(self._ret_alerts, 1)

        row3 = self._add_form_row(layout, "Sessions retention")
        self._ret_sessions = QSpinBox()
        self._ret_sessions.setRange(1, 365)
        self._ret_sessions.setValue(90)
        self._ret_sessions.setSuffix(" days")
        self._ret_sessions.valueChanged.connect(self._mark_dirty)
        row3.addWidget(self._ret_sessions, 1)

        layout.addStretch(1)
        return w

    def _build_appearance(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(S.LG, S.LG, S.LG, S.LG)
        layout.setSpacing(S.MD)

        self._add_section_title(layout, "Appearance")

        row = self._add_form_row(layout, "UI Scale")
        self._scale_spin = QDoubleSpinBox()
        self._scale_spin.setRange(0.5, 2.0)
        self._scale_spin.setSingleStep(0.1)
        self._scale_spin.setSuffix("x")
        self._scale_spin.valueChanged.connect(self._mark_dirty)
        row.addWidget(self._scale_spin, 1)

        layout.addStretch(1)
        return w

    def _build_alerts(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(S.LG, S.LG, S.LG, S.LG)
        layout.setSpacing(S.MD)

        self._add_section_title(layout, "Alerts")

        self._alert_popup_check = QCheckBox("Enable alert popups")
        self._alert_popup_check.stateChanged.connect(self._mark_dirty)
        layout.addWidget(self._alert_popup_check)

        # Alert thresholds
        row = self._add_form_row(layout, "CPU threshold (%)")
        self._cpu_red_spin = QSpinBox()
        self._cpu_red_spin.setRange(50, 100)
        self._cpu_red_spin.setSuffix("%")
        self._cpu_red_spin.valueChanged.connect(self._mark_dirty)
        row.addWidget(self._cpu_red_spin, 1)

        row2 = self._add_form_row(layout, "GPU temp threshold (°C)")
        self._gpu_temp_spin = QSpinBox()
        self._gpu_temp_spin.setRange(60, 110)
        self._gpu_temp_spin.setSuffix("°C")
        self._gpu_temp_spin.valueChanged.connect(self._mark_dirty)
        row2.addWidget(self._gpu_temp_spin, 1)

        row3 = self._add_form_row(layout, "RAM threshold (%)")
        self._ram_red_spin = QSpinBox()
        self._ram_red_spin.setRange(50, 100)
        self._ram_red_spin.setSuffix("%")
        self._ram_red_spin.valueChanged.connect(self._mark_dirty)
        row3.addWidget(self._ram_red_spin, 1)

        row4 = self._add_form_row(layout, "FPS min threshold")
        self._fps_min_spin = QSpinBox()
        self._fps_min_spin.setRange(1, 300)
        self._fps_min_spin.setSuffix(" FPS")
        self._fps_min_spin.valueChanged.connect(self._mark_dirty)
        row4.addWidget(self._fps_min_spin, 1)

        layout.addStretch(1)
        return w

    # ---------- UI Helpers ----------

    def _add_section_title(self, layout, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: TT.TITLE_SMALL['size']px; font-weight: bold; color: {TC.TEXT_PRIMARY}; "
            f"background: transparent; margin-bottom: 8px;")
        layout.addWidget(lbl)

    def _add_form_row(self, layout, label_text):
        row = QHBoxLayout()
        row.setSpacing(S.SM)
        lbl = QLabel(label_text)
        lbl.setFixedWidth(140)
        lbl.setStyleSheet(
            f"color: {TC.TEXT_SECONDARY}; font-size: TT.BODY['size']px; background: transparent;")
        row.addWidget(lbl)
        layout.addLayout(row)
        return row

    # ---------- Section 切换 ----------

    def _switch_section(self, section):
        for name, item in self._sidebar_items.items():
            item.set_active(name == section)
        if section in self._section_widgets:
            self._stack.setCurrentWidget(self._section_widgets[section])

    # ---------- Dirty State ----------

    def _mark_dirty(self):
        """P1.5: 委托 VM 标记脏（单一数据源）。"""
        if self._vm:
            self._vm._mark_dirty()
        self._dirty_lbl.setText("● Unsaved changes")
        self._save_btn.setEnabled(True)

    def _clear_dirty(self):
        """P1.5: 委托 VM 清除脏标记。"""
        if self._vm:
            self._vm._clear_dirty()
        self._dirty_lbl.setText("")
        self._save_btn.setEnabled(False)

    # ---------- ViewModel 注入 ----------

    def set_view_model(self, vm) -> None:
        self._vm = vm

    # ---------- 生命周期 ----------

    def on_show(self) -> None:
        super().on_show()
        self._load_all()
        self._clear_dirty()

    def on_hide(self) -> None:
        super().on_hide()

    # ---------- 数据加载 ----------

    def _load_all(self) -> None:
        if not self._vm:
            return
        vm = self._vm

        # General
        self._lang_combo.setCurrentIndex(
            0 if vm.get("language") == "zh_CN" else 1)
        self._log_combo.setCurrentIndex(
            max(0, self._log_combo.findData(vm.get("log_level", "INFO"))))
        self._debug_check.setChecked(vm.get("debug_mode", False))

        # Connection
        self._auto_disc_check.setChecked(vm.get("auto_discovery", True))
        self._auto_conn_check.setChecked(vm.get("auto_connect", True))
        self._udp_spin.setValue(vm.get("udp_port", 12346))

        # Appearance
        self._scale_spin.setValue(vm.get("ui_scale", 1.0))

        # Alerts
        self._alert_popup_check.setChecked(vm.get("alert_popup", True))
        self._cpu_red_spin.setValue(
            (vm.get_alert("cpu.total_usage") or {}).get("red", 95))
        self._gpu_temp_spin.setValue(
            (vm.get_alert("gpu.core_temp_c") or {}).get("red", 90))
        self._ram_red_spin.setValue(
            (vm.get_alert("ram.usage_percent") or {}).get("red", 90))
        self._fps_min_spin.setValue(
            (vm.get_alert("fps.fps") or {}).get("red_min", 30))

        # Monitoring (retention)
        self._ret_metrics.setValue(vm.get("retention_metrics", 30))
        self._ret_alerts.setValue(vm.get("retention_alerts", 90))
        self._ret_sessions.setValue(vm.get("retention_sessions", 90))

    # ---------- 保存 ----------

    def _on_save(self) -> None:
        if not self._vm or not self._vm.is_dirty():
            return
        vm = self._vm

        # General
        vm.set("language", self._lang_combo.currentData())
        vm.set("log_level", self._log_combo.currentData())
        vm.set("debug_mode", self._debug_check.isChecked())

        # Connection
        vm.set("auto_discovery", self._auto_disc_check.isChecked())
        vm.set("auto_connect", self._auto_conn_check.isChecked())
        vm.set("udp_port", self._udp_spin.value())

        # Appearance
        vm.set("ui_scale", self._scale_spin.value())

        # Alerts
        vm.set("alert_popup", self._alert_popup_check.isChecked())
        vm.set_alert("cpu.total_usage", red=self._cpu_red_spin.value())
        vm.set_alert("gpu.core_temp_c", red=self._gpu_temp_spin.value())
        vm.set_alert("ram.usage_percent", red=self._ram_red_spin.value())
        vm.set_alert("fps.fps", red_min=self._fps_min_spin.value())

        # Monitoring (retention)
        vm.set("retention_metrics", self._ret_metrics.value())
        vm.set("retention_alerts", self._ret_alerts.value())
        vm.set("retention_sessions", self._ret_sessions.value())

        # 一次写盘
        vm.save()
        self._clear_dirty()
        self._show_save_feedback()

    def _show_save_feedback(self):
        self._status_lbl.setText("✓ Saved")
        self._status_lbl.setStyleSheet(
            f"color: {TC.STATUS_ONLINE}; font-size: TT.BODY_SMALL['size']px; font-weight: 600; background: transparent;")
        QTimer.singleShot(2000, lambda: self._status_lbl.setText(""))
