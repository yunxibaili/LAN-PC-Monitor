# -*- coding: utf-8 -*-
"""
common/theme_tokens.py —— 共享设计令牌（v5.2 RC-6）。

仅定义基础颜色/间距/字体令牌常量，不包含 QSS 或函数。
供 host/gui/theme 和 agent/gui/theme 共同引用。

结构：
    common/theme_tokens
         |
    -----------------
    |               |
  Host UI        Agent UI
  (gui/theme)    (gui/theme)

注意：common 不依赖 host 或 agent。令牌定义为纯常量。
"""
# ---- 颜色令牌 ----
COLOR_BG_DARK = "#0F1117"
COLOR_BG_SURFACE = "#161B22"
COLOR_BG_CARD = "#1C2333"
COLOR_TEXT_PRIMARY = "#E6EDF3"
COLOR_TEXT_SECONDARY = "#8B949E"
COLOR_TEXT_DISABLED = "#484F58"
COLOR_ACCENT = "#3B82F6"
COLOR_SUCCESS = "#22C55E"
COLOR_WARNING = "#F59E0B"
COLOR_DANGER = "#EF4444"
COLOR_INFO = "#60A5FA"
COLOR_BORDER = "#21262D"

# ---- 间距令牌 (px) ----
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24
SPACING_XXL = 32

# ---- 字体令牌 ----
FONT_FAMILY = "'Microsoft YaHei', 'Segoe UI', Consolas, sans-serif"
FONT_SIZE_TITLE_LG = "24px"
FONT_SIZE_TITLE_MD = "20px"
FONT_SIZE_TITLE_SM = "16px"
FONT_SIZE_BODY = "14px"
FONT_SIZE_BODY_SM = "12px"
FONT_SIZE_CAPTION = "11px"
FONT_SIZE_NUMERIC_LG = "32px"
FONT_SIZE_NUMERIC_MD = "20px"

# ---- 圆角令牌 (px) ----
RADIUS_CARD = 12
RADIUS_BUTTON = 6
RADIUS_BADGE = 12
