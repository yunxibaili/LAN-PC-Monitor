# -*- coding: utf-8 -*-
"""ThemeStyle —— QSS 样式生成器（v5.2 Phase 4-2）。"""
from host.gui.theme.colors import ThemeColors as C
from host.gui.theme.metrics import ThemeMetrics as M


def dark_qss():
    return f"""
* {{
    font-family: 'Microsoft YaHei', 'Segoe UI', Consolas, sans-serif;
    font-size: {M.FONT_SIZE_MD}px;
    color: {C.TEXT_PRIMARY};
}}
QMainWindow, QDialog {{ background-color: {C.BG_BASE}; }}
QWidget {{ background: transparent; }}
QLabel#panel_title {{
    color: {C.PRIMARY}; font-weight: bold; font-size: {M.FONT_SIZE_LG}px;
    border-bottom: 1px solid {C.BORDER_DEFAULT}; padding-bottom: {M.SPACING_SM}px;
}}
QGroupBox {{
    border: 1px solid {C.BORDER_DEFAULT}; border-radius: {M.RADIUS_SM}px;
    margin-top: {M.SPACING_SM}px; color: {C.TEXT_PRIMARY};
    background: {C.BG_CARD};
}}
QGroupBox::title {{
    subcontrol-origin: margin; left: {M.SPACING_SM}px;
    padding: 0 {M.SPACING_XS}px; color: {C.PRIMARY};
}}
QPushButton {{
    background-color: {C.BG_ELEVATED}; color: {C.TEXT_PRIMARY};
    border: 1px solid {C.BORDER_DEFAULT};
    padding: {M.SPACING_SM}px {M.SPACING_LG}px;
    border-radius: {M.RADIUS_SM}px;
}}
QPushButton:hover {{ background-color: {C.BG_HOVER}; border-color: {C.PRIMARY}; }}
QPushButton:pressed {{ background-color: {C.BG_BASE}; }}
QPushButton:disabled {{ color: {C.TEXT_MUTED}; background-color: {C.BG_SURFACE}; }}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {C.BG_INPUT}; color: {C.TEXT_PRIMARY};
    border: 1px solid {C.BORDER_DEFAULT};
    padding: {M.SPACING_XS}px {M.SPACING_SM}px;
    border-radius: {M.RADIUS_SM}px;
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
QCheckBox {{ color: {C.TEXT_PRIMARY}; spacing: {M.SPACING_SM}px; }}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border: 2px solid {C.BORDER_DEFAULT}; border-radius: 4px;
    background: {C.BG_INPUT};
}}
QCheckBox::indicator:checked {{ background: {C.PRIMARY}; border-color: {C.PRIMARY}; }}
QListWidget {{
    background-color: {C.BG_CARD}; border: 1px solid {C.BORDER_DEFAULT};
    border-radius: {M.RADIUS_SM}px; outline: none;
}}
QListWidget::item {{ padding: {M.SPACING_SM}px; border-bottom: 1px solid {C.BORDER_DEFAULT}; }}
QListWidget::item:selected {{ background-color: {C.BG_HOVER}; border-left: 3px solid {C.PRIMARY}; }}
QListWidget::item:hover {{ background-color: {C.BG_HOVER}; }}
QTableWidget {{
    background-color: {C.BG_BASE}; alternate-background-color: {C.TABLE_ALT_ROW};
    gridline-color: {C.TABLE_GRID}; color: {C.TEXT_PRIMARY}; border: none;
    border-radius: {M.RADIUS_SM}px; selection-background-color: {C.BG_HOVER};
}}
QTableWidget::item {{ padding: {M.SPACING_XS}px; }}
QTableWidget::item:hover {{ background-color: {C.TABLE_HOVER}; }}
QHeaderView::section {{
    background-color: {C.TABLE_HEADER_BG}; color: {C.TEXT_SECONDARY};
    border: none; border-bottom: 2px solid {C.BORDER_DEFAULT};
    padding: {M.SPACING_SM}px; font-weight: 600;
}}
QTabWidget::pane {{ border: 1px solid {C.BORDER_DEFAULT}; border-radius: {M.RADIUS_SM}px; background: {C.BG_CARD}; }}
QTabBar::tab {{
    background: {C.BG_ELEVATED}; color: {C.TEXT_SECONDARY};
    padding: {M.SPACING_SM}px {M.SPACING_LG}px;
    border: 1px solid {C.BORDER_DEFAULT}; border-bottom: none;
    border-top-left-radius: {M.RADIUS_SM}px; border-top-right-radius: {M.RADIUS_SM}px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{ background: {C.BG_CARD}; color: {C.TEXT_PRIMARY}; border-bottom: 2px solid {C.PRIMARY}; font-weight: 600; }}
QTabBar::tab:hover:!selected {{ background: {C.BG_HOVER}; }}
QScrollBar:vertical {{ background: transparent; width: {M.SPACING_SM}px; margin: {M.SPACING_XS}px; }}
QScrollBar::handle:vertical {{ background: {C.BORDER_DEFAULT}; min-height: 24px; border-radius: {M.SPACING_SM}px; }}
QScrollBar::handle:vertical:hover {{ background: {C.TEXT_MUTED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QProgressBar {{ border: none; background-color: {C.BAR_BG}; border-radius: 3px; max-height: 6px; text-align: center; }}
QProgressBar::chunk {{ border-radius: 3px; background-color: {C.BAR_SUCCESS}; }}
QSplitter::handle {{ background: {C.BORDER_DEFAULT}; width: 1px; }}
QStatusBar {{ background: {C.BG_SURFACE}; color: {C.TEXT_SECONDARY}; border-top: 1px solid {C.BORDER_DEFAULT}; font-size: {M.FONT_SIZE_SM}px; }}
QToolTip {{ background-color: {C.BG_ELEVATED}; color: {C.TEXT_PRIMARY}; border: 1px solid {C.BORDER_DEFAULT}; border-radius: {M.RADIUS_SM}px; padding: {M.SPACING_XS}px; }}
"""
