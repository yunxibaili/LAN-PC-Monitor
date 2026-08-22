# -*- coding: utf-8 -*-
"""
common/version.py —— 应用版本单一来源（v5.4 版本漂移治理）。

设计：所有对外展示/上报的"应用版本"统一从此处读取，杜绝多处硬编码漂移。
历史漂移：health 曾返回 5.0.0、v5.2.3 / v5.3.3 / v5.3.4 并存（DESIGN 误写 v5.4）。

注意：discovery 的 version="5.0" 是**协议版本**（广播协议字段），与 APP_VERSION 不同，故不并入本常量。
"""

# 应用版本（对外展示 / REST health / UI 显示）
APP_VERSION = "5.3.4"

# 版本显示串（带 'v' 前缀，供 UI label 使用）
VERSION_LABEL = f"v{APP_VERSION}"
