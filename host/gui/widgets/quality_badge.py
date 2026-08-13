# -*- coding: utf-8 -*-
"""
QualityBadge —— 评分徽标（v5.2 Phase 4-1B）。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QWidget

from host.gui.theme.colors import ThemeColors as TC
from host.gui.theme.metrics import ThemeMetrics as TM


class QualityBadge(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        self._score_label = QLabel("—")
        self._score_label.setAlignment(Qt.AlignCenter)
        self._score_label.setStyleSheet(
            f"color: {TC.TEXT_MUTED}; font-size: {TM.FONT_SIZE_LG}px; font-weight: bold; background: transparent;")
        layout.addWidget(self._score_label)

        self._grade_label = QLabel("—")
        self._grade_label.setAlignment(Qt.AlignCenter)
        self._grade_label.setStyleSheet(
            f"color: {TC.TEXT_MUTED}; font-size: {TM.FONT_SIZE_SM}px; background: transparent;")
        layout.addWidget(self._grade_label)

    def set_score(self, score: int, grade: str) -> None:
        color = TC.score_color(score)
        self._score_label.setText(str(score))
        self._score_label.setStyleSheet(
            f"color: {color}; font-size: {TM.FONT_SIZE_LG}px; font-weight: bold; background: transparent;")
        self._grade_label.setText(grade)
        self._grade_label.setStyleSheet(
            f"color: {color}; font-size: {TM.FONT_SIZE_SM}px; background: transparent;")
