# -*- coding: utf-8 -*-
"""
ThemeTypography —— 统一字体系统（v5.2 Phase 3-9 / RC-7A Token Wiring）。

基础值来自 common/theme_tokens.py（单一来源）。
保持现有 API（TT.TITLE_LARGE / TT.css()）不变。
"""
import common.theme_tokens as ThemeTokens


class ThemeTypography:
    """字体常量。"""

    FONT_FAMILY = ThemeTokens.FONT_FAMILY

    TITLE_LARGE = {"size": int(ThemeTokens.FONT_SIZE_TITLE_LG.replace("px", "")), "weight": "bold"}
    TITLE_MEDIUM = {"size": int(ThemeTokens.FONT_SIZE_TITLE_MD.replace("px", "")), "weight": "bold"}
    TITLE_SMALL = {"size": int(ThemeTokens.FONT_SIZE_TITLE_SM.replace("px", "")), "weight": "bold"}

    BODY = {"size": int(ThemeTokens.FONT_SIZE_BODY.replace("px", "")), "weight": "normal"}
    BODY_SMALL = {"size": int(ThemeTokens.FONT_SIZE_BODY_SM.replace("px", "")), "weight": "normal"}

    CAPTION = {"size": int(ThemeTokens.FONT_SIZE_CAPTION.replace("px", "")), "weight": "normal"}

    NUMERIC_LARGE = {"size": int(ThemeTokens.FONT_SIZE_NUMERIC_LG.replace("px", "")), "weight": "bold"}
    NUMERIC_MEDIUM = {"size": int(ThemeTokens.FONT_SIZE_NUMERIC_MD.replace("px", "")), "weight": "bold"}

    @staticmethod
    def css(typedef: dict) -> str:
        """转换为 CSS 字符串。"""
        parts = [f"font-family: {ThemeTypography.FONT_FAMILY};"]
        if "size" in typedef:
            parts.append(f"font-size: {typedef['size']}px;")
        if typedef.get("weight") == "bold":
            parts.append("font-weight: bold;")
        return " ".join(parts)
