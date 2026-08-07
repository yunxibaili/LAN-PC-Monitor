# -*- coding: utf-8 -*-
"""
P0-P3 自检脚本 —— 无 GUI 窗口验证数据链路（v3.0 架构）。

用法（在项目根目录，需已 pip install -r requirements.txt）：
    python test_p0.py

验证项：
1. common/protocol 帧收发（含中文、粘包边界、大帧）
2. node/tcp_server 鉴权流程（正确/错误 token）
3. 采集节点聚合假数据 → TCP → 监控主机 NodeConnection 完整链路
4. RTT ping/pong
5. 退出阶段无竞态日志噪声（停机顺序验证）
6. host/config 持久化（hosts 增删去重）
7. 真实采集器冒烟测试（collect() 结构 + 可序列化）
8. 监控主机 UDP 自动发现（node_heartbeat 监听）
9. 网络质量评分器（v3.0 系数校准）

说明：
- 仅验证网络与数据链路，不弹出 GUI 窗口。
- NodeConnection 依赖 PyQt5.QtCore 信号机制；未安装 PyQt5 时跳过信号相关验证。
"""
import os
import socket
import sys
import threading
import time

# 将项目根目录加入 sys.path，保证可以直接运行
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 尝试创建 Qt 应用（信号跨线程投递需要），失败则标记无 Qt
try:
    from PyQt5.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication([])
    HAS_QT = True
except Exception:
    _app = None
    HAS_QT = False

PASS = 0
FAIL = 0
SKIP = 0


def check(name, cond):
    """断言检查：通过打勾，失败打叉。"""
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}")


def skip(name):
    """跳过检查（无 Qt 环境）。"""
    global SKIP
    SKIP += 1
    print(f"  [SKIP] {name}")


def pump_qt(seconds: float):
    """等待期间泵送 Qt 事件循环，使跨线程信号得以投递。"""
    if not HAS_QT:
        time.sleep(seconds)
        return
    end = time.time() + seconds
    while time.time() < end:
        _app.processEvents()
        time.sleep(0.02)


def test_protocol():
    """测试帧协议收发。"""
    print("\n--- 1. 帧协议 send_frame/recv_frame ---")
    from common.protocol import send_frame, recv_frame

    a, b = socket.socketpair()
    payload = {"type": "ping", "ts": 12345.6789, "中文": "主机名"}
    send_frame(a, payload)
    got = recv_frame(b)
    check("帧收发含中文", got == payload)
    check("中文未乱码", got and got["中文"] == "主机名")

    big = {"type": "monitor_data", "payload": "x" * 50000}
    send_frame(a, big)
    send_frame(a, {"type": "pong", "seq": 2})
    got1 = recv_frame(b)
    got2 = recv_frame(b)
    check("大帧(50KB)收发", got1 == big)
    check("粘包边界两帧分离", got2 == {"type": "pong", "seq": 2})

    a.close()
    check("对端关闭返回 None", recv_frame(b) is None)
    b.close()


def test_auth():
    """测试鉴权流程（采集节点 TCP Server）。"""
    print("\n--- 2. 节点鉴权流程 ---")
    from node.tcp_server import MonitorTCPServer
    from common.protocol import send_frame, recv_frame

    server = MonitorTCPServer(host="127.0.0.1", port=12345, token="secret123")
    server.start()
    time.sleep(0.2)

    # 错误 token
    sock = socket.create_connection(("127.0.0.1", 12345), timeout=3)
    sock.settimeout(3)
    send_frame(sock, {"type": "auth", "token": "wrong"})
    auth = recv_frame(sock)
    check("错误 token 被拒绝", auth and auth.get("ok") is False)
    sock.close()
    time.sleep(0.1)

    # 正确 token
    sock = socket.create_connection(("127.0.0.1", 12345), timeout=3)
    sock.settimeout(3)
    send_frame(sock, {"type": "auth", "token": "secret123"})
    auth = recv_frame(sock)
    check("正确 token 通过", auth and auth.get("ok") is True)
    check("唯一主机数 = 1", server.unique_client_count() == 1)

    # ping/pong
    ts = time.perf_counter()
    send_frame(sock, {"type": "ping", "ts": ts})
    pong = recv_frame(sock)
    rtt = (time.perf_counter() - ts) * 1000
    check("ping/pong 往返", pong and pong.get("type") == "pong"
          and abs(pong["ts"] - ts) < 1e-9)
    check("RTT 为正且 < 100ms", 0 < rtt < 100)

    # 广播数据帧
    recv_thread_done = threading.Event()
    received = {}

    def recv_once():
        nonlocal received
        received = recv_frame(sock)
        recv_thread_done.set()

    threading.Thread(target=recv_once, daemon=True).start()
    server.broadcast({"type": "monitor_data", "hostname": "TEST-PC"})
    recv_thread_done.wait(3)
    check("广播数据帧送达", received and received.get("hostname") == "TEST-PC")

    sock.close()
    time.sleep(0.1)
    check("断开后唯一主机数 = 0", server.unique_client_count() == 0)
    server.stop()


def test_connection():
    """测试监控主机 NodeConnection 与节点数据流（完整链路，依赖 Qt 信号）。"""
    print("\n--- 3. 节点聚合 → 主机接收 完整链路 ---")
    if not HAS_QT:
        skip("未安装 PyQt5，跳过信号链路验证")
        return

    from node.tcp_server import MonitorTCPServer
    from node.fake_data import FakeDataGenerator
    from node.aggregator import DataAggregator
    from host.connection import NodeConnection

    server = MonitorTCPServer(host="127.0.0.1", port=12346, token="tok123")
    server.start()
    time.sleep(0.2)

    # 用假数据源驱动聚合器（不依赖真实采集器，保证纯链路验证）
    agg = DataAggregator(server=server, data_source=FakeDataGenerator())
    agg.start()
    time.sleep(0.2)

    conn = NodeConnection("testnode", "127.0.0.1", 12346, "tok123", alias="测试节点")
    frames = []
    statuses = []
    rtts = []

    conn.data_received.connect(lambda f, h: frames.append(f))
    conn.status_changed.connect(lambda s, h: statuses.append(s))
    conn.rtt_updated.connect(lambda r, h: rtts.append(r))
    conn.start()

    # 等待连接与数据（泵 Qt 事件循环投递跨线程信号）
    deadline = time.time() + 6
    while time.time() < deadline and not frames:
        pump_qt(0.2)

    check("主机收到 monitor_data", len(frames) > 0)
    if frames:
        f0 = frames[0]
        check("数据帧含完整字段", f0.get("hostname")
              and "cpu" in f0 and "gpu" in f0 and "ram" in f0)
        check("connected_clients 去重计数 = 1", f0.get("connected_clients") == 1)
    check("主机状态含 已连接", any("已连接" in s for s in statuses))

    # 等待 RTT
    deadline = time.time() + 6
    while time.time() < deadline and not rtts:
        pump_qt(0.2)
    check("RTT 测量成功", len(rtts) > 0 and rtts[0] > 0)

    conn.stop()
    agg.stop()
    server.stop()


def test_graceful_shutdown():
    """测试退出阶段无竞态日志噪声（本次修复重点）。"""
    print("\n--- 5. 退出阶段无噪声 ---")
    if not HAS_QT:
        skip("未安装 PyQt5，跳过")
        return

    import io
    import logging
    from common.logger import setup_logger

    # 用一个内存 handler 捕获退出期间的日志
    stream = io.StringIO()
    ch = logging.StreamHandler(stream)
    ch.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))

    log = setup_logger("host", level=logging.DEBUG)
    log.addHandler(ch)

    from node.tcp_server import MonitorTCPServer
    from node.fake_data import FakeDataGenerator
    from node.aggregator import DataAggregator
    from node.discovery import DiscoveryBroadcaster
    from host.connection import NodeConnection

    # 起一个完整采集节点（TCP + UDP 广播 + 聚合）
    server = MonitorTCPServer(host="127.0.0.1", port=12347, token="shut123")
    server.start()
    bcast = DiscoveryBroadcaster(tcp_port=12347, udp_port=12347,
                                 token="shut123", interval=0.1)
    bcast.start()
    agg = DataAggregator(server=server, data_source=FakeDataGenerator())
    agg.start()
    time.sleep(0.3)

    # 挂一个监控主机连接
    conn = NodeConnection("shut", "127.0.0.1", 12347, "shut123", alias="关机测试")
    conn.start()
    deadline = time.time() + 4
    while time.time() < deadline and not conn.is_connected():
        pump_qt(0.1)
    check("主机已连接", conn.is_connected())

    # 记录当前日志长度，然后执行停机
    stream.truncate(0)
    stream.seek(0)

    # 执行退出顺序（与 node_main.py / host_main.py 一致）
    conn.stop()
    agg.stop()
    server.stop()
    bcast.stop()
    time.sleep(0.5)  # 给 daemon 线程时间退出并输出可能的噪声
    pump_qt(0.3)

    noise = stream.getvalue().strip()
    # 停机期间不应出现 广播失败/剔除失效客户端/连接失败 等噪声
    bad_keywords = ["广播失败", "剔除", "连接失败", "Bad file descriptor",
                    "鉴权失败", "UDP 广播失败"]
    bad_lines = [l for l in noise.splitlines()
                 if any(k in l for k in bad_keywords)]
    check("退出阶段无噪声日志", not bad_lines)
    if bad_lines:
        print("      实际输出噪声:")
        for l in bad_lines:
            print(f"        {l}")

    # 清理 handler 避免影响后续
    log.removeHandler(ch)
    ch.close()


def test_client_config():
    """测试监控主机配置持久化。"""
    print("\n--- 6. 主机配置持久化 ---")
    import tempfile
    tmp = tempfile.mkdtemp()
    import host.config as hcfg
    hcfg.CONFIG_FILE = os.path.join(tmp, "host_config.json")

    cfg = hcfg.load_config()
    from common.utils import make_host_id
    hcfg.upsert_host(cfg, make_host_id("192.168.1.100", 12345),
                     "192.168.1.100", 12345, "tok", "游戏节点")
    hcfg.upsert_host(cfg, make_host_id("192.168.1.101", 12345),
                     "192.168.1.101", 12345, "tok2", "直播节点")
    check("添加两台节点", len(cfg["hosts"]) == 2)

    hcfg.upsert_host(cfg, make_host_id("192.168.1.100", 12345),
                     "192.168.1.100", 12345, "tok3", "改名")
    check("同 IP+端口 去重更新", len(cfg["hosts"]) == 2
          and cfg["hosts"][0]["alias"] == "改名")

    cfg2 = hcfg.load_config()
    check("持久化后重新加载", len(cfg2["hosts"]) == 2)

    node_id = cfg2["hosts"][0]["node_id"]
    hcfg.remove_host(cfg2, node_id)
    check("移除节点", len(cfg2["hosts"]) == 1)


def test_collectors():
    """
    测试真实采集器：各采集器 collect() 返回字段完整且可 JSON 序列化。

    注意：校验直接使用 collect() 的返回值，而非 get()。
    因为 get() 只返回采集线程 _loop() 写入的缓存 self._data，
    测试若未调 start() 线程，_data 始终为空。collect() 每次调用
    都返回完整数据（文档 §5.2 约定），与线程调度无关，更适合冒烟测试。
    """
    print("\n--- 7. 真实采集器冒烟测试 ---")
    try:
        import psutil  # noqa: F401
    except ImportError:
        skip("未安装 psutil，跳过")
        return

    from node.collectors import create_collectors
    import json

    collectors = create_collectors({})

    # 预热两次：CPU/proc/disk/net 首次 collect() 仅建立差分基准，
    # 第二次调用才返回完整数据（含使用率/速度）
    for _ in range(2):
        for name, col in collectors.items():
            try:
                col.collect()
            except Exception as e:
                check(f"采集器 {name} 预热异常: {e}", False)

    # 校验各采集器 collect() 返回值可序列化且非空
    for name, col in collectors.items():
        try:
            data = col.collect()
            json.dumps(data, ensure_ascii=False)
            check(f"采集器 {name} 返回可序列化数据", True)
        except Exception as e:
            check(f"采集器 {name} 异常: {e}", False)

    # 磁盘采集器 collect() 返回 {"disks": [...]}；聚合器会解包为列表
    try:
        disk_data = collectors["disk"].collect()
        check("磁盘采集器返回 disks 列表",
              isinstance(disk_data.get("disks"), list))
    except Exception as e:
        check(f"磁盘采集器异常: {e}", False)

    # 关键字段存在性（§7 Schema 字段），直接校验 collect() 返回值
    for name in ("cpu", "ram", "net", "sys"):
        try:
            data = collectors[name].collect()
        except Exception as e:
            check(f"采集器 {name} collect() 异常: {e}", False)
            continue
        if name == "cpu":
            check("CPU 含 total_usage", "total_usage" in data)
        elif name == "ram":
            check("RAM 含 usage_percent", "usage_percent" in data)
        elif name == "net":
            check("NET 含 upload_mb_s", "upload_mb_s" in data)
        elif name == "sys":
            check("SYS 含 uptime_seconds", "uptime_seconds" in data)


def test_quality_scorer():
    """
    测试 QualityScorer 评分（§9）。

    各等级档位用独立评分器验证瞬时映射，避免滑动窗口把前值混入平均。
    """
    print("\n--- 9. 网络质量评分器 ---")
    from common.quality import QualityScorer

    # 优秀：低延迟低丢包（0% 丢包下 5ms 内满 100）
    s = QualityScorer(window=10)
    score, grade = s.update(1.0, 0.0)
    check("低延迟丢包 → 优秀", score >= 90 and grade == "优秀")

    # 良好：中延迟（15ms → 85）
    s = QualityScorer(window=10)
    score, grade = s.update(15.0, 0.0)
    check("中延迟 → 70~89", 70 <= score <= 89 and grade == "良好")

    # 一般：较高延迟（30ms → 63）
    s = QualityScorer(window=10)
    score, grade = s.update(30.0, 1.0)
    check("较高延迟 → 一般", 50 <= score <= 69 and grade == "一般")

    # 较差：高丢包（8% 丢包 → 20）
    s = QualityScorer(window=10)
    score, grade = s.update(5.0, 8.0)
    check("高丢包 → 较差", score < 50 and grade == "较差")

    # 滑动平均平滑：连续低延迟下 1 次恶劣值只会小幅拉低，
    # 而连续恶劣下 1 次优秀值也不会瞬间翻绿
    s_good = QualityScorer(window=10)
    for _ in range(9):
        s_good.update(2.0, 0.0)   # 9 次优秀
    s_good.update(200.0, 20.0)    # 1 次恶劣 → 瞬时 0
    score_after_bad, _ = s_good.update(2.0, 0.0)  # 再回优秀
    check("滑动平均：恶劣值后不剧变", score_after_bad >= 70)

    s_bad = QualityScorer(window=10)
    for _ in range(9):
        s_bad.update(200.0, 20.0)  # 9 次恶劣
    s_bad.update(2.0, 0.0)         # 1 次优秀
    score_after_good, _ = s_bad.update(200.0, 20.0)  # 再回恶劣
    check("滑动平均：优秀值后不虚高", score_after_good < 50)


def test_discovery():
    """测试监控主机 UDP 心跳监听（node_heartbeat 自动发现）。"""
    print("\n--- 8. 监控主机 UDP 自动发现 ---")
    if not HAS_QT:
        skip("未安装 PyQt5，跳过")
        return

    from node.discovery import DiscoveryListener
    import json
    import socket as _sock

    bcast_port = 23456  # 避开默认 12346，防止与真实监听冲突

    listener = DiscoveryListener(udp_port=bcast_port)
    listener.start()
    time.sleep(0.2)

    # 向监听端口发送一个模拟节点心跳
    s = _sock.socket(_sock.AF_INET, _sock.SOCK_DGRAM)
    payload = json.dumps({
        "type": "node_heartbeat",
        "hostname": "TEST-PC",
        "ip": "127.0.0.1",
        "tcp_port": 12345,
        "token": "disc_tok",
        "ts": time.time(),
    }, ensure_ascii=False).encode("utf-8")
    s.sendto(payload, ("127.0.0.1", bcast_port))
    s.close()

    # 等待监听器接收
    deadline = time.time() + 3
    hosts = {}
    while time.time() < deadline:
        hosts = listener.get_hosts()
        if hosts:
            break
        pump_qt(0.1)

    check("监听器收到心跳", len(hosts) > 0)
    if hosts:
        info = list(hosts.values())[0]
        check("心跳含 hostname", info.get("hostname") == "TEST-PC")
        check("心跳含 tcp_port", info.get("tcp_port") == 12345)

    listener.stop()


def run_demo():
    """
    演示模式：启动采集节点后台 + 监控主机 GUI（需 Windows + PyQt5）。

    用法：python test_p0.py --demo
    - 采集节点后台启动（真实采集器，建议管理员运行以显示温度/GPU）
    - 监控主机主窗口（含本机节点 + 自动连接 host_config.json 中的节点）

    注意：所有 QWidget/QObject 均在主线程创建（Qt 线程铁律），
    采集/推送服务内部使用 daemon 线程，启动后自行运行。
    """
    print("=" * 60)
    print("演示模式：启动采集节点 + 监控主机")
    print("=" * 60)
    if not HAS_QT:
        print("[错误] 需要 PyQt5。请先: pip install -r requirements.txt")
        sys.exit(1)

    from PyQt5.QtWidgets import QApplication

    from common.logger import setup_logger
    from common.theme import DARK_QSS
    from node import config as node_config
    from node.aggregator import DataAggregator
    from node.collectors import create_collectors, start_all
    from node.discovery import DiscoveryBroadcaster
    from node.tcp_server import MonitorTCPServer
    from host import config as host_config
    from host.gui.main_window import HostMainWindow

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)

    # ---- 采集节点后台（本机模拟一个被监控节点）----
    setup_logger("node")
    node_cfg = node_config.load_config()
    server = MonitorTCPServer(port=node_cfg["tcp_port"], token=node_cfg["token"])
    server.start()
    bcast = DiscoveryBroadcaster(
        tcp_port=node_cfg["tcp_port"], udp_port=node_cfg["udp_port"],
        token=node_cfg["token"],
        use_multicast=node_cfg.get("use_multicast", False),
        preferred_iface=node_cfg.get("preferred_iface", ""))
    bcast.start()
    collectors = create_collectors(node_cfg)
    start_all(collectors)
    agg = DataAggregator(server=server, collectors=collectors)
    agg.start()

    # ---- 监控主机主窗口（本机节点 + 自动连接已保存节点）----
    setup_logger("host")
    host_cfg = host_config.load_config()
    window = HostMainWindow(host_cfg)
    window.show()

    print("监控主机已启动。关闭窗口将退出整个演示。")
    sys.exit(app.exec_())


def main():
    print("=" * 60)
    print("P0-P3 自检脚本")
    print("=" * 60)
    if not HAS_QT:
        print("\n[警告] 未安装 PyQt5，信号相关验证将被跳过。")
        print("        请先: pip install -r requirements.txt\n")

    try:
        test_protocol()
        test_auth()
        test_connection()
        test_graceful_shutdown()
        test_client_config()
        test_collectors()
        test_discovery()
        test_quality_scorer()
    except Exception:
        import traceback
        traceback.print_exc()
        global FAIL
        FAIL += 1

    print("\n" + "=" * 60)
    print(f"结果: {PASS} 通过, {FAIL} 失败, {SKIP} 跳过")
    if FAIL:
        print("存在失败项，请检查上方输出。")
        sys.exit(1)
    if SKIP:
        print("有跳过项（缺 PyQt5），其余全部通过。")
        sys.exit(0)
    print("全部通过！数据链路正常。")
    sys.exit(0)


if __name__ == "__main__":
    # 支持 --demo：一条命令启动主机端 + 副机端 GUI 演示
    if "--demo" in sys.argv:
        run_demo()
    else:
        main()
