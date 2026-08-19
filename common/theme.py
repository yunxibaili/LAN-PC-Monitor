# -*- coding: utf-8 -*-
"""
Theme System — Agent GUI 主题（v5.3.4 统一到 theme_tokens）。

所有颜色来自 common/theme_tokens.py（单一来源），与 Host GUI 色板一致。
Agent 侧不再维护独立色板。
"""
import common.theme_tokens as _T
from PyQt5.QtWidgets import QLabel

# ---------- 颜色：全部来自 theme_tokens ----------
COLOR_BG = _T.COLOR_BG_DARK
COLOR_TEXT = _T.COLOR_TEXT_PRIMARY
COLOR_NORMAL = _T.COLOR_SUCCESS
COLOR_WARN = _T.COLOR_WARNING
COLOR_DANGER = _T.COLOR_DANGER
COLOR_NA = _T.COLOR_TEXT_DISABLED
COLOR_ACCENT = _T.COLOR_ACCENT
COLOR_HIGHLIGHT = _T.COLOR_BG_CARD

# ---------- 阈值（与 ThemeColors 一致） ----------
USAGE_WARN, USAGE_DANGER = 80, 95
RAM_WARN, RAM_DANGER = 80, 90
TEMP_WARN, TEMP_DANGER = 80, 85
HOTSPOT_WARN, HOTSPOT_DANGER = 95, 105
DISK_WARN, DISK_DANGER = 85, 95
SCORE_WARN = 60
RTT_WARN, RTT_DANGER = 5, 20

# ---------- QSS 亮色主题（与 Host 一致） ----------
_BORDER = _T.COLOR_BORDER
_SURFACE = _T.COLOR_BG_SURFACE
_ELEVATED = _T.COLOR_BG_CARD

DARK_QSS = f"""
    * {{ font-family: {_T.FONT_FAMILY}; }}
    QMainWindow, QDialog, QWidget {{ background-color: {COLOR_BG}; color: {COLOR_TEXT}; }}
    QLabel {{ background: transparent; color: {COLOR_TEXT}; }}
    QLabel#panel_title {{
        color: {COLOR_ACCENT}; font-weight: bold; font-size: 14px;
        border-bottom: 1px solid {_BORDER}; padding-bottom: 4px;
    }}
    QGroupBox {{
        border: 1px solid {_BORDER}; border-radius: 4px; margin-top: 8px;
        color: {COLOR_TEXT};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {COLOR_ACCENT};
    }}
    QListWidget, QPlainTextEdit {{ background-color: {_SURFACE}; border: 1px solid {_BORDER}; }}
    QPushButton {{ background-color: {_ELEVATED}; color: {COLOR_TEXT}; border: 1px solid {_BORDER}; padding: 6px 12px; border-radius: 3px; }}
    QPushButton:hover {{ background-color: #E5E7EB; }}
    QPushButton:pressed {{ background-color: {COLOR_BG}; }}
    QScrollBar:vertical {{ background: {_SURFACE}; width: 10px; }}
    QScrollBar::handle:vertical {{ background: {_BORDER}; min-height: 24px; border-radius: 5px; }}
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


# 问号帮助按钮标志
_WINDOW_CONTEXT_HELP_HINT = 0x00000400


def remove_help_button(widget) -> None:
    """移除窗口标题栏的问号帮助按钮。"""
    flags = int(widget.windowFlags())
    if flags & _WINDOW_CONTEXT_HELP_HINT:
        widget.setWindowFlags(widget.windowFlags() & ~_WINDOW_CONTEXT_HELP_HINT)


def setup_dialog(dialog) -> None:
    """统一初始化对话框：应用深色主题 + 移除问号帮助按钮。"""
    from PyQt5.QtWidgets import QApplication
    remove_help_button(dialog)
    if QApplication.instance():
        dialog.setStyleSheet(DARK_QSS)
