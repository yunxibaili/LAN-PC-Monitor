# -*- coding: utf-8 -*-
"""
通用工具模块。

提供：单位换算、局域网 IP 选取（多网卡场景）、host_id 生成等。
"""
import hashlib
import socket

try:
    import netifaces
except ImportError:  # 未安装时降级为 socket 探测法
    netifaces = None


def bytes_to_mb(value: float) -> float:
    """字节数 → MB，保留 2 位小数。"""
    return round(value / 1024 / 1024, 2)


def bytes_to_gb(value: float) -> float:
    """字节数 → GB，保留 2 位小数。"""
    return round(value / 1024 / 1024 / 1024, 2)


def bits_to_mbps(value: float) -> float:
    """比特每秒 → Mbps，保留 2 位小数。"""
    return round(value / 1024 / 1024, 2)


def format_uptime(seconds: float) -> str:
    """秒数 → "Xd HH:MM:SS" 人类可读格式。"""
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{days}d {hours:02d}:{minutes:02d}:{secs:02d}"


def get_lan_ip(preferred_iface: str = "") -> str:
    """
    获取局域网 IP，过滤虚拟网卡（见《技术文档.md》§18.8）。

    优先级：
    1. 指定 preferred_iface（网卡名）时，返回该网卡 IP；
    2. 遍历所有网卡，排除回环/虚拟/VPN，取私网段 IP；
    3. 多个候选时优先有线(Ethernet/以太网)，其次无线(Wi-Fi)；
    4. 全部失败时兜底 UDP 连接 8.8.8.8 取出口 IP。

    :param preferred_iface: 首选网卡名（如 "以太网"），空串表示自动
    :return: 局域网 IP 字符串
    """
    if netifaces is not None:
        candidates = []  # (iface, ip)
        for iface in netifaces.interfaces():
            try:
                addrs = netifaces.ifaddresses(iface)
            except Exception:
                continue
            inet = addrs.get(netifaces.AF_INET, [])
            for a in inet:
                ip = a.get("addr", "")
                if not ip or ip.startswith("127."):
                    continue
                # 仅接受私网段
                if not (ip.startswith("192.168.") or ip.startswith("10.")
                        or ip.startswith("172.")):
                    continue
                # 排除常见虚拟网卡
                name_lower = iface.lower()
                if any(k in name_lower for k in
                       ["virtual", "vmware", "hyper-v", "wsl", "docker",
                        "vethernet", "loopback"]):
                    continue
                candidates.append((iface, ip))

        if preferred_iface:
            for iface, ip in candidates:
                if preferred_iface in iface:
                    return ip
        if candidates:
            # 优先有线网卡
            for iface, ip in candidates:
                if any(k in iface.lower() for k in
                       ["ethernet", "以太网", "local area"]):
                    return ip
            return candidates[0][1]

    # 兜底：UDP 连接法（无需实际发包，仅取出口 IP）
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def make_host_id(ip: str, port: int) -> str:
    """根据 IP+端口生成 8 位 host_id（见《技术文档.md》§12.2）。"""
    return hashlib.md5(f"{ip}:{port}".encode()).hexdigest()[:8]


def generate_token() -> str:
    """生成随机 token（基于 uuid4 去除连字符，取 12 位），防误连。"""
    import uuid
    return uuid.uuid4().hex[:12]


def check_port_in_use(port: int, proto: str = "tcp") -> bool:
    """
    检测端口是否被占用（§5.1 步骤 5：端口占用检测）。

    :param port:  端口号
    :param proto: "tcp" 或 "udp"
    :return: 被占用返回 True
    """
    try:
        if proto == "udp":
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", port))
        s.close()
        return False
    except OSError:
        return True


def get_local_node_info() -> dict:
    """
    读取本机采集节点配置（node_config.json），返回连接所需信息。

    用于副机端/主机端"一键添加本机节点"，省去手动填 IP/端口/token。
    :return: {"ip":..., "port":..., "token":..., "alias":...}；
             文件不存在或解析失败返回空 dict。
    """
    import json
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_file = os.path.join(root, "node_config.json")
    try:
        with open(cfg_file, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return {
            "ip": get_lan_ip(cfg.get("preferred_iface", "")),
            "port": cfg.get("tcp_port", 12345),
            "token": cfg.get("token", ""),
            "alias": socket.gethostname(),
        }
    except Exception:
        return {}


def get_default_gateway() -> str:
    """
    获取默认网关 IP（用于网关延迟测量，见《技术文档.md》§8.6）。

    Windows 下优先用 route print 解析；失败时用 netifaces.gateways()。
    :return: 网关 IP 字符串；获取失败返回空串
    """
    # 优先 netifaces.gateways()（跨平台，无子进程）
    if netifaces is not None:
        try:
            gateways = netifaces.gateways()
            default = gateways.get("default", {})
            if netifaces.AF_INET in default:
                return default[netifaces.AF_INET][0]
        except Exception:
            pass
    # Windows 兜底：route print 解析
    try:
        import subprocess
        out = subprocess.run(["route", "print", "0.0.0.0"],
                             capture_output=True, text=True, timeout=5).stdout
        for line in out.splitlines():
            # 匹配 0.0.0.0 目标行的网关列（兼容中英文，首列 0.0.0.0）
            parts = line.split()
            if len(parts) >= 3 and parts[0] == "0.0.0.0" and \
                    parts[1] == "0.0.0.0":
                return parts[2]
    except Exception:
        pass
    return ""


def parse_ping_output(output: str) -> float:
    """
    解析系统 ping 命令输出，提取 RTT 毫秒（兼容中英文，§8.6 增强点 #23）。

    中文：时间=2ms   /  时间<1ms
    英文：time=2ms   /  time<1ms
    匹配第一条有效 RTT 值。
    :param output: ping 命令 stdout
    :return: RTT 毫秒；解析失败返回 None
    """
    import re
    # 中文"时间="与英文"time="，匹配 <xms 或 =xms 或 =x.xx ms
    patterns = [
        r"时间\s*[=<]\s*([\d.]+)\s*ms",
        r"time\s*[=<]\s*([\d.]+)\s*ms",
        r"时间\s*=\s*([\d.]+)\s*毫秒",
        r"time\s*=\s*([\d.]+)\s*ms",
    ]
    for pat in patterns:
        m = re.search(pat, output, re.IGNORECASE)
        if m:
            return float(m.group(1))
    return None


def ping_gateway(gateway: str = "", timeout: float = 3.0) -> float:
    """
    对默认网关执行系统 ping，返回 RTT 毫秒（免提权，见《技术文档.md》§15.4）。

    :param gateway: 网关 IP；空串时自动探测
    :param timeout: 超时秒数
    :return: RTT 毫秒；失败返回 None
    """
    import subprocess
    gw = gateway or get_default_gateway()
    if not gw:
        return None
    try:
        out = subprocess.run(
            ["ping", "-n", "1", "-w", str(int(timeout * 1000)), gw],
            capture_output=True, text=True, timeout=timeout + 2).stdout
        return parse_ping_output(out)
    except Exception:
        return None
