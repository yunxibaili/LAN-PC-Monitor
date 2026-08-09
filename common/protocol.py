# -*- coding: utf-8 -*-
"""
通信协议模块 —— TCP 帧格式（解决粘包）与各控制帧类型定义。

帧格式（见《README.md》§4.1）：
    ┌──────────────────────┬───────────────────────────────────┐
    │  帧长度 (4 bytes, 大端) │  JSON 载荷 (UTF-8, length 字节)     │
    │  uint32, 不含自身 4 字节 │  {"type": "monitor_data", ...}     │
    └──────────────────────┴───────────────────────────────────┘

控制帧与数据帧 type 一览（§4.2）：
    monitor_data  主机 → 副机  1 秒监控数据帧
    ping/pong     副机 → 主机   RTT 测量（ts 用 perf_counter）
    loss_ping/loss_pong 副机 → 主机 丢包测量
    auth / auth_result  副机 → 主机 / 主机 → 副机 鉴权
    host_heartbeat 主机 → 局域网(UDP) 自动发现心跳

注意事项：
- 帧内 JSON 使用 ensure_ascii=False，保证中文主机名/进程名不乱码。
- recv_frame 遇损坏帧返回 None，由上层丢弃并等下一帧，不抛异常中断连接。
"""
import json
import socket
import struct

# 默认端口（与文档一致）
DEFAULT_TCP_PORT = 12345
DEFAULT_UDP_PORT = 12346

# 帧类型常量
TYPE_MONITOR_DATA = "monitor_data"      # 监控数据帧
TYPE_PING = "ping"                       # RTT 测量请求
TYPE_PONG = "pong"                       # RTT 测量回复
TYPE_LOSS_PING = "loss_ping"             # 丢包测量请求
TYPE_LOSS_PONG = "loss_pong"             # 丢包测量回复
TYPE_AUTH = "auth"                       # 鉴权请求
TYPE_AUTH_RESULT = "auth_result"         # 鉴权结果
TYPE_HOST_HEARTBEAT = "host_heartbeat"   # UDP 自动发现心跳


def send_frame(sock: socket.socket, payload: dict) -> None:
    """
    发送一帧：4 字节大端长度前缀 + UTF-8 JSON 载荷。

    :param sock:   已连接的 TCP socket
    :param payload: 任意可 JSON 序列化的字典（须含 type 字段）
    """
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    sock.sendall(struct.pack(">I", len(data)) + data)


def recv_exactly(sock: socket.socket, n: int) -> bytes | None:
    """
    精确接收 n 字节；对端关闭时返回 None（而非抛异常）。

    :param sock: 已连接的 TCP socket
    :param n:    需要接收的字节数
    :return:     收到的字节串；连接被对端关闭返回 None
    """
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            # 对端已关闭连接
            return None
        buf += chunk
    return buf


def recv_frame(sock: socket.socket) -> dict | None:
    """
    接收并解析一帧 JSON。

    :param sock: 已连接的 TCP socket
    :return:     解析后的字典；连接关闭或收到损坏帧时返回 None
    """
    header = recv_exactly(sock, 4)
    if header is None:
        return None
    length = struct.unpack(">I", header)[0]
    if length > 10 * 1024 * 1024:  # 单帧上限 10MB，防止恶意超大帧拖垮内存
        return None
    body = recv_exactly(sock, length)
    if body is None:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        # 损坏帧丢弃，等下一帧
        return None
