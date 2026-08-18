# -*- coding: utf-8 -*-
"""
common/theme_tokens.py —— 共享设计令牌（v5.4 亮色模式 Professional Monitoring Console）。

基于 Gentelella v4 / Grafana / Windows Fluent 设计原则提取。
供 host/gui/theme 和 agent/gui/theme 共同引用。
"""
# ---- 颜色令牌（亮色模式） ----
COLOR_BG_DARK = "#FFFFFF"           # 主背景（白色）
COLOR_BG_SURFACE = "#F9FAFB"       # 表面容器（卡片/侧栏）
COLOR_BG_CARD = "#F3F4F6"          # 卡片背景
COLOR_TEXT_PRIMARY = "#111827"      # 主要文字
COLOR_TEXT_SECONDARY = "#6B7280"    # 次要文字
COLOR_TEXT_DISABLED = "#9CA3AF"     # 禁用
COLOR_ACCENT = "#3B82F6"           # 信息/选中/强调
COLOR_SUCCESS = "#22C55E"          # 正常/在线
COLOR_WARNING = "#EAB308"          # 警告
COLOR_DANGER = "#EF4444"           # 危险/离线
COLOR_INFO = "#3B82F6"             # 信息
COLOR_BORDER = "#E5E7EB"           # 边框
COLOR_OFFLINE = "#6B7280"          # 离线/灰色

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
RADIUS_CARD = 8
RADIUS_BUTTON = 6
RADIUS_BADGE = 6
