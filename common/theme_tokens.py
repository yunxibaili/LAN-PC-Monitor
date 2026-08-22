# -*- coding: utf-8 -*-
"""
common/theme_tokens.py —— 白色高密度监控主题令牌（v5.5 重设计）。

风格：白色卡片 + 浅灰背景 + 深色侧栏（专业监控控制台，清晰高对比）。
来源：白色版网页原型 + Apple/Emil 设计原则（半透明阴影、克制动效、材质层次）。
设计要点：
  - 浅灰蓝背景 + 纯白卡片 + 细灰边框 + 半透明柔影（不用实线硬边框）
  - 高对比状态色（在线绿/警告橙/危险红/信息蓝）
  - 图表色高区分度，保证浅色背景可读性
"""
# ---- 背景 ----
COLOR_BG_DARK = "#F5F7FB"          # 窗口底色（浅灰蓝）
COLOR_BG_SURFACE = "#F9FAFB"        # 表面容器（表头/输入底）
COLOR_BG_CARD = "#FFFFFF"           # 卡片背景（纯白）

# ---- 文字 ----
COLOR_TEXT_PRIMARY = "#1E2633"      # 主文字
COLOR_TEXT_SECONDARY = "#626D7D"    # 次要文字
COLOR_TEXT_DISABLED = "#9CA3AF"     # 禁用/说明文字

# ---- 语义色 ----
COLOR_ACCENT = "#3B82F6"            # 信息/选中（蓝）
COLOR_ACCENT_DK = "#2563EB"         # accent 深
COLOR_SUCCESS = "#2FB344"           # 在线/正常（绿）
COLOR_WARNING = "#F59F00"           # 警告（橙）
COLOR_DANGER = "#D63939"            # 危险/离线（红）
COLOR_INFO = "#0EA5E9"              # 信息（亮蓝）
COLOR_BORDER = "#E6E7EB"            # 卡片边框（细灰）
COLOR_OFFLINE = "#9CA3AF"           # 离线

# ---- Sidebar（深色侧栏，白底对比）----
SIDEBAR_BG = "#1A2332"              # 侧栏深色
SIDEBAR_TEXT = "#B3BCCB"            # 侧栏文字
SIDEBAR_TEXT_HOVER = "#CBD5E1"      # hover 文字
SIDEBAR_TEXT_ACTIVE = "#FFFFFF"     # 激活文字
SIDEBAR_TEXT_MUTED = "#7B8FA3"      # 分组标题/次要
SIDEBAR_BORDER = "rgba(255,255,255,0.06)"
SIDEBAR_HOVER = "rgba(255,255,255,0.05)"
SIDEBAR_ACTIVE_BG = "rgba(59,130,246,0.16)"

# ---- 间距 (4px base) ----
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24
SPACING_XXL = 32

# ---- 字体 ----
FONT_FAMILY = "'Segoe UI', 'Inter', 'Microsoft YaHei', sans-serif"
FONT_SIZE_TITLE_LG = "24px"
FONT_SIZE_TITLE_MD = "20px"
FONT_SIZE_TITLE_SM = "16px"
FONT_SIZE_BODY = "14px"
FONT_SIZE_BODY_SM = "12px"
FONT_SIZE_CAPTION = "11px"
FONT_SIZE_NUMERIC_LG = "32px"
FONT_SIZE_NUMERIC_MD = "20px"

# ---- 圆角 ----
RADIUS_CARD = 12
RADIUS_BUTTON = 8
RADIUS_BADGE = 8
