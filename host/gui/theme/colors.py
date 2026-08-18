# -*- coding: utf-8 -*-
"""
ThemeColors —— 统一颜色系统（v5.2 Phase 3-9 / RC-7A Token Wiring）。

基础 token 来自 common/theme_tokens.py（单一来源）。
语义 token 保留本文件（Host UI 专用）。
"""
import common.theme_tokens as ThemeTokens


class ThemeColors:
    """颜色常量。所有 GUI 颜色从此处引用。"""

    # ---- 基础 token：来自 common/theme_tokens.py ----
    BACKGROUND_PRIMARY = ThemeTokens.COLOR_BG_DARK
    BACKGROUND_SECONDARY = ThemeTokens.COLOR_BG_SURFACE
    BACKGROUND_CARD = ThemeTokens.COLOR_BG_CARD

    TEXT_PRIMARY = ThemeTokens.COLOR_TEXT_PRIMARY
    TEXT_SECONDARY = ThemeTokens.COLOR_TEXT_SECONDARY
    TEXT_DISABLED = ThemeTokens.COLOR_TEXT_DISABLED

    ACCENT_PRIMARY = ThemeTokens.COLOR_ACCENT

    STATUS_ONLINE = ThemeTokens.COLOR_SUCCESS
    STATUS_OFFLINE = ThemeTokens.COLOR_DANGER
    STATUS_WARNING = ThemeTokens.COLOR_WARNING
    STATUS_ERROR = ThemeTokens.COLOR_DANGER

    ALERT_INFO = ThemeTokens.COLOR_INFO
    ALERT_WARN = ThemeTokens.COLOR_WARNING
    ALERT_DANGER = ThemeTokens.COLOR_DANGER

    BORDER_DEFAULT = ThemeTokens.COLOR_BORDER

    # ---- 语义 token：Host UI 专用（保留，不来自 theme_tokens） ----
    BACKGROUND_ELEVATED = "#1E293B"
    BACKGROUND_HOVER = "#253049"
    BACKGROUND_INPUT = "#0D1117"

    TEXT_INVERSE = "#0F1117"
    TEXT_ON_COLOR = "#FFFFFF"

    BORDER_FOCUS = "#3B82F6"
    BORDER_SUBTLE = "#30363D"

    CHART_PRIMARY = "#3B82F6"
    CHART_SECONDARY = "#F59E0B"
    CHART_GREEN = "#22C55E"
    CHART_RED = "#EF4444"
    CHART_PURPLE = "#A855F7"
    CHART_CYAN = "#06B6D4"
    CHART_AREA = "rgba(59,130,246,0.12)"
    CHART_GRID = "#21262D"
    CHART_THRESHOLD_WARN = "#F59E0B"
    CHART_THRESHOLD_DANGER = "#EF4444"

    BAR_BG = "#21262D"
    BAR_SUCCESS = "#22C55E"
    BAR_WARNING = "#F59E0B"
    BAR_DANGER = "#EF4444"

    TABLE_HEADER_BG = "#161B22"
    TABLE_ALT_ROW = "#141920"
    TABLE_GRID = "#21262D"
    TABLE_HOVER = "#1C2333"

    # ---- 别名（向后兼容，逐步淘汰） ----
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

    # ---- 向后兼容别名（测试/旧代码使用） ----
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
        if value >= danger: return cls.BAR_DANGER
        elif value >= warn: return cls.BAR_WARNING
        return cls.BAR_SUCCESS

    @classmethod
    def score_color(cls, score):
        if score is None or score == "N/A": return cls.TEXT_DISABLED
        if score < 60: return cls.STATUS_ERROR
        if score < 80: return cls.STATUS_WARNING
        return cls.STATUS_ONLINE

    @classmethod
    def temp_color(cls, temp):
        if temp is None or temp == "N/A": return cls.TEXT_DISABLED
        if temp > 85: return cls.STATUS_ERROR
        if temp > 80: return cls.STATUS_WARNING
        return cls.STATUS_ONLINE

    @classmethod
    def usage_color(cls, val):
        if val is None or val == "N/A": return cls.TEXT_DISABLED
        if val > 95: return cls.STATUS_ERROR
        if val > 80: return cls.STATUS_WARNING
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
