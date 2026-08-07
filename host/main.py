# -*- coding: utf-8 -*-
"""
监控主机入口模块（见《技术文档.md》§6）。

启动流程：
1. 解析命令行参数（--install-startup / --remove-startup）
2. 单实例检测（Global\\PC_Monitor_Host）
3. 初始化日志 → logs/host.log
4. 加载配置 host_config.json
5. 创建 QApplication + 深色主题
6. 初始化本机节点（本地采集器直供 GUI）
7. 加载已保存远程节点并自动连接
8. 启动 UDP 心跳监听（自动发现）
9. 进入 Qt 事件循环
"""
import argparse
import logging
import sys

from PyQt5.QtWidgets import QApplication

from common.logger import setup_logger
from common.single_instance import ensure_single_instance, release_single_instance
from common.startup import install_host_startup, remove_host_startup
from common.theme import DARK_QSS
from host import config as host_config
from host.gui.main_window import HostMainWindow


def parse_args():
    parser = argparse.ArgumentParser(description="监控主机：集中显示所有节点")
    parser.add_argument("--install-startup", action="store_true",
                        help="安装开机自启动（注册表 Run，无需管理员）")
    parser.add_argument("--remove-startup", action="store_true",
                        help="卸载开机自启动")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.install_startup:
        return 0 if install_host_startup() else 1
    if args.remove_startup:
        return 0 if remove_host_startup() else 1

    mutex = ensure_single_instance("Global\\PC_Monitor_Host")
    if mutex is None:
        print("已有监控主机实例在运行，退出。")
        return 1

    log = setup_logger("host")
    log.info("====== 监控主机启动 ======")

    cfg = host_config.load_config()

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)

    window = HostMainWindow(cfg)
    window.show()

    ret = app.exec_()
    release_single_instance(mutex)
    log.info("====== 监控主机退出 ======")
    return ret


if __name__ == "__main__":
    sys.exit(main())
