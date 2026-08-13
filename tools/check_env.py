# -*- coding: utf-8 -*-
"""
环境检测工具 —— 检查运行依赖与功能降级状态（v5.0 稳定性优化）。

用法：
    python tools/check_env.py

检测项：
    PyQt5           Host GUI（缺失 → GUI 不可用，仅后端可用）
    zeroconf        mDNS 自动发现（缺失 → 降级为仅 UDP 广播）
    wmi             温度/部分硬件采集（缺失 → 相关指标 N/A）
    pynvml          NVIDIA GPU 采集（缺失 → GPU 降级 N/A）
    PresentMon.exe  精准帧率（缺失 → 降级 DXGI 截帧）
    websockets      Agent WS 服务端
    aiohttp         Agent REST 服务端
    websocket-client Host WS 客户端
"""
import importlib
import json
import os
import socket
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 需检测的库 → (包名, 功能说明, 缺失时影响)
LIBS = [
    ("PyQt5",            "Host GUI（集中监控大屏）",       "GUI 不可用，仅后端服务可用"),
    ("zeroconf",         "mDNS 零配置自动发现",            "降级为仅 UDP 广播自动发现"),
    ("wmi",              "WMI 硬件采集（温度/盘符映射）",   "温度/盘符映射等指标 N/A"),
    ("pynvml",           "NVIDIA GPU 采集（NVML）",        "GPU 指标降级 N/A"),
    ("websockets",       "Agent WebSocket 服务端",         "Agent WS 推送不可用"),
    ("aiohttp",          "Agent REST 服务端",              "Agent REST API 不可用"),
    ("websocket",        "Host WS 客户端（websocket-client）", "Host 无法订阅 Agent"),
    ("psutil",           "核心采集（CPU/内存/磁盘/网络）",  "基础采集全部不可用"),
]


def check_libs() -> list:
    """检测各库是否可用，返回结果列表。"""
    results = []
    for mod, desc, impact in LIBS:
        try:
            importlib.import_module(mod)
            results.append({"name": mod, "desc": desc, "ok": True,
                            "impact": ""})
        except ImportError:
            results.append({"name": mod, "desc": desc, "ok": False,
                            "impact": impact})
    return results


def check_presentmon() -> dict:
    """检测 PresentMon.exe 是否存在。"""
    path = os.path.join(ROOT, "tools", "PresentMon.exe")
    return {
        "name": "PresentMon.exe",
        "desc": "精准帧率采集（PresentMon CLI）",
        "ok": os.path.exists(path),
        "impact": "降级为 DXGI 截帧（dxcam）或帧率 N/A" if not os.path.exists(path) else "",
    }


def check_platform() -> str:
    """返回平台。"""
    return sys.platform


def summarize(results: list) -> dict:
    """汇总功能降级状态。"""
    degraded = [r["name"] for r in results if not r["ok"]]
    return {
        "platform": sys.platform,
        "python": sys.version.split()[0],
        "hostname": socket.gethostname(),
        "available": sum(1 for r in results if r["ok"]),
        "missing": len(results) - sum(1 for r in results if r["ok"]),
        "degraded_features": degraded,
    }


def main() -> int:
    print("=" * 60)
    print("LAN PC Monitor 环境检测")
    print("=" * 60)
    print(f"平台: {sys.platform}  Python: {sys.version.split()[0]}")
    print(f"主机名: {socket.gethostname()}\n")

    results = check_libs()
    results.append(check_presentmon())

    print("--- 依赖与功能 ---")
    for r in results:
        mark = "✅" if r["ok"] else "❌"
        line = f"  {mark} {r['name']:<18} {r['desc']}"
        if not r["ok"]:
            line += f"  → {r['impact']}"
        print(line)

    summary = summarize(results)
    print("\n--- 汇总 ---")
    print(f"  可用: {summary['available']}/{len(results)}")
    if summary["missing"]:
        print(f"  缺失: {summary['missing']}（功能降级）")
        for feat in summary["degraded_features"]:
            print(f"    - {feat}")
    else:
        print("  全部依赖可用，无功能降级")

    # 输出 JSON（供脚本/CI 消费）
    print("\n--- JSON ---")
    print(json.dumps({"summary": summary,
                      "checks": [{"name": r["name"], "ok": r["ok"],
                                  "impact": r["impact"]} for r in results]},
                     ensure_ascii=False, indent=2))

    # 缺失任何必需核心依赖（psutil）→ 退出码 1
    core_missing = any(r["name"] == "psutil" and not r["ok"] for r in results)
    return 1 if core_missing else 0


if __name__ == "__main__":
    sys.exit(main())
