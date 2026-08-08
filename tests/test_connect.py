# -*- coding: utf-8 -*-
"""
双端连接端到端测试 —— 无 PyQt5 环境模拟 host 客户端连接 node 端。

验证：
1. node 端 TCP Server 启动（真实采集器）
2. host 端鉴权成功
3. host 端连续接收 monitor_data 帧（含完整字段）
4. RTT ping/pong
5. 丢包 loss_ping/loss_pong
6. 数据完整性（system/cpu/ram/gpu/disk/net/processes 各分区）
7. 断线后 node 端唯一客户端计数归零

用法：python test_connect.py
"""
import os
import socket
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from common.protocol import send_frame, recv_frame

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  {detail}")


def main():
    print("=" * 60)
    print("双端连接端到端测试")
    print("=" * 60)

    # 启动 node 端（真实采集器）
    from node.tcp_server import MonitorTCPServer
    from node.aggregator import DataAggregator
    from node.collectors import create_collectors, start_all

    PORT = 18900
    TOKEN = "e2e_test_token"
    server = MonitorTCPServer(port=PORT, token=TOKEN)
    server.start()
    collectors = create_collectors({})
    start_all(collectors)
    agg = DataAggregator(server=server, collectors=collectors)
    agg.start()
    print("\n--- Node 端已启动 (TCP %d) ---" % PORT)

    # 预热采集器
    time.sleep(3)

    # --- 连接 host 客户端 ---
    print("\n--- 1. Host 连接与鉴权 ---")
    sock = socket.create_connection(("127.0.0.1", PORT), timeout=5)
    sock.settimeout(5)
    send_frame(sock, {"type": "auth", "token": TOKEN})
    auth = recv_frame(sock)
    check("鉴权通过", auth and auth.get("ok") is True, str(auth))
    check("node 唯一客户端数=1", server.unique_client_count() == 1)

    # --- 2. 连续接收数据帧 ---
    print("\n--- 2. 接收 monitor_data 数据帧 ---")
    frames = []
    for i in range(5):
        try:
            f = recv_frame(sock)
            frames.append(f)
        except socket.timeout:
            print(f"  [WARN] 第{i+1}帧接收超时")
    check("连续收到 5 帧", len(frames) == 5, f"收到 {len(frames)} 帧")

    if frames:
        f0 = frames[-1]  # 用最后一帧（预热完成后）
        # 顶层字段
        check("帧 type=monitor_data", f0.get("type") == "monitor_data")
        check("含 hostname", bool(f0.get("hostname")))
        # 各分区
        check("system 含 IP", bool(f0.get("system", {}).get("local_ip")),
              str(f0.get("system", {}).get("local_ip")))
        check("system 含 uptime", "uptime_seconds" in f0.get("system", {}))
        check("cpu 含 total_usage", "total_usage" in f0.get("cpu", {}))
        check("ram 含 usage_percent", "usage_percent" in f0.get("ram", {}))
        check("gpu 含 usage_percent", "usage_percent" in f0.get("gpu", {}))
        check("disk 为列表", isinstance(f0.get("disk", []), list))
        check("net 含 upload_mb_s", "upload_mb_s" in f0.get("net", {}))
        check("processes 含 top_cpu", "top_cpu" in f0.get("processes", {}))

        # 打印一帧摘要
        print("\n  最新一帧摘要:")
        print(f"    hostname = {f0.get('hostname')}")
        print(f"    IP       = {f0.get('system', {}).get('local_ip')}")
        print(f"    uptime   = {f0.get('system', {}).get('uptime_seconds')}s")
        print(f"    CPU      = {f0.get('cpu', {}).get('total_usage')}%")
        print(f"    RAM      = {f0.get('ram', {}).get('usage_percent')}%")
        print(f"    GPU      = {f0.get('gpu', {}).get('usage_percent')}")

    # --- 3. RTT ping/pong ---
    print("\n--- 3. RTT 测量 ---")
    rtts = []
    for _ in range(3):
        ts = time.perf_counter()
        send_frame(sock, {"type": "ping", "ts": ts})
        pong = recv_frame(sock)
        if pong and pong.get("type") == "pong":
            rtts.append((time.perf_counter() - ts) * 1000)
    check("收到 3 次 pong", len(rtts) == 3)
    if rtts:
        avg = sum(rtts) / len(rtts)
        check("RTT < 100ms", avg < 100, f"avg {avg:.3f}ms")
        print(f"    RTT 样本: {[f'{r:.3f}' for r in rtts]} ms")

    # --- 4. 丢包 loss_ping/loss_pong ---
    print("\n--- 4. 丢包测量 ---")
    loss_ok = 0
    for seq in (1, 2, 3):
        send_frame(sock, {"type": "loss_ping", "seq": seq, "ts": time.perf_counter()})
        lp = recv_frame(sock)
        if lp and lp.get("type") == "loss_pong" and lp.get("seq") == seq:
            loss_ok += 1
    check("收到 3 个 loss_pong", loss_ok == 3, f"{loss_ok}/3")

    # --- 5. 断开后计数归零 ---
    print("\n--- 5. 断线清理 ---")
    sock.close()
    time.sleep(0.5)
    check("断开后唯一客户端数=0", server.unique_client_count() == 0)

    # 清理
    agg.stop()
    from node.collectors import stop_all
    stop_all(collectors)
    server.stop()

    print("\n" + "=" * 60)
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
