# -*- coding: utf-8 -*-
"""v5.2 UI 主题模块（Phase 4-1B Design System）。"""
from host.gui.theme.colors import ThemeColors
from host.gui.theme.metrics import ThemeMetrics
from host.gui.theme.spacing import ThemeSpacing
from host.gui.theme.layout import ThemeLayout
from host.gui.theme.animation import ThemeAnimation
from host.gui.theme.typography import ThemeTypography
from host.gui.theme.components import remove_help_button
from host.gui.theme.icons import ThemeIcons
from host.gui.theme.style import dark_qss

# 便捷函数（兼容旧代码 common.theme 风格调用）
COLOR_TEXT = ThemeColors.TEXT_PRIMARY
COLOR_NA = ThemeColors.TEXT_DISABLED
COLOR_NORMAL = ThemeColors.STATUS_ONLINE
COLOR_WARN = ThemeColors.STATUS_WARNING
COLOR_DANGER = ThemeColors.STATUS_ERROR
COLOR_ACCENT = ThemeColors.ACCENT_PRIMARY


def usage_color(value):
    return ThemeColors.usage_color(value)


def temp_color(value):
    return ThemeColors.temp_color(value)


def score_color(value):
    return ThemeColors.score_color(value)


def rtt_color(value):
    return ThemeColors.rtt_color(value)


def apply_color(label, color):
    label.setStyleSheet(f"color: {color}; background: transparent;")


__all__ = [
    "ThemeColors", "ThemeMetrics", "ThemeSpacing", "ThemeLayout", "ThemeAnimation",
    "ThemeTypography", "ThemeIcons", "dark_qss", "remove_help_button",
    "COLOR_TEXT", "COLOR_NA", "COLOR_NORMAL", "COLOR_WARN", "COLOR_DANGER", "COLOR_ACCENT",
    "usage_color", "temp_color", "score_color", "rtt_color", "apply_color",
]
