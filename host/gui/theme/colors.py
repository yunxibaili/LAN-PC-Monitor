# -*- coding: utf-8 -*-
"""ThemeColors —— 统一颜色系统（v5.2 Phase 3-9）。"""
from host.store.signals import Signal


class ThemeColors:
    """颜色常量。所有 GUI 颜色从此处引用。"""

    # ---- 背景 ----
    BACKGROUND_PRIMARY = "#0F1117"
    BACKGROUND_SECONDARY = "#161B22"
    BACKGROUND_CARD = "#1C2333"
    BACKGROUND_ELEVATED = "#1E293B"
    BACKGROUND_HOVER = "#253049"
    BACKGROUND_INPUT = "#0D1117"

    # ---- 文字 ----
    TEXT_PRIMARY = "#E6EDF3"
    TEXT_SECONDARY = "#8B949E"
    TEXT_DISABLED = "#484F58"
    TEXT_INVERSE = "#0F1117"
    TEXT_ON_COLOR = "#FFFFFF"

    # ---- 强调色 ----
    ACCENT_PRIMARY = "#3B82F6"

    # ---- 状态色 ----
    STATUS_ONLINE = "#22C55E"
    STATUS_OFFLINE = "#EF4444"
    STATUS_WARNING = "#F59E0B"
    STATUS_ERROR = "#EF4444"

    # ---- 告警色 ----
    ALERT_INFO = "#60A5FA"
    ALERT_WARN = "#F59E0B"
    ALERT_DANGER = "#EF4444"

    # ---- 边框 ----
    BORDER_DEFAULT = "#21262D"
    BORDER_FOCUS = "#3B82F6"
    BORDER_SUBTLE = "#30363D"

    # ---- 图表 ----
    CHART_PRIMARY = "#3B82F6"
    CHART_SECONDARY = "#F59E0B"
    CHART_AREA = "rgba(59,130,246,0.12)"
    CHART_GRID = "#21262D"
    CHART_THRESHOLD_WARN = "#F59E0B"
    CHART_THRESHOLD_DANGER = "#EF4444"

    # ---- 进度条 ----
    BAR_BG = "#21262D"
    BAR_SUCCESS = "#22C55E"
    BAR_WARNING = "#F59E0B"
    BAR_DANGER = "#EF4444"

    # ---- 表格 ----
    TABLE_HEADER_BG = "#161B22"
    TABLE_ALT_ROW = "#141920"
    TABLE_GRID = "#21262D"
    TABLE_HOVER = "#1C2333"

    # ---- 别名（向后兼容，逐步淘汰） ----
    BG_BASE = "#0F1117"
    BG_SURFACE = "#161B22"
    BG_CARD = "#1C2333"
    BG_ELEVATED = "#1E293B"
    BG_HOVER = "#253049"
    BG_INPUT = "#0D1117"
    COLOR_TEXT = "#E6EDF3"
    COLOR_NORMAL = "#22C55E"
    COLOR_WARN = "#F59E0B"
    COLOR_DANGER = "#EF4444"
    COLOR_NA = "#484F58"
    COLOR_ACCENT = "#3B82F6"
    COLOR_HIGHLIGHT = "#1C2333"
    CHART_BG = "#161B22"

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
