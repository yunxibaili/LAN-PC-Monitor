# -*- coding: utf-8 -*-
"""
Legacy Theme System — Agent GUI 兼容层。

状态: legacy
用途: Agent GUI 当前依赖此模块（DARK_QSS / COLOR_* / helper functions）
迁移: Phase 4-7 Agent GUI Upgrade 时决定

Host GUI 不使用此模块。新开发应使用 host/gui/theme。

注意: 本模块的 COLOR_* 常量与 host/gui/theme/colors.py 的 ThemeColors
存在色值差异（Agent 使用旧色板 #1e1e1e / #007acc，Host 使用新色板 #0F1117 / #3B82F6）。
这是有意设计，不是 bug。Agent 视觉统一属于 Phase 4-7 范围。
"""
from PyQt5.QtWidgets import QLabel

# ---------- 颜色定义 ----------
COLOR_BG = "#1e1e1e"          # 窗口背景
COLOR_TEXT = "#d4d4d4"        # 常规文字
COLOR_NORMAL = "#4ec9b0"      # 绿（正常）
COLOR_WARN = "#d7ba7d"        # 橙（警告）
COLOR_DANGER = "#f44747"      # 红（危险）
COLOR_NA = "#808080"          # 灰（N/A）
COLOR_ACCENT = "#007acc"      # 蓝（强调/选中）
COLOR_HIGHLIGHT = "#2d2d30"   # 选中背景

# ---------- 阈值（§14.1） ----------
# 使用率：<80 绿；80~95 橙；>95 红
USAGE_WARN, USAGE_DANGER = 80, 95
# 内存：<80 绿；80~90 橙；>90 红
RAM_WARN, RAM_DANGER = 80, 90
# 温度：<80 绿；80~85 橙；>85 红
TEMP_WARN, TEMP_DANGER = 80, 85
# GPU 热点：<95 绿；95~105 橙；>105 红
HOTSPOT_WARN, HOTSPOT_DANGER = 95, 105
# 磁盘使用率：<85 绿；85~95 橙；>95 红
DISK_WARN, DISK_DANGER = 85, 95
# 网络评分：≥80 绿；60~79 橙；<60 红
SCORE_WARN = 60
# RTT：<5ms 绿；5~20ms 橙；>20ms 红
RTT_WARN, RTT_DANGER = 5, 20

# 全局 QSS 深色主题（common 自包含，不依赖 host.gui.theme）
DARK_QSS = f"""
    * {{ font-family: 'Microsoft YaHei', Consolas, sans-serif; }}
    QMainWindow, QDialog, QWidget {{ background-color: {COLOR_BG}; color: {COLOR_TEXT}; }}
    QLabel {{ background: transparent; color: {COLOR_TEXT}; }}
    QLabel#panel_title {{
        color: {COLOR_ACCENT}; font-weight: bold; font-size: 14px;
        border-bottom: 1px solid #3e3e42; padding-bottom: 4px;
    }}
    QGroupBox {{
        border: 1px solid #3e3e42; border-radius: 4px; margin-top: 8px;
        color: {COLOR_TEXT};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {COLOR_ACCENT};
    }}
    QListWidget, QPlainTextEdit {{ background-color: #252526; border: 1px solid #3e3e42; }}
    QPushButton {{ background-color: #3c3c3c; color: {COLOR_TEXT}; border: 1px solid #565656; padding: 6px 12px; border-radius: 3px; }}
    QPushButton:hover {{ background-color: #4a4a4a; }}
    QPushButton:pressed {{ background-color: #2d2d30; }}
    QScrollBar:vertical {{ background: #252526; width: 10px; }}
    QScrollBar::handle:vertical {{ background: #3f3f46; min-height: 24px; border-radius: 5px; }}
    """


def usage_color(percent):
    """使用率阈值变色（CPU/GPU/内存）：N/A → 灰。"""
    if percent == "N/A" or percent is None:
        return COLOR_NA
    if percent > USAGE_DANGER:
        return COLOR_DANGER
    if percent > USAGE_WARN:
        return COLOR_WARN
    return COLOR_NORMAL


def temp_color(temp_c):
    """温度阈值变色：N/A → 灰。"""
    if temp_c == "N/A" or temp_c is None:
        return COLOR_NA
    if temp_c > TEMP_DANGER:
        return COLOR_DANGER
    if temp_c > TEMP_WARN:
        return COLOR_WARN
    return COLOR_NORMAL


def score_color(score):
    """网络评分变色：N/A → 灰。"""
    if score == "N/A" or score is None:
        return COLOR_NA
    if score < SCORE_WARN:
        return COLOR_DANGER
    if score < 80:
        return COLOR_WARN
    return COLOR_NORMAL


def rtt_color(rtt_ms):
    """RTT 变色：N/A → 灰。"""
    if rtt_ms == "N/A" or rtt_ms is None:
        return COLOR_NA
    if rtt_ms > RTT_DANGER:
        return COLOR_DANGER
    if rtt_ms > RTT_WARN:
        return COLOR_WARN
    return COLOR_NORMAL


def apply_color(label: QLabel, color: str) -> None:
    """动态设置 QLabel 文字颜色（保留字体设置）。"""
    label.setStyleSheet(f"color: {color}; background: transparent;")


# 问号帮助按钮标志（Qt.WindowContextHelpButtonHint = 0x00000400）
_WINDOW_CONTEXT_HELP_HINT = 0x00000400


def remove_help_button(widget) -> None:
    """
    移除窗口标题栏的问号帮助按钮（Windows 上 QDialog 默认带）。

    Windows 下 QDialog 标题栏自带 "?" 图标，点击进入 What's This 模式，
    在某些场景下可能引发异常/闪退（§6 反馈）。统一移除该按钮，
    保留最小化/最大化/关闭等常规按钮。
    """
    flags = int(widget.windowFlags())
    if flags & _WINDOW_CONTEXT_HELP_HINT:
        widget.setWindowFlags(widget.windowFlags() & ~_WINDOW_CONTEXT_HELP_HINT)


def setup_dialog(dialog) -> None:
    """
    统一初始化对话框：应用深色主题 + 移除问号帮助按钮。
    所有 QDialog 创建后调用，保证行为一致。
    """
    from PyQt5.QtWidgets import QApplication
    remove_help_button(dialog)
    if QApplication.instance():
        dialog.setStyleSheet(DARK_QSS)
