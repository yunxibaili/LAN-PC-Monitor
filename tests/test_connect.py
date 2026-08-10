# -*- coding: utf-8 -*-
"""
v5.0 双端连接端到端测试 —— 已废弃。

v5.0 前后端分离后：
- 节点端（node.tcp_server）已删除，改用 Agent 的 aiohttp REST + WebSocket。
- v4.0 双端 TCP 连接测试不再适用。

请使用 ``tests/test_api.py`` 覆盖：
- Agent REST /api/health、/api/nodes、/api/config
- Agent WebSocket /ws 鉴权 + monitor_data 帧推送
- loss_ping / loss_pong 回显

保留本文件仅为兼容历史调用：直接打印提示并以 0 退出码通过。
"""
import sys


def main():
    print("=" * 60)
    print("test_connect.py 已废弃（v4.0 TCP 双端测试，v5.0 不再适用）")
    print("请使用 test_api.py 覆盖 REST + WebSocket 端到端测试")
    print("=" * 60)
    print("\n  [SKIP] test_connect (v4.0 node.* → v5.0 agent/host; 使用 test_api.py)")
    print("\n结果: 0 通过, 0 失败 (skip)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
