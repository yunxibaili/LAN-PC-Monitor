# -*- coding: utf-8 -*-
"""
common/theme_tokens.py —— 共享设计令牌（v5.4 Gentelella 对齐）。

基于 Gentelella v4 暗色模式（https://github.com/ColorlibHQ/gentelella）。
供 host/gui/theme 和 agent/gui/theme 共同引用。
"""
# ---- 颜色令牌（Gentelella Dark Mode 对齐） ----
COLOR_BG_DARK = "#0f1623"         # body-bg
COLOR_BG_SURFACE = "#1a2332"      # surface（卡片/侧栏）
COLOR_BG_CARD = "#1e2a3a"         # 卡片背景（略亮于 surface）
COLOR_TEXT_PRIMARY = "#e6ebf2"    # text
COLOR_TEXT_SECONDARY = "#b3bccb"  # text-secondary
COLOR_TEXT_DISABLED = "#5a6473"   # text-disabled
COLOR_ACCENT = "#1ABB9C"          # primary（Gentelella teal）
COLOR_SUCCESS = "#2fb344"         # green
COLOR_WARNING = "#f59f00"         # yellow
COLOR_DANGER = "#d63939"          # red
COLOR_INFO = "#4299e1"            # azure
COLOR_BORDER = "rgba(255,255,255,0.08)"  # border-color dark

# ---- 间距令牌 (px) ----
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24
SPACING_XXL = 32

# ---- 字体令牌 ----
FONT_FAMILY = "'Inter', 'Microsoft YaHei', 'Segoe UI', sans-serif"
FONT_SIZE_TITLE_LG = "24px"
FONT_SIZE_TITLE_MD = "20px"
FONT_SIZE_TITLE_SM = "16px"
FONT_SIZE_BODY = "14px"
FONT_SIZE_BODY_SM = "12px"
FONT_SIZE_CAPTION = "11px"
FONT_SIZE_NUMERIC_LG = "32px"
FONT_SIZE_NUMERIC_MD = "20px"

# ---- 圆角令牌 (px) ----
RADIUS_CARD = 6
RADIUS_BUTTON = 6
RADIUS_BADGE = 6
