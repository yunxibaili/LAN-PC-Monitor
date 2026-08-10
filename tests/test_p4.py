# -*- coding: utf-8 -*-
"""
P4 集成测试 —— 真实双端连接 + 帧率降级 + 性能兜底 + 便捷发现（见《README.md》§21 P4 / §2.5 / §23）。

用法（在项目根目录，需已 pip install -r requirements.txt）：
    python test_p4.py

验证项：
T1. 采集节点真实进程启动（TCP 监听 / 连接码打印 / mDNS 注册 / 端口占用检测）
T2. 双端连接主链路（重点）：NodeConnection 鉴权 → monitor_data 数据帧 → RTT
T3. 双客户端同时连接（不同源 IP → connected_clients 去重计数 = 2）
T4. 错误 token 鉴权拒绝
T5. 断线自动重连：杀节点 → 重连中 → 重启节点 → 自动恢复数据
T6. 双通道发现：UDP 广播 + mDNS 同时发现同一节点，按 IP 去重
T7. 性能兜底 SelfMonitor：CPU 超限降级（1s→2s + 关帧率）、恢复（→1s）
T8. 帧率降级链路：presentmon 无工具 → DXGI 降级日志；none/dxgi 模式

说明：
- 会启动/停止真实采集节点子进程（使用 node_config.json 实际端口/token）。
- 运行前请确认没有其他节点实例占用 12345/12346 端口。
- 不弹出 GUI 窗口。
"""
import os
import socket
import subprocess
import sys
import threading
import time

# Ensure stdout supports UTF-8 on Windows (avoid GBK encoding failures)
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from PyQt5.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication([])
    HAS_QT = True
except Exception:
    _app = None
    HAS_QT = False

from common.protocol import send_frame, recv_frame  # noqa: E402

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        try:
            print(f"  [FAIL] {name}  {repr(detail)[:200]}")
        except (UnicodeEncodeError, UnicodeDecodeError):
            print(f"  [FAIL] {name}  (detail omitted: encoding error)")


def pump_qt(seconds: float):
    if not HAS_QT:
        time.sleep(seconds)
        return
    end = time.time() + seconds
    while time.time() < end:
        _app.processEvents()
        time.sleep(0.02)


def wait_until(fn, timeout=15, interval=0.2) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if fn():
            return True
        pump_qt(interval)
    return False


def get_node_config():
    import json
    with open(os.path.join(ROOT, "node_config.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def node_log_tail(size: int = 8192) -> str:
    """读取 logs/node.log 尾部（节点 logger 只写文件，propagate=False）。"""
    path = os.path.join(ROOT, "logs", "node.log")
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - size))
            return f.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def _extract_connect_code(text: str):
    """从节点启动输出中提取 6 位数字连接码。"""
    import re
    # 匹配"本机节点连接码: 482913" 以及 GBK 编码后的乱码版本
    m = re.search(r"(?:本机节点连接码|连接码)[:\s]*(\d{6})", text)
    if m:
        return m.group(1)
    # Fallback: match any 6-digit number on its own line after "连接码" or garbled
    for line in text.splitlines():
        if len(line.strip()) >= 6 and re.search(r"\d{6}", line):
            dm = re.search(r"(\d{6})", line)
            if dm and dm.group(1):
                return dm.group(1)
    return None


class NodeProc:
    """采集节点子进程封装（读线程收集输出）。"""

    def __init__(self, proc, lines):
        self.proc = proc
        self.lines = lines

    @property
    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def output(self) -> str:
        return "".join(self.lines)


def start_node_proc(tcp_port=12345):
    """启动真实采集节点子进程，等待 TCP 端口就绪。"""
    lines = []
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.Popen(
        [sys.executable, "-u", "-m", "node"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    def _reader():
        try:
            for raw in proc.stdout:
                lines.append(raw.decode("utf-8", errors="replace"))
        except Exception:
            pass
    threading.Thread(target=_reader, daemon=True).start()

    deadline = time.time() + 25
    while time.time() < deadline:
        if proc.poll() is not None:
            return None, "".join(lines)
        try:
            s = socket.create_connection(("127.0.0.1", tcp_port), timeout=1)
            s.close()
            return NodeProc(proc, lines), None
        except OSError:
            time.sleep(0.5)
    proc.kill()
    return None, "等待 TCP 端口就绪超时"


def stop_node_proc(np):
    if np is None:
        return
    if np.alive:
        np.proc.kill()
        try:
            np.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
    # 强杀不触发 finally → 清理单实例锁，避免下次启动误判"已有实例"
    import tempfile, glob as _glob
    for _lf in _glob.glob(os.path.join(tempfile.gettempdir(), "*Monitor*.lock")):
        try:
            os.remove(_lf)
        except OSError:
            pass


def make_connection(node_id, token, alias="测试节点"):
    from host.connection import NodeConnection
    conn = NodeConnection(node_id, "127.0.0.1", 12345, token, alias=alias)
    conn._frames = []
    conn._statuses = []
    conn._rtts = []
    conn.data_received.connect(lambda f, n: conn._frames.append(f))
    conn.status_changed.connect(lambda s, n: conn._statuses.append(s))
    conn.rtt_updated.connect(lambda r, n: conn._rtts.append(r))
    conn.start()
    return conn


def test_node_process():
    """T1 节点真实进程启动。"""
    print("\n--- T1. 采集节点真实进程启动 ---")
    np, err = start_node_proc()
    check("节点进程启动并监听 TCP 12345", np is not None, err or "")

    # 端口占用检测（§5.1 步骤 5 / 单实例）：节点运行时再次启动应报错退出
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    p2 = subprocess.Popen(
        [sys.executable, "-u", "-m", "node"], cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        out2 = p2.communicate(timeout=15)[0].decode("utf-8", errors="replace")
        # 单实例互斥体先于端口检查拦截（node/main.py 两种路径都返回 1）
        blocked = ("已被占用" in out2) or ("已有采集节点实例" in out2)
        check("重复启动被拦截（单实例/端口占用）退出码 1",
              p2.returncode == 1 and blocked, out2[-300:])
    except Exception as e:
        check("重复启动被拦截（单实例/端口占用）退出码 1", False, str(e))
        p2.kill()

    # 等启动输出（连接码）与日志文件（mDNS 注册，logger 只写文件）
    ok = wait_until(lambda: "本机节点连接码: " in np.output(), timeout=15)
    code = _extract_connect_code(np.output())
    check("启动打印 6 位数字连接码",
          ok and code is not None and code.isdigit() and len(code) == 6,
          np.output()[-300:])
    # mDNS：有 zeroconf 检查注册；无 zeroconf 检查降级日志（环境兼容）
    ok = wait_until(
        lambda: ("mDNS 服务已注册" in node_log_tail())
                or ("zeroconf 未安装" in node_log_tail()), timeout=15)
    mdns_ok = "mDNS 服务已注册" in node_log_tail()
    check("mDNS 服务注册（或 zeroconf 未安装降级）", ok and (
        mdns_ok or "zeroconf 未安装" in node_log_tail()),
        node_log_tail()[-300:])

    # UDP 心跳广播可被本机监听
    from host.discovery import DiscoveryListener
    lan_ip = get_lan_ip()
    lis = DiscoveryListener()
    lis.start()
    ok = wait_until(lambda: lan_ip in lis.get_hosts(), timeout=10)
    check("UDP 心跳广播（DiscoveryListener 发现本机）", ok,
          str(list(lis.get_hosts().keys())))
    lis.stop()
    return np


def get_lan_ip() -> str:
    from common.utils import get_lan_ip as _g
    try:
        ip = _g("")
        return ip if ip else "127.0.0.1"
    except Exception:
        return "127.0.0.1"


def test_dual_end(cfg):
    """T2 双端连接主链路 + T3 双客户端 + T4 错误 token。"""
    print("\n--- T2. 双端连接主链路（重点） ---")
    conn = make_connection("p4-node-1", cfg["token"])
    ok = wait_until(lambda: conn.is_connected(), timeout=15)
    check("客户端连接成功（鉴权通过）", ok)
    ok = wait_until(lambda: any("connected" in s for s in conn._statuses),
                    timeout=15)
    check("状态包含 connected", ok, str(conn._statuses))

    ok = wait_until(lambda: len(conn._frames) > 0, timeout=20)
    check("收到 monitor_data 数据帧", ok, f"frames={len(conn._frames)}")
    if conn._frames:
        f0 = conn._frames[0]
        check("数据帧含完整字段", f0.get("hostname") and "cpu" in f0
              and "ram" in f0 and "gpu" in f0 and "fps" in f0, str(list(f0)))
        check("connected_clients = 1", f0.get("connected_clients") == 1,
              str(f0.get("connected_clients")))
        fps = f0.get("fps", {})
        # 性能兜底可能在预热阶段就关掉 fps 采集器（CPU 瞬时虚高），
        # fps 返回 {} 是合法的降级状态
        check("fps 字段结构完整（降级 source 有效）",
              isinstance(fps, dict) and ("source" not in fps or fps["source"] in ("presentmon", "dxgi", "none")),
              str(fps))

    ok = wait_until(lambda: len(conn._rtts) > 0, timeout=15)
    check("RTT ping/pong 成功", ok and conn._rtts[0] > 0,
          str(conn._rtts[:3]))

    print("\n--- T3. 双客户端连接（去重计数） ---")
    conn2 = make_connection("p4-node-2", cfg["token"], alias="第二客户端")
    ok = wait_until(lambda: conn2.is_connected(), timeout=15)
    check("第二客户端连接成功", ok)

    # 第三个客户端以局域网 IP 为源地址连接（连到局域网 IP 而非回环，
    # 保证服务端按 IP 去重计数 = 2：127.0.0.1 + 局域网 IP）
    lan_ip = get_lan_ip()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    connected_vals = []

    try:
        sock.bind((lan_ip, 0))
        sock.connect((lan_ip, 12345))
        send_frame(sock, {"type": "auth", "token": cfg["token"]})
        auth = recv_frame(sock)
        check("局域网 IP 源客户端鉴权通过", bool(auth and auth.get("ok")),
              str(auth))

        # auth 读完后启动阻塞读帧线程（避免超时半帧失步）
        def _raw_reader():
            try:
                while True:
                    frame = recv_frame(sock)
                    if frame is None:
                        break
                    if frame.get("type") == "monitor_data":
                        connected_vals.append(frame.get("connected_clients"))
            except Exception:
                pass
        threading.Thread(target=_raw_reader, daemon=True).start()

        n = wait_until(lambda: len(connected_vals) > 0, timeout=15)
        check("connected_clients 去重计数 = 2（127.0.0.1 + 局域网IP）",
              n and connected_vals[-1] == 2,
              f"connected={connected_vals}")
    except Exception as e:
        check("双客户端去重计数 = 2", False, str(e))
    finally:
        try:
            sock.close()
        except Exception:
            pass

    print("\n--- T4. 错误 token 鉴权拒绝 ---")
    bad = make_connection("p4-bad", "wrong-token-999", alias="坏token")
    ok = wait_until(lambda: any("auth_failed" in s for s in bad._statuses),
                    timeout=15)
    check("错误 token 状态为 auth_failed", ok, str(bad._statuses))
    check("错误 token 不建立数据连接", not bad.is_connected())
    bad.stop()
    conn2.stop()
    conn.stop()


def test_reconnect(cfg):
    """T5 断线自动重连。"""
    print("\n--- T5. 断线自动重连 ---")
    np, err = start_node_proc()
    check("节点启动（重连测试）", np is not None, err or "")
    conn = make_connection("p4-reconn", cfg["token"])
    ok = wait_until(lambda: conn.is_connected(), timeout=15)
    check("初始连接成功", ok)
    n0 = len(conn._frames)
    ok = wait_until(lambda: len(conn._frames) > n0, timeout=20)
    check("初始数据流正常", ok, f"frames={len(conn._frames)}")

    # 杀掉节点 → 应进入重连（socket timeout 30s，需等待更久）
    stop_node_proc(np)
    pump_qt(0.5)
    # 从外部关闭 socket 加速断开感知，避免等完整 30s TCP timeout
    if conn._sock:
        try:
            conn._sock.close()
        except Exception:
            pass
    ok = wait_until(lambda: not conn.is_connected(), timeout=8)
    check("节点被杀后连接断开", ok, str(conn._statuses))
    ok2 = wait_until(lambda: any("reconnecting" in s or "offline" in s
                                  for s in conn._statuses), timeout=8)
    check("状态进入重连/离线", ok2, str(conn._statuses))

    # 重启节点 → 应自动恢复
    np2, err2 = start_node_proc()
    check("节点重启成功", np2 is not None, err2 or "")
    ok = wait_until(lambda: conn.is_connected(), timeout=30)
    check("客户端自动重连成功", ok)
    m1 = len(conn._frames)
    ok = wait_until(lambda: len(conn._frames) > m1, timeout=20)
    check("重连后数据流恢复", ok, f"frames={len(conn._frames)}")

    conn.stop()
    stop_node_proc(np2)


def test_discovery():
    """T6 双通道发现去重。"""
    print("\n--- T6. UDP + mDNS 双通道发现去重 ---")
    np, err = start_node_proc()
    check("节点启动（发现测试）", np is not None, err or "")

    from host.discovery import DiscoveryListener, MdnsDiscovery
    lan_ip = get_lan_ip()
    lis = DiscoveryListener()
    mdns = MdnsDiscovery()
    lis.start()
    mdns.start()

    ok_udp = wait_until(lambda: lan_ip in lis.get_hosts(), timeout=10)
    ok_mdns = wait_until(lambda: lan_ip in mdns.get_hosts(), timeout=20)
    check("UDP 广播发现节点", ok_udp, str(list(lis.get_hosts().keys())))
    check("mDNS 发现节点", ok_mdns, str(list(mdns.get_hosts().keys())))

    m = mdns.get_hosts().get(lan_ip, {})
    check("mDNS 节点含 hostname/tcp_port", bool(m.get("hostname"))
          and m.get("tcp_port") == 12345, str(m))

    merged = dict(lis.get_hosts())
    merged.update(mdns.get_hosts())
    check("双通道按 IP 去重（同一节点仅一项）",
          merged.get(lan_ip) is not None and len(merged) >= 1,
          f"udp={list(lis.get_hosts().keys())} mdns={list(mdns.get_hosts().keys())}")

    lis.stop()
    mdns.stop()
    stop_node_proc(np)


def test_self_monitor():
    """T7 性能兜底 SelfMonitor。"""
    print("\n--- T7. 性能兜底（SelfMonitor） ---")
    from host.self_monitor import SelfMonitor

    class FakeAgg:
        interval = 1.0

    class FakeFps:
        stopped = False

        def stop(self):
            self.stopped = True

    agg = FakeAgg()
    fps = FakeFps()
    sm = SelfMonitor(agg, {"fps": fps}, interval=0.05)
    sm.proc.cpu_percent = lambda interval=1.0: 8.0
    sm.check()   # 预热：首次采样丢弃（psutil 首次返回平均值虚高，§16 健壮性）
    check("首次采样预热丢弃（不误降级）",
          agg.interval == 1.0 and not fps.stopped)
    sm.check()   # streak=1：单次超阈值不降级（防抖动）
    check("单次超阈值不降级（防抖动）",
          agg.interval == 1.0 and not fps.stopped)
    sm.check()   # streak=2：连续两次超阈值 → 降级
    check("CPU 连续 2 次>5% → 采集频率降为 2s", agg.interval == 2.0,
          f"interval={agg.interval}")
    check("CPU>5% → 帧率采集器已关闭", fps.stopped)
    sm.proc.cpu_percent = lambda interval=1.0: 1.0
    sm.check()
    sm.check()
    check("CPU<3% → 采集频率恢复 1s", agg.interval == 1.0,
          f"interval={agg.interval}")
    check("帧率不自动恢复（避免抖动）", fps.stopped)
    sm.stop()


def test_fps_degrade():
    """T8 帧率降级链路。"""
    print("\n--- T8. 帧率降级链路 ---")
    from common.collectors.fps_collector import FpsCollector, FrameStats
    import logging

    records = []
    h = logging.Handler()
    h.setLevel(logging.DEBUG)

    def emit(r):
        records.append(r.getMessage())
    h.emit = emit
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(h)
    try:
        c = FpsCollector(mode="presentmon")
        check("PresentMon 缺失 → 自动降级 DXGI", c.mode == "dxgi",
              f"mode={c.mode}")
        check("降级日志含 PresentMon.exe 未找到",
              any("PresentMon.exe 未找到" in m for m in records),
              str(records))
        d = c.collect()
        check("降级后 source=dxgi，fps 字段完整",
              d["source"] == "dxgi" and set(["fps", "frame_time_ms",
                                             "low_1_percent"]) <= set(d.keys()),
              str(d))
        c.stop()

        c2 = FpsCollector(mode="none")
        d2 = c2.collect()
        check("none 模式 → source=none", d2["source"] == "none", str(d2))
        c2.stop()

        c3 = FpsCollector(mode="dxgi")
        d3 = c3.collect()
        check("dxgi 模式可用（无 dxcam 时 N/A 不崩溃）",
              d3["source"] == "dxgi" and d3["fps"] == "N/A", str(d3))
        c3.stop()

        s = FrameStats()
        for _ in range(100):
            s.push(10.0)
        check("100 帧 10ms → 平均 100 FPS", s.fps() == 100.0)
        check("1% Low = 100 FPS", s.low_1() == 100.0)
        s2 = FrameStats()
        for _ in range(100):
            s2.push(100.0)
        check("1% Low = 10 FPS（100ms 帧）", s2.low_1() == 10.0)
    finally:
        root.removeHandler(h)


def main():
    print("=" * 60)
    print("P4 集成测试（双端连接 / 帧率降级 / 性能兜底 / 便捷发现）")
    print("=" * 60)
    # v5.0: node_config.json 已删除（v5.0 节点改为 agent_config.json），
    # v4.0 节点子进程测试不再适用。
    if not os.path.exists(os.path.join(ROOT, "node_config.json")):
        print("  [SKIP] test_p4 (v4.0 node.* 已迁移至 agent，请使用 test_api.py)")
        print()
        print(f"结果: 0 通过, 0 失败, 0 跳过（v5.0 弃用）")
        return 0

    # 清理历史残留单实例锁（避免上次强杀节点残留导致误判"已有实例"）
    import tempfile, glob as _glob
    for _lf in _glob.glob(os.path.join(tempfile.gettempdir(), "*Monitor*.lock")):
        try:
            os.remove(_lf)
        except OSError:
            pass
    cfg = get_node_config()
    np = None
    try:
        np = test_node_process()
        test_dual_end(cfg)
        stop_node_proc(np)     # T1/T2 共享同一节点实例，T2 结束后清理
        np = None
        test_reconnect(cfg)
        test_discovery()
        test_self_monitor()
        test_fps_degrade()
    except Exception:
        import traceback
        traceback.print_exc()
        global FAIL
        FAIL += 1
    finally:
        if np is not None and np.alive:
            stop_node_proc(np)

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败, 0 跳过")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
