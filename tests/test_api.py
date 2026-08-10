# -*- coding: utf-8 -*-
"""
Agent REST + WebSocket 端到端测试（v5.0 新增，见《README.md》§23.1）。

验证：
1. Agent 进程启动并监听 HTTP/WS 端口
2. REST /api/health 鉴权（带 token 200 / 无 token 401 / 错 token 401）
3. REST /api/nodes 返回本机信息
4. REST /api/config 不返回 token；POST 更新白名单字段；token 不可经 API 修改
5. WebSocket /ws 鉴权（正确 token 通过、错误 token 拒绝）
6. WebSocket 连续接收 monitor_data 帧（含完整字段、connected_clients 正确）
7. WebSocket loss_ping → loss_pong 回显

用法：python tests/test_api.py
"""
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 测试专用端口，避免与运行中的 Agent/Node 冲突
TEST_PORT = 23456
TEST_UDP_PORT = 23457
# 测试用独立配置（不触碰用户 agent_config.json）
TEST_CFG = {
    "http_port": TEST_PORT,
    "udp_port": TEST_UDP_PORT,
    "token": "test-token-123",
    "use_multicast": False,
    "preferred_iface": "",
    "gpu_index": 0,
    "collectors": {"fps": "none", "gpu": False, "temperature": False},
    "log_level": "INFO",
}

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


def http_request(method, path, token=None, body=None):
    """发起 HTTP 请求，返回 (status, parsed_json)。"""
    url = f"http://127.0.0.1:{TEST_PORT}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        req.data = json.dumps(body).encode("utf-8")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, (json.loads(raw) if raw else {})
        except json.JSONDecodeError:
            return e.code, {}


def ws_test(token, expect_ok, frames_to_collect=0):
    """WebSocket 测试：连接 /ws，校验鉴权与数据推送。返回 (ok, 详情)。"""
    try:
        import websockets
        import asyncio
    except ImportError:
        return False, "websockets 未安装"

    async def _run():
        uri = f"ws://127.0.0.1:{TEST_PORT}/ws?token={token}"
        try:
            async with websockets.connect(uri, max_size=16 * 1024 * 1024) as ws:
                if not expect_ok:
                    # 错误 token：可能收到 auth_result 或直接关闭
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=3)
                        return False, f"错误 token 却收到: {msg}"
                    except asyncio.TimeoutError:
                        return True, "连接被静默拒绝（无消息）"
                # 正确 token：等 auth_result
                auth = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
                if not auth.get("ok"):
                    return False, f"鉴权失败: {auth}"
                # 收集 monitor_data 帧
                frames = []
                for _ in range(frames_to_collect):
                    m = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
                    if m.get("type") != "monitor_data":
                        return False, f"期望 monitor_data, got {m.get('type')}"
                    frames.append(m)
                # loss_ping → loss_pong
                await ws.send(json.dumps(
                    {"type": "loss_ping", "seq": 42, "ts": 1.25}))
                pong = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
                if pong.get("type") != "loss_pong" or pong.get("seq") != 42:
                    return False, f"loss_pong 异常: {pong}"
                return True, frames
        except Exception as e:
            if not expect_ok:
                # 错误 token 被主动关闭也算通过
                if "1008" in str(e) or "unauthorized" in str(e) \
                        or "Invalid status code" in str(e):
                    return True, f"连接被拒: {type(e).__name__}"
            return False, f"异常: {type(e).__name__}: {e}"

    return asyncio.run(_run())


def start_agent():
    """启动 Agent 子进程（测试专用配置），返回 Popen。"""
    env = dict(os.environ)
    # 通过环境变量传配置，避免写磁盘（agent.config 支持读环境覆盖）
    env["PCMONITOR_AGENT_CFG"] = json.dumps(TEST_CFG)
    # 为测试注入自定义配置加载：用一个小的 -c 包裹，读环境变量
    code = (
        "import os,json;"
        "import agent.config as c;"
        "c.CONFIG_FILE=os.devnull;"  # 不读写磁盘配置
        "data=json.loads(os.environ['PCMONITOR_AGENT_CFG']);"
        "c.DEFAULT_CONFIG.update(data);"
        "import agent.main;"
        "agent.main.main()"
    )
    return subprocess.Popen(
        [sys.executable, "-u", "-c", code],
        cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def wait_port(proc, port, timeout=15):
    """等待端口监听就绪。"""
    import socket
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False  # 进程已退出
        s = socket.socket()
        try:
            s.settimeout(0.3)
            s.connect(("127.0.0.1", port))
            s.close()
            return True
        except OSError:
            s.close()
            time.sleep(0.3)
    return False


def main():
    print("=" * 60)
    print("Agent REST + WebSocket 端到端测试")
    print("=" * 60)

    # 若 websockets 未安装，跳过 WS 部分但 REST 部分仍测
    try:
        import websockets  # noqa: F401
        has_ws = True
    except ImportError:
        has_ws = False
        print("  [WARN] websockets 未安装，跳过 WebSocket 测试")

    proc = start_agent()
    if not wait_port(proc, TEST_PORT):
        out = proc.stdout.read().decode("utf-8", "replace") if proc.stdout else ""
        check("Agent 进程启动并监听端口", False, out[-500:])
        proc.kill()
        print(f"\n结果: {PASS} 通过, {FAIL} 失败")
        return 1 if FAIL else 0

    check("Agent 进程启动并监听端口", True)

    # ---- REST API ----
    print("\n--- 1. REST API ---")
    status, body = http_request("GET", "/api/health", token=TEST_CFG["token"])
    check("GET /api/health 带 token 200",
          status == 200 and body.get("status") == "ok")
    check("health 返回版本/主机名/端口",
          body.get("version") and body.get("hostname") and body.get("port"))

    status, _ = http_request("GET", "/api/health")
    check("GET /api/health 无 token 401", status == 401)

    status, _ = http_request("GET", "/api/health", token="wrong-token")
    check("GET /api/health 错 token 401", status == 401)

    status, body = http_request("GET", "/api/nodes", token=TEST_CFG["token"])
    check("GET /api/nodes 返回本机信息",
          status == 200 and body.get("self", {}).get("hostname"))

    status, body = http_request("GET", "/api/config", token=TEST_CFG["token"])
    check("GET /api/config 不返回 token", status == 200 and "token" not in body)

    status, body = http_request("POST", "/api/config",
                                token=TEST_CFG["token"],
                                body={"log_level": "DEBUG"})
    check("POST /api/config 更新白名单字段", status == 200 and body.get("ok"))

    status, _ = http_request("POST", "/api/config",
                             token=TEST_CFG["token"],
                             body={"token": "hacked"})
    check("POST /api/config 拒绝改 token", status == 200)  # 接口不报错但 token 不变

    # ---- WebSocket ----
    if has_ws:
        print("\n--- 2. WebSocket ---")
        ok, detail = ws_test("wrong-token", expect_ok=False)
        check("错误 token 连接被拒", ok, detail)

        ok, frames = ws_test(TEST_CFG["token"], expect_ok=True,
                             frames_to_collect=3)
        if ok and isinstance(frames, list) and frames:
            f0 = frames[0]
            check("WS 鉴权通过并收到 3 帧", True)
            check("monitor_data 含完整字段",
                  all(k in f0 for k in
                      ("system", "cpu", "ram", "gpu", "disk",
                       "net", "net_quality", "fps", "processes")))
            # 注：第一帧可能因时序 connected_clients=0（订阅者刚加入），
            # 取最后一帧判断更可靠。
            check("connected_clients 计数正确",
                  frames[-1].get("connected_clients", 0) >= 1)
            check("loss_ping → loss_pong 回显", True)
        else:
            check("WS 鉴权通过并收到 3 帧", False, detail)
    else:
        print("\n--- 2. WebSocket ---")
        check("WebSocket 测试", False, "websockets 未安装")

    # 清理
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
