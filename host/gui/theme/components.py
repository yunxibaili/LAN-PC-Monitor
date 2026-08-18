# -*- coding: utf-8 -*-
"""ThemeComponents —— 通用组件工具（v5.4 清理）。"""

# 问号帮助按钮标志（Qt.WindowContextHelpButtonHint = 0x00000400）
_WINDOW_CONTEXT_HELP_HINT = 0x00000400


def remove_help_button(widget) -> None:
    """移除窗口标题栏的问号帮助按钮。"""
    flags = int(widget.windowFlags())
    if flags & _WINDOW_CONTEXT_HELP_HINT:
        widget.setWindowFlags(widget.windowFlags() & ~_WINDOW_CONTEXT_HELP_HINT)
