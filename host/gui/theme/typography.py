# -*- coding: utf-8 -*-
"""ThemeTypography —— 统一字体系统（v5.2 Phase 3-9）。"""


class ThemeTypography:
    """字体常量。"""

    FONT_FAMILY = "'Microsoft YaHei', 'Segoe UI', sans-serif"

    TITLE_LARGE = {"size": 24, "weight": "bold"}
    TITLE_MEDIUM = {"size": 20, "weight": "bold"}
    TITLE_SMALL = {"size": 16, "weight": "bold"}

    BODY = {"size": 14, "weight": "normal"}
    BODY_SMALL = {"size": 12, "weight": "normal"}

    CAPTION = {"size": 11, "weight": "normal"}

    NUMERIC_LARGE = {"size": 32, "weight": "bold"}
    NUMERIC_MEDIUM = {"size": 20, "weight": "bold"}

    @staticmethod
    def css(typedef: dict) -> str:
        """转换为 CSS 字符串。"""
        parts = [f"font-family: {ThemeTypography.FONT_FAMILY};"]
        if "size" in typedef:
            parts.append(f"font-size: {typedef['size']}px;")
        if typedef.get("weight") == "bold":
            parts.append("font-weight: bold;")
        return " ".join(parts)
