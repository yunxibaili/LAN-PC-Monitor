# -*- coding: utf-8 -*-
"""
副机端入口模块 —— 本机仪表盘 + 节点管理（见《技术文档.md》§6）。

供 `python -m client` 调用；`client_main.py` 为独立脚本入口的等价实现。
"""
import logging
import sys

from PyQt5.QtWidgets import QApplication

from common.logger import setup_logger
from common.single_instance import ensure_single_instance, release_single_instance
from common.startup import install_client_startup, remove_client_startup
from common.theme import DARK_QSS
from client import config as client_config
from client.gui.main_window import ClientMainWindow


def main() -> int:
    # 支持 --install-startup / --remove-startup
    if "--install-startup" in sys.argv:
        return 0 if install_client_startup() else 1
    if "--remove-startup" in sys.argv:
        return 0 if remove_client_startup() else 1

    mutex = ensure_single_instance("Global\\PC_Monitor_Client")
    if mutex is None:
        print("已有副机端实例在运行，退出。")
        return 1

    log = setup_logger("client")
    log.info("====== 副机端启动 ======")

    cfg = client_config.load_config()

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)

    window = ClientMainWindow(cfg)
    window.show()

    ret = app.exec_()
    release_single_instance(mutex)
    log.info("====== 副机端退出 ======")
    return ret


if __name__ == "__main__":
    sys.exit(main())
