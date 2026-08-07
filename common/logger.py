# -*- coding: utf-8 -*-
"""
日志模块 —— RotatingFileHandler 轮转日志（见《技术文档.md》§11）。

- 单文件最大 10MB，保留 5 份备份。
- 强制 UTF-8 编码，避免中文日志乱码。
- 返回独立命名 logger，避免与第三方库 logger 混淆。
"""
import logging
import os
from logging.handlers import RotatingFileHandler

# 默认日志目录（相对项目根目录）
DEFAULT_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

# 已创建的 logger 缓存，避免重复添加 handler 导致日志重复
_created_loggers = {}


def setup_logger(name: str, log_file: str = None, level: int = logging.INFO,
                 log_dir: str = DEFAULT_LOG_DIR) -> logging.Logger:
    """
    创建（或复用）一个带 RotatingFileHandler 的 logger。

    :param name:    logger 名称（如 "host" / "client"）
    :param log_file: 日志文件名（如 "host.log"），None 时用 f"{name}.log"
    :param level:    日志级别，生产环境建议 INFO
    :param log_dir:  日志目录，默认项目根 logs/
    :return: logging.Logger 实例
    """
    if name in _created_loggers:
        return _created_loggers[name]

    os.makedirs(log_dir, exist_ok=True)
    log_file = log_file or f"{name}.log"
    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = RotatingFileHandler(
        os.path.join(log_dir, log_file),
        maxBytes=10 * 1024 * 1024,   # 10MB
        backupCount=5,               # 5 份备份
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(handler)
    logger.propagate = False  # 不传给根 logger，避免重复输出

    _created_loggers[name] = logger
    return logger
