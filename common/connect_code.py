# -*- coding: utf-8 -*-
"""
便捷连接工具（见《技术文档.md》§23.2-23.4）。

提供：
- make_connect_code / resolve_connect_code：连接码（PCM-XXXX-XXXX）生成与反查
- parse_connect_uri：剪贴板连接串（pcmonitor://）解析
- export_config / import_config：.pcm 配置文件导入导出（token Base64+XOR 混淆）

全部为标准库实现，不依赖第三方库，便于在无 GUI 环境测试。
"""
import base64
import datetime
import hashlib
import json
import os
from urllib.parse import urlparse, parse_qs

# ---------------------------------------------------------------------------
# 连接码（§23.2）
# ---------------------------------------------------------------------------

def make_connect_code(ip: str, port: int, token: str) -> str:
    """
    生成连接码：PCM-XXXX-XXXX。
    编码 ip:port:token 的 SHA-256 前 8 位，不含明文地址。
    """
    raw = f"{ip}:{port}:{token}"
    digest = hashlib.sha256(raw.encode()).hexdigest().upper()
    return f"PCM-{digest[:4]}-{digest[4:8]}"


def resolve_connect_code(code: str, candidates: dict) -> dict | None:
    """
    在本地发现候选节点中反查匹配项（§23.2）。

    :param code:        用户输入的连接码（如 PCM-8A3B-9F2C）
    :param candidates:  本地 mDNS/UDP 发现的候选节点
                        {ip: {"port":..., "token":..., "hostname":..., ...}}
    :return: {"ip":..., **info} 匹配项；无匹配返回 None
    """
    code = code.strip().upper()
    for ip, info in candidates.items():
        port = info.get("port") or info.get("tcp_port")
        token = info.get("token", "")
        if port and make_connect_code(ip, port, token) == code:
            return {"ip": ip, **info}
    return None


# ---------------------------------------------------------------------------
# 剪贴板连接串（§23.3）
# ---------------------------------------------------------------------------

def parse_connect_uri(text: str) -> dict | None:
    """
    解析 pcmonitor:// 连接串，失败返回 None。

    格式：pcmonitor://<ip>:<port>?token=<token>&alias=<别名>（URL 编码别名）
    """
    try:
        u = urlparse(text.strip())
        if u.scheme != "pcmonitor":
            return None
        q = parse_qs(u.query)
        return {
            "ip": u.hostname,
            "port": u.port or 12345,
            "token": (q.get("token") or [""])[0],
            "alias": (q.get("alias") or [""])[0],
        }
    except Exception:
        return None


def make_connect_uri(ip: str, port: int, token: str, alias: str = "") -> str:
    """
    生成 pcmonitor:// 连接串（供节点端"复制连接串"功能）。
    """
    from urllib.parse import quote
    alias_q = f"&alias={quote(alias)}" if alias else ""
    return f"pcmonitor://{ip}:{port}?token={token}{alias_q}"


# ---------------------------------------------------------------------------
# .pcm 配置文件（§23.4）
# ---------------------------------------------------------------------------

# 简单 XOR 密钥（本地混淆用，非高强度加密）
_XOR_KEY = 0x5A


def _obfuscate(text: str) -> str:
    """token 混淆：Base64 + XOR（§23.4，防明文泄露）。"""
    data = text.encode("utf-8")
    xored = bytes(b ^ _XOR_KEY for b in data)
    return base64.b64encode(xored).decode("ascii")


def _deobfuscate(enc: str) -> str:
    """token 反混淆。"""
    try:
        data = base64.b64decode(enc)
        xored = bytes(b ^ _XOR_KEY for b in data)
        return xored.decode("utf-8")
    except Exception:
        return ""


def export_config(nodes: list, path: str) -> bool:
    """
    导出节点配置到 .pcm 文件（§23.4）。

    :param nodes: [{"node_id","ip","port","token","alias"}, ...]
    :param path:  目标文件路径
    :return: 成功返回 True
    """
    try:
        payload = {
            "format": "pcmonitor-config",
            "version": 1,
            "exported_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "nodes": [
                {
                    "alias": n.get("alias", ""),
                    "ip": n.get("ip", ""),
                    "port": n.get("port", 12345),
                    "token_enc": _obfuscate(n.get("token", "")),
                }
                for n in nodes
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def import_config(path: str) -> list | None:
    """
    导入 .pcm 配置文件（§23.4）。

    :param path: .pcm 文件路径
    :return: [{"ip","port","token","alias"}, ...]；校验失败返回 None
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("format") != "pcmonitor-config" or data.get("version") != 1:
            return None
        nodes = []
        for n in data.get("nodes", []):
            nodes.append({
                "ip": n.get("ip", ""),
                "port": n.get("port", 12345),
                "token": _deobfuscate(n.get("token_enc", "")),
                "alias": n.get("alias", ""),
            })
        return nodes
    except Exception:
        return None
