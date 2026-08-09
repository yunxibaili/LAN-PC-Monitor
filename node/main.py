# -*- coding: utf-8 -*-
"""
采集节点入口模块（见《README.md》§5.1）。

启动流程：
1. 解析命令行参数（--install-startup / --remove-startup / 普通启动）
2. 单实例检测（Global\\PC_Monitor_Node）
3. 初始化日志 → logs/node.log
4. 加载配置 node_config.json
5. 启动 TCP Server (0.0.0.0:12345)
6. 启动 UDP 广播器（2 秒 node_heartbeat）
7. 启动采集器线程池
8. 启动数据聚合器（1 秒广播）
9. 进入后台循环（Event.wait 阻塞），等退出信号

无界面要点：不创建 QApplication、不弹窗口。可用 pythonw.exe 启动。
"""
import argparse
import logging
import signal
import socket
import sys
import threading

from common.logger import setup_logger
from common.single_instance import ensure_single_instance, release_single_instance
from common.startup import install_node_startup, remove_node_startup
from common.utils import get_lan_ip
from node import config as node_config
from node.aggregator import DataAggregator
from node.collectors import create_collectors, start_all, stop_all
from node.discovery import (DiscoveryBroadcaster, register_mdns,
                            unregister_mdns)
from node.tcp_server import MonitorTCPServer

# 全局退出事件
_stop_event = threading.Event()


def _handle_signal(signum, frame):
    """SIGINT/SIGTERM → 置退出事件。"""
    logging.getLogger("node").info("收到退出信号 %s", signum)
    _stop_event.set()


def parse_args():
    parser = argparse.ArgumentParser(description="采集节点：无界面后台采集+推送")
    parser.add_argument("--install-startup", action="store_true",
                        help="安装开机自启动（需管理员，schtasks）")
    parser.add_argument("--remove-startup", action="store_true",
                        help="卸载开机自启动")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.install_startup:
        ok = install_node_startup()
        return 0 if ok else 1
    if args.remove_startup:
        ok = remove_node_startup()
        return 0 if ok else 1

    # 单实例检测
    mutex = ensure_single_instance("Global\\PC_Monitor_Node")
    if mutex is None:
        print("已有采集节点实例在运行，退出。")
        return 1

    # 初始化日志
    log = setup_logger("node")
    log.info("====== 采集节点启动 ======")

    # 加载配置
    cfg = node_config.load_config()
    log.info("TCP 端口 %d, UDP 端口 %d", cfg["tcp_port"], cfg["udp_port"])

    # 端口占用检测（§5.1 步骤 5）
    from common.utils import check_port_in_use
    if check_port_in_use(cfg["tcp_port"], "tcp"):
        print(f"错误: TCP 端口 {cfg['tcp_port']} 已被占用，请检查是否已有节点实例运行。")
        return 1
    if check_port_in_use(cfg["udp_port"], "udp"):
        print(f"错误: UDP 端口 {cfg['udp_port']} 已被占用，请检查是否已有节点实例运行。")
        return 1

    # 注册退出信号
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    # TCP Server
    server = MonitorTCPServer(port=cfg["tcp_port"], token=cfg["token"])
    server.start()

    # UDP 广播器
    broadcaster = DiscoveryBroadcaster(
        tcp_port=cfg["tcp_port"], udp_port=cfg["udp_port"], token=cfg["token"],
        use_multicast=cfg.get("use_multicast", False),
        preferred_iface=cfg.get("preferred_iface", ""))
    broadcaster.start()

    # mDNS 零配置注册（§5.6 / §23.1），zeroconf 不可用时自动降级
    lan_ip = get_lan_ip(cfg.get("preferred_iface", ""))
    mdns_zc = register_mdns(lan_ip, cfg["tcp_port"], socket.gethostname(),
                            cfg["token"])

    # 打印连接码（§23.2），便于用户在其他电脑输入接入
    try:
        from common.connect_code import make_connect_code
        code = make_connect_code(lan_ip, cfg["tcp_port"], cfg["token"])
        print(f"\n  本机节点连接码: {code}   (在副机/主机端\"连接码接入\"输入)")
        print(f"  连接串: pcmonitor://{lan_ip}:{cfg['tcp_port']}?token={cfg['token']}\n")
        log.info("本机连接码: %s", code)
    except Exception:
        pass

    # 采集器
    collectors = create_collectors(cfg)
    start_all(collectors)

    # 聚合器
    aggregator = DataAggregator(server=server, collectors=collectors)
    aggregator.start()

    # 性能兜底（§16）：CPU 超限自动降级
    from host.self_monitor import SelfMonitor
    self_monitor = SelfMonitor(aggregator, collectors)
    self_monitor.start()

    log.info("采集节点运行中（无界面后台）。Ctrl+C 退出。")
    try:
        # 后台阻塞，等待退出信号
        while not _stop_event.is_set():
            _stop_event.wait(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        # 退出清理
        self_monitor.stop()
        log.info("====== 采集节点退出中 ======")
        aggregator.stop()
        stop_all(collectors)
        server.stop()
        broadcaster.stop()
        unregister_mdns(mdns_zc)
        release_single_instance(mutex)
        log.info("====== 采集节点退出 ======")
    return 0


if __name__ == "__main__":
    sys.exit(main())
