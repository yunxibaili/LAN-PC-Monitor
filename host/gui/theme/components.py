# -*- coding: utf-8 -*-
"""ThemeComponents —— 统一组件样式（v5.2 Phase 3-9）。"""


class CardStyle:
    RADIUS = 12
    PADDING_H = 16
    PADDING_V = 12
    BG = "#1C2333"
    BORDER = "#21262D"
    HOVER_BORDER = "#3B82F6"


class ButtonStyle:
    RADIUS = 6
    HEIGHT = 36
    BG = "#1E293B"
    BG_HOVER = "#253049"
    BG_PRESSED = "#0F1117"
    BORDER = "#21262D"
    BORDER_HOVER = "#3B82F6"
    FONT_SIZE = 14


class InputStyle:
    RADIUS = 6
    HEIGHT = 36
    BG = "#0D1117"
    BORDER = "#21262D"
    BORDER_FOCUS = "#3B82F6"
    FONT_SIZE = 14


class TableStyle:
    HEADER_BG = "#161B22"
    ROW_ALT = "#141920"
    ROW_HOVER = "#1C2333"
    BORDER = "#21262D"
    ROW_HEIGHT = 38
    FONT_SIZE = 13


class BadgeStyle:
    RADIUS = 12
    PADDING_H = 8
    PADDING_V = 4
    FONT_SIZE = 11
    ONLINE_BG = "#22C55E"
    OFFLINE_BG = "#EF4444"
    WARNING_BG = "#F59E0B"
    INFO_BG = "#60A5FA"


# 问号帮助按钮标志（Qt.WindowContextHelpButtonHint = 0x00000400）
_WINDOW_CONTEXT_HELP_HINT = 0x00000400


def remove_help_button(widget) -> None:
    """
    移除窗口标题栏的问号帮助按钮（Windows 上 QDialog 默认带）。
    """
    flags = int(widget.windowFlags())
    if flags & _WINDOW_CONTEXT_HELP_HINT:
        widget.setWindowFlags(widget.windowFlags() & ~_WINDOW_CONTEXT_HELP_HINT)
