# -*- coding: utf-8 -*-
"""ThemeStyle —— QSS 样式生成器（v5.4 亮色 Professional Monitoring Console）。"""
from host.gui.theme.colors import ThemeColors as C
from host.gui.theme.spacing import ThemeSpacing as S
from host.gui.theme.typography import ThemeTypography as TT


def light_qss():
    """亮色主题 QSS。"""
    return f"""
* {{
    font-family: {TT.FONT_FAMILY};
    font-size: {TT.BODY['size']}px;
    color: {C.TEXT_PRIMARY};
}}
QMainWindow {{ background-color: {C.BG_BASE}; }}
QDialog {{ background-color: {C.BG_BASE}; }}
QLabel {{
    background: transparent;
}}
QLabel#panel_title {{
    color: {C.PRIMARY}; font-weight: bold; font-size: {TT.TITLE_LARGE['size']}px;
    border-bottom: 1px solid {C.BORDER_DEFAULT}; padding-bottom: {S.SM}px;
}}
QGroupBox {{
    border: 1px solid {C.BORDER_DEFAULT}; border-radius: {S.SM}px;
    margin-top: {S.SM}px; color: {C.TEXT_PRIMARY};
    background: {C.BG_CARD};
}}
QGroupBox::title {{
    subcontrol-origin: margin; left: {S.SM}px;
    padding: 0 {S.XS}px; color: {C.PRIMARY};
}}
QPushButton {{
    background-color: {C.BG_ELEVATED}; color: {C.TEXT_PRIMARY};
    border: 1px solid {C.BORDER_DEFAULT};
    padding: {S.SM}px {S.LG}px;
    border-radius: {S.SM}px;
}}
QPushButton:hover {{ background-color: {C.BG_HOVER}; border-color: {C.PRIMARY}; }}
QPushButton:pressed {{ background-color: {C.BG_BASE}; }}
QPushButton:disabled {{ color: {C.TEXT_MUTED}; background-color: {C.BG_SURFACE}; }}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {C.BG_INPUT}; color: {C.TEXT_PRIMARY};
    border: 1px solid {C.BORDER_DEFAULT};
    padding: {S.XS}px {S.SM}px;
    border-radius: {S.SM}px;
    selection-background-color: {C.PRIMARY};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border-color: {C.PRIMARY};
}}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background-color: {C.BG_CARD}; border: 1px solid {C.BORDER_DEFAULT};
    selection-background-color: {C.BG_HOVER};
}}
QCheckBox {{ color: {C.TEXT_PRIMARY}; spacing: {S.SM}px; }}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border: 2px solid {C.BORDER_DEFAULT}; border-radius: 4px;
    background: {C.BG_INPUT};
}}
QCheckBox::indicator:checked {{ background: {C.PRIMARY}; border-color: {C.PRIMARY}; }}
QListWidget {{
    background-color: {C.BG_CARD}; border: 1px solid {C.BORDER_DEFAULT};
    border-radius: {S.SM}px; outline: none;
}}
QListWidget::item {{ padding: {S.SM}px; border-bottom: 1px solid {C.BORDER_DEFAULT}; }}
QListWidget::item:selected {{ background-color: {C.BG_HOVER}; border-left: 3px solid {C.PRIMARY}; }}
QListWidget::item:hover {{ background-color: {C.BG_HOVER}; }}
QTableWidget {{
    background-color: {C.BG_BASE}; alternate-background-color: {C.TABLE_ALT_ROW};
    gridline-color: {C.TABLE_GRID}; color: {C.TEXT_PRIMARY}; border: none;
    border-radius: {S.SM}px; selection-background-color: {C.BG_HOVER};
}}
QTableWidget::item {{ padding: {S.XS}px; }}
QTableWidget::item:hover {{ background-color: {C.TABLE_HOVER}; }}
QHeaderView::section {{
    background-color: {C.TABLE_HEADER_BG}; color: {C.TEXT_SECONDARY};
    border: none; border-bottom: 2px solid {C.BORDER_DEFAULT};
    padding: {S.SM}px; font-weight: 600;
}}
QTabWidget::pane {{ border: 1px solid {C.BORDER_DEFAULT}; border-radius: {S.SM}px; background: {C.BG_CARD}; }}
QTabBar::tab {{
    background: {C.BG_ELEVATED}; color: {C.TEXT_SECONDARY};
    padding: {S.SM}px {S.LG}px;
    border: 1px solid {C.BORDER_DEFAULT}; border-bottom: none;
    border-top-left-radius: {S.SM}px; border-top-right-radius: {S.SM}px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{ background: {C.BG_CARD}; color: {C.TEXT_PRIMARY}; border-bottom: 2px solid {C.PRIMARY}; font-weight: 600; }}
QTabBar::tab:hover:!selected {{ background: {C.BG_HOVER}; }}
QScrollBar:vertical {{ background: transparent; width: {S.SM}px; margin: {S.XS}px; }}
QScrollBar::handle:vertical {{ background: {C.BORDER_DEFAULT}; min-height: 24px; border-radius: {S.SM}px; }}
QScrollBar::handle:vertical:hover {{ background: {C.TEXT_MUTED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QProgressBar {{ border: none; background-color: {C.BAR_BG}; border-radius: 4px; max-height: 8px; text-align: center; }}
QProgressBar::chunk {{ border-radius: 4px; background-color: {C.BAR_SUCCESS}; }}
QSplitter::handle {{ background: {C.BORDER_DEFAULT}; width: 1px; }}
QStatusBar {{ background: {C.BG_SURFACE}; color: {C.TEXT_SECONDARY}; border-top: 1px solid {C.BORDER_DEFAULT}; font-size: {TT.CAPTION['size']}px; }}
QToolTip {{ background-color: {C.BG_ELEVATED}; color: {C.TEXT_PRIMARY}; border: 1px solid {C.BORDER_DEFAULT}; border-radius: {S.SM}px; padding: {S.XS}px; }}
"""


class ThemeStyle:
    """QSS 样式生成器。"""
    @staticmethod
    def dark_qss() -> str:
        return light_qss()

    @staticmethod
    def light_qss() -> str:
        return light_qss()


# 向后兼容别名
dark_qss = light_qss
