# -*- coding: utf-8 -*-
"""
网络质量评分器 —— 滑动平均平滑抖动（见《技术文档.md》§9，v3.0 校准）。

评分公式（§9.1，延迟扣分系数 v3.0 校准为 *15）：
    延迟扣分 = max(0, (rtt_ms - 5) / 10) * 15     # 5ms 起算，每增 10ms 扣 15 分
    丢包扣分 = packet_loss_percent * 10           # 每 1% 丢包扣 10 分
    瞬时分   = max(0, round(100 - 延迟扣分 - 丢包扣分))

瞬时分校验（§9.1，应与等级一致）：
    RTT 1ms  → 100 优秀 ✅
    RTT 15ms → 85  良好 ✅
    RTT 30ms→53  一般 ✅
    RTT 5ms+8%丢包 → 20 较差 ✅

滑动平均（§9.2）：最近 N 次瞬时分均值，平滑无线网络抖动。
单测评估各档等级时用独立新建 scorer（避免前序样本污染均值）。

等级（§9.3）：
    ≥90 优秀（绿） | 70~89 良好（青绿） | 50~69 一般（橙） | <50 较差（红）
"""
from collections import deque


class QualityScorer:
    """滑动平均评分器。"""

    def __init__(self, window: int = 10):
        """
        :param window: 滑动窗口大小（取最近 N 次瞬时分求均值）
        """
        self.scores = deque(maxlen=window)

    def update(self, rtt_ms: float, loss_percent: float):
        """
        输入一次 RTT 与丢包率，返回 (评分, 等级)。

        :param rtt_ms:      到监控主机 RTT（毫秒）
        :param loss_percent: 丢包率（百分比）
        :return: (score:int, grade:str)
        """
        latency_pen = max(0, (rtt_ms - 5) / 10) * 15
        loss_pen = loss_percent * 10
        instant = max(0, round(100 - latency_pen - loss_pen))
        self.scores.append(instant)
        score = round(sum(self.scores) / len(self.scores))
        grade = self.grade_of(score)
        return score, grade

    @staticmethod
    def grade_of(score: int) -> str:
        """评分 → 等级（§9.3）。"""
        if score >= 90:
            return "优秀"
        if score >= 70:
            return "良好"
        if score >= 50:
            return "一般"
        return "较差"

    def reset(self) -> None:
        """清空滑动窗口。"""
        self.scores.clear()
