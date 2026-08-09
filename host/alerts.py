# -*- coding: utf-8 -*-
"""
红线告警引擎 —— 自定义数值红线检测（见《README.md》第四篇）。

- AlertEngine：根据配置规则检测一帧数据中的指标是否越线。
- extract_path：按 'section.key' 或 'disk[0].key' 提取指标值。

告警等级：
    "red"  — 红色告警（超上限 red / 低于下限 red_min）
    "warn" — 橙色预警（超上限 warn / 低于下限 warn_min）
"""
import logging

log = logging.getLogger("host.alerts")


def extract_path(frame: dict, path: str):
    """
    按 'section.key' 或 'disk[0].key' 提取指标值。

    :param frame: monitor_data 数据帧
    :param path:  指标路径，如 'cpu.total_usage'、'disk[0].usage_percent'
    :return: 指标值；无法提取返回 None
    """
    # 处理数组索引 disk[0].usage_percent
    if "[" in path:
        try:
            head, rest = path.split("]", 1)
            section = head.split("[")[0]
            idx = int(head.split("[")[1])
            sub = rest.lstrip(".")
            return frame[section][idx].get(sub)
        except (KeyError, IndexError, TypeError, ValueError):
            return None
    section, _, key = path.partition(".")
    try:
        return frame.get(section, {}).get(key)
    except (AttributeError, TypeError):
        return None


class AlertEngine:
    """红线告警引擎：根据配置规则检测指标是否越线。"""

    def __init__(self, rules):
        """
        :param rules: 规则列表，每项 dict：
            {path, name, red?, warn?, red_min?, warn_min?}
            至少包含 red/warn 之一或 red_min/warn_min 之一。
        """
        self.rules = rules or []

    def check(self, frame: dict) -> list:
        """
        对一帧数据检测所有规则，返回告警列表。

        :param frame: monitor_data 数据帧
        :return: [{"name","path","value","level","threshold"}, ...]
                 level: "red" / "warn"
        """
        alerts = []
        for rule in self.rules:
            path = rule.get("path", "")
            value = extract_path(frame, path)
            if value in (None, "N/A", ""):
                continue
            level = self._judge(rule, value)
            if level:
                alerts.append({
                    "name": rule.get("name", path.rsplit(".", 1)[-1]),
                    "path": path,
                    "value": value,
                    "level": level,
                    "threshold": rule.get("red") or rule.get("red_min")
                                 or rule.get("warn") or rule.get("warn_min"),
                })
        return alerts

    def _judge(self, rule: dict, value) -> str | None:
        """判定单条规则：返回 "red"/"warn"/None。"""
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None
        # 上限
        if rule.get("red") is not None and v > rule["red"]:
            return "red"
        if rule.get("warn") is not None and v > rule["warn"]:
            return "warn"
        # 下限
        if rule.get("red_min") is not None and v < rule["red_min"]:
            return "red"
        if rule.get("warn_min") is not None and v < rule["warn_min"]:
            return "warn"
        return None
