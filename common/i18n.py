# -*- coding: utf-8 -*-
"""
国际化（i18n）核心模块 —— 多语言支持（见《README.md》§22 / docs/i18n_design.md）。

提供：
- load_language(lang)：加载语言资源（zh_CN / en）
- tr(key, *args)：按 key 取文案，支持 {0}/{1} 占位符
- get_lang()：当前语言
- choose_language_dialog()：启动时语言选择弹窗

文案资源：i18n/{lang}.json（zh_CN.json / en.json，key 一致）。
"""
import json
import os

# 支持的语言
LANGS = ("zh_CN", "en")

_lang = "zh_CN"
_strings = {}

# i18n 资源目录
_I18N_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "i18n")


def load_language(lang: str) -> None:
    """加载语言资源；语言缺失或文件缺失回退 zh_CN。"""
    global _lang, _strings
    _lang = lang if lang in LANGS else "zh_CN"
    path = os.path.join(_I18N_DIR, f"{_lang}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _strings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _strings = {}
        if _lang != "zh_CN":
            load_language("zh_CN")


def tr(key: str, *args) -> str:
    """
    按 key 取文案；key 不存在时回退显示 key 本身（便于发现遗漏）。
    支持 {0}/{1} 位置占位符格式化。
    """
    text = _strings.get(key, key)
    if args:
        try:
            return text.format(*args)
        except (IndexError, KeyError):
            return text
    return text


def get_lang() -> str:
    """当前语言代码。"""
    return _lang


def choose_language_dialog(parent=None) -> str:
    """
    语言选择弹窗（启动时首次调用）。

    弹窗按钮固定双语（中文 / English），不依赖已加载语言；
    选定后调用 load_language() 并返回语言代码。
    """
    from PyQt5.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPushButton,
                                 QVBoxLayout, QWidget)

    if parent is not None and not isinstance(parent, QWidget):
        parent = None
    dialog = QDialog(parent)
    dialog.setWindowTitle("选择语言 / Select Language")
    dialog.resize(320, 160)
    layout = QVBoxLayout(dialog)

    label = QLabel("请选择语言 / Please choose your language:")
    label.setStyleSheet("font-size: 15px;")
    layout.addWidget(label)

    btn_row = QHBoxLayout()
    result = {"lang": "zh_CN"}

    def choose(lang):
        result["lang"] = lang
        dialog.accept()

    btn_zh = QPushButton("中文")
    btn_zh.setMinimumHeight(40)
    btn_zh.clicked.connect(lambda: choose("zh_CN"))
    btn_en = QPushButton("English")
    btn_en.setMinimumHeight(40)
    btn_en.clicked.connect(lambda: choose("en"))
    btn_row.addWidget(btn_zh)
    btn_row.addWidget(btn_en)
    layout.addLayout(btn_row)

    dialog.exec_()
    load_language(result["lang"])
    return result["lang"]


def ensure_language(cfg: dict, save_config_fn, parent=None) -> str:
    """
    启动时确保语言已确定并加载（v5.1：取消启动语言弹窗）。

    流程：
    1. 配置有 "language" → 直接 load_language。
    2. 配置无 → 默认 zh_CN，写入配置，**不弹窗**。
       语言改由设置中心统一管理（首次初始化向导中可设置）。

    :param cfg:            配置字典（含/不含 language）
    :param save_config_fn: 回调 fn(cfg) 保存配置
    :param parent:         保留参数（兼容旧调用）
    :return: 最终语言代码
    """
    lang = cfg.get("language")
    if lang and lang in LANGS:
        load_language(lang)
        return lang
    # v5.1：无语言配置 → 默认 zh_CN，静默写入，不弹启动弹窗
    lang = "zh_CN"
    load_language(lang)
    cfg["language"] = lang
    if save_config_fn:
        try:
            save_config_fn(cfg)
        except Exception:
            pass
    return lang
