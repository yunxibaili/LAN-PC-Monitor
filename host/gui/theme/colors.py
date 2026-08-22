# -*- coding: utf-8 -*-
"""
ThemeColors —— 统一颜色系统（v5.5 暗色玻璃拟态）。
"""
import common.theme_tokens as ThemeTokens


class ThemeColors:
    """颜色常量。所有 GUI 颜色从此处引用。"""

    # ---- 基础 token ----
    BACKGROUND_PRIMARY = ThemeTokens.COLOR_BG_DARK       # #0A0F1E
    BACKGROUND_SECONDARY = ThemeTokens.COLOR_BG_SURFACE   # #111827
    BACKGROUND_CARD = ThemeTokens.COLOR_BG_CARD           # #141B2E

    TEXT_PRIMARY = ThemeTokens.COLOR_TEXT_PRIMARY          # #F8FAFC
    TEXT_SECONDARY = ThemeTokens.COLOR_TEXT_SECONDARY      # #94A3B8
    TEXT_DISABLED = ThemeTokens.COLOR_TEXT_DISABLED        # #64748B

    ACCENT_PRIMARY = ThemeTokens.COLOR_ACCENT             # #3B82F6
    ACCENT_DK = ThemeTokens.COLOR_ACCENT_DK               # #2563EB

    STATUS_ONLINE = ThemeTokens.COLOR_SUCCESS             # #22C55E
    STATUS_OFFLINE = ThemeTokens.COLOR_OFFLINE            # #475569
    STATUS_WARNING = ThemeTokens.COLOR_WARNING            # #F59F00
    STATUS_ERROR = ThemeTokens.COLOR_DANGER               # #EF4444

    ALERT_INFO = ThemeTokens.COLOR_INFO
    ALERT_WARN = ThemeTokens.COLOR_WARNING
    ALERT_DANGER = ThemeTokens.COLOR_DANGER

    BORDER_DEFAULT = ThemeTokens.COLOR_BORDER             # rgba(255,255,255,0.08)

    # ---- 语义 token（白色）----
    BACKGROUND_ELEVATED = "#FFFFFF"        # hover 升阶卡片
    BACKGROUND_HOVER = "#F5F7FB"           # hover 背景
    BACKGROUND_INPUT = "#F9FAFB"           # 输入框底

    TEXT_INVERSE = "#FFFFFF"               # 反色文字（用在深色块上）
    TEXT_ON_COLOR = "#FFFFFF"              # 状态色块上的文字

    BORDER_FOCUS = "#3B82F6"
    BORDER_SUBTLE = "#EFF0F3"

    # ---- 图表色（浅色背景高区分度）----
    CHART_PRIMARY = "#3B82F6"              # 蓝
    CHART_SECONDARY = "#AE3EC9"            # 紫
    CHART_GREEN = "#22C55E"                # 绿
    CHART_RED = "#D63939"                  # 红
    CHART_PURPLE = "#8B5CF6"               # 紫
    CHART_ORANGE = "#F76707"               # 橙
    CHART_CYAN = "#0891B2"                 # 青
    CHART_AREA = "rgba(59,130,246,0.08)"
    CHART_GRID = "rgba(30,38,51,0.06)"
    CHART_THRESHOLD_WARN = "#F59F00"
    CHART_THRESHOLD_DANGER = "#D63939"

    BAR_BG = "#E6E7EB"                # 进度条/环形背景（需能被 QColor 解析）
    BAR_SUCCESS = "#2FB344"
    BAR_WARNING = "#F59F00"
    BAR_DANGER = "#D63939"

    TABLE_HEADER_BG = "#F9FAFB"
    TABLE_ALT_ROW = "#F9FAFB"
    TABLE_GRID = "#E6E7EB"
    TABLE_HOVER = "#F5F7FB"

    # ---- 别名 ----
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

    # ---- Sidebar 暗色模式 ----
    SIDEBAR_BG = ThemeTokens.SIDEBAR_BG
    SIDEBAR_TEXT = ThemeTokens.SIDEBAR_TEXT
    SIDEBAR_TEXT_HOVER = ThemeTokens.SIDEBAR_TEXT_HOVER
    SIDEBAR_TEXT_ACTIVE = ThemeTokens.SIDEBAR_TEXT_ACTIVE
    SIDEBAR_TEXT_MUTED = ThemeTokens.SIDEBAR_TEXT_MUTED
    SIDEBAR_BORDER = ThemeTokens.SIDEBAR_BORDER
    SIDEBAR_HOVER = ThemeTokens.SIDEBAR_HOVER
    SIDEBAR_ACTIVE_BG = ThemeTokens.SIDEBAR_ACTIVE_BG

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
