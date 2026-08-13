# -*- coding: utf-8 -*-
"""
连接工厂 —— 创建 NodeConnection（v5.2 Phase 3-8 架构约束）。

职责：
  - 作为 host/gui 层（Page/Widget/Controller）与 host.connection.NodeConnection
    之间的唯一桥梁。
  - 惰性导入 NodeConnection（依赖 PyQt5），便于无 GUI 环境测试 controllers。

架构约束：
  - host/gui 下的 Controller 不静态依赖 Connection；统一经本工厂创建。
"""
import logging

log = logging.getLogger("host.facade.connection_factory")


def create_connection(node_id: str, ip: str, port: int,
                      token: str, alias: str = ""):
    """创建并返回 NodeConnection 实例。

    :param node_id: 节点唯一 ID
    :param ip:      目标 Agent IP
    :param port:    目标 Agent HTTP 端口
    :param token:   鉴权 token
    :param alias:   节点别名（可选）
    :return: NodeConnection 实例
    """
    from host.connection import NodeConnection
    return NodeConnection(node_id, ip, port, token, alias)
