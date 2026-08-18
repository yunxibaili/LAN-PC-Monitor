# -*- coding: utf-8 -*-
"""
ThemeColors —— 统一颜色系统（v5.4 Gentelella 对齐）。

基础 token 来自 common/theme_tokens.py（Gentelella Dark Mode）。
语义 token 保留本文件（Host UI 专用）。
"""
import common.theme_tokens as ThemeTokens


class ThemeColors:
    """颜色常量。所有 GUI 颜色从此处引用。"""

    # ---- 基础 token：来自 common/theme_tokens.py（Gentelella Dark） ----
    BACKGROUND_PRIMARY = ThemeTokens.COLOR_BG_DARK       # #0f1623
    BACKGROUND_SECONDARY = ThemeTokens.COLOR_BG_SURFACE   # #1a2332
    BACKGROUND_CARD = ThemeTokens.COLOR_BG_CARD           # #1e2a3a

    TEXT_PRIMARY = ThemeTokens.COLOR_TEXT_PRIMARY          # #e6ebf2
    TEXT_SECONDARY = ThemeTokens.COLOR_TEXT_SECONDARY      # #b3bccb
    TEXT_DISABLED = ThemeTokens.COLOR_TEXT_DISABLED        # #5a6473

    ACCENT_PRIMARY = ThemeTokens.COLOR_ACCENT             # #1ABB9C (teal)

    STATUS_ONLINE = ThemeTokens.COLOR_SUCCESS             # #2fb344
    STATUS_OFFLINE = ThemeTokens.COLOR_DANGER             # #d63939
    STATUS_WARNING = ThemeTokens.COLOR_WARNING            # #f59f00
    STATUS_ERROR = ThemeTokens.COLOR_DANGER               # #d63939

    ALERT_INFO = ThemeTokens.COLOR_INFO                   # #4299e1
    ALERT_WARN = ThemeTokens.COLOR_WARNING                # #f59f00
    ALERT_DANGER = ThemeTokens.COLOR_DANGER               # #d63939

    BORDER_DEFAULT = ThemeTokens.COLOR_BORDER             # rgba(255,255,255,0.08)

    # ---- 语义 token：Host UI 专用 ----
    BACKGROUND_ELEVATED = "#22303f"
    BACKGROUND_HOVER = "rgba(255,255,255,0.04)"
    BACKGROUND_INPUT = "#141d2b"

    TEXT_INVERSE = "#0f1623"
    TEXT_ON_COLOR = "#ffffff"

    BORDER_FOCUS = "#1ABB9C"
    BORDER_SUBTLE = "rgba(255,255,255,0.05)"

    CHART_PRIMARY = "#1ABB9C"
    CHART_SECONDARY = "#f59f00"
    CHART_GREEN = "#2fb344"
    CHART_RED = "#d63939"
    CHART_PURPLE = "#ae3ec9"
    CHART_CYAN = "#17a2b8"
    CHART_AREA = "rgba(26,187,156,0.12)"
    CHART_GRID = "rgba(255,255,255,0.05)"
    CHART_THRESHOLD_WARN = "#f59f00"
    CHART_THRESHOLD_DANGER = "#d63939"

    BAR_BG = "rgba(255,255,255,0.06)"
    BAR_SUCCESS = "#2fb344"
    BAR_WARNING = "#f59f00"
    BAR_DANGER = "#d63939"

    TABLE_HEADER_BG = "#141d2b"
    TABLE_ALT_ROW = "#1a2332"
    TABLE_GRID = "rgba(255,255,255,0.06)"
    TABLE_HOVER = "#22303f"

    # ---- 别名（向后兼容） ----
    BG_BASE = BACKGROUND_PRIMARY
    BG_SURFACE = BACKGROUND_SECONDARY
    BG_CARD = BACKGROUND_CARD
    BG_ELEVATED = BACKGROUND_ELEVATED
    BG_HOVER = BACKGROUND_HOVER
    BG_INPUT = BACKGROUND_INPUT
    COLOR_TEXT = TEXT_PRIMARY
    COLOR_NORMAL = STATUS_ONLINE
    COLOR_WARN = STATUS_WARNING
    COLOR_DANGER = STATUS_ERROR
    COLOR_NA = TEXT_DISABLED
    COLOR_ACCENT = ACCENT_PRIMARY
    COLOR_HIGHLIGHT = BACKGROUND_CARD
    CHART_BG = BACKGROUND_SECONDARY

    SUCCESS = STATUS_ONLINE
    WARNING = STATUS_WARNING
    DANGER = STATUS_ERROR
    PRIMARY = ACCENT_PRIMARY
    TEXT_MUTED = TEXT_DISABLED

    @classmethod
    def status_color(cls, status):
        m = {"connected": cls.STATUS_ONLINE, "online": cls.STATUS_ONLINE,
             "connecting": cls.STATUS_WARNING, "reconnecting": cls.STATUS_WARNING,
             "timeout": cls.STATUS_WARNING, "offline": cls.STATUS_OFFLINE,
             "auth_failed": cls.STATUS_ERROR}
        return m.get(status, cls.TEXT_DISABLED)

    @classmethod
    def alert_color(cls, level):
        return {"red": cls.ALERT_DANGER, "warn": cls.ALERT_WARN}.get(level, cls.TEXT_DISABLED)

    @classmethod
    def bar_color(cls, value, warn=80, danger=95):
        if value >= danger:
            return cls.BAR_DANGER
        if value >= warn:
            return cls.BAR_WARNING
        return cls.BAR_SUCCESS

    @classmethod
    def score_color(cls, score):
        if score is None or score == "N/A":
            return cls.TEXT_DISABLED
        if score < 60:
            return cls.STATUS_ERROR
        if score < 80:
            return cls.STATUS_WARNING
        return cls.STATUS_ONLINE

    @classmethod
    def temp_color(cls, temp):
        if temp is None or temp == "N/A":
            return cls.TEXT_DISABLED
        if temp > 85:
            return cls.STATUS_ERROR
        if temp > 80:
            return cls.STATUS_WARNING
        return cls.STATUS_ONLINE

    @classmethod
    def usage_color(cls, val):
        if val is None or val == "N/A":
            return cls.TEXT_DISABLED
        if val > 95:
            return cls.STATUS_ERROR
        if val > 80:
            return cls.STATUS_WARNING
        return cls.STATUS_ONLINE

    @classmethod
    def rtt_color(cls, value):
        if value is None or value == "N/A":
            return cls.TEXT_DISABLED
        try:
            value = float(value)
        except (TypeError, ValueError):
            return cls.TEXT_DISABLED
        if value < 5:
            return cls.STATUS_ONLINE
        if value < 20:
            return cls.STATUS_WARNING
        return cls.STATUS_ERROR
