# -*- coding: utf-8 -*-
"""
test_v52_node_detail_vm.py —— NodeDetailViewModel 单元测试（v5.2 Phase 3-3A）。

测试重点（审查建议）：
1. 完整字段映射：monitor_data 43 字段 -> NodeDetailData
2. 节点隔离：node_A 变化不影响 node_B
3. 空数据：GPU 不存在 -> gpu.usage=None（非 0）
4. 删除：NodeStore.remove -> cache 删除 -> data_removed 信号
5. 缓存：frame1 创建，frame2 更新同一对象
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from host.store.frame_store import FrameStore
from host.store.node_store import NodeStore
from host.viewmodels.node_detail_vm import (
    NodeDetailViewModel, NodeDetailData, _safe_float, _safe_int,
)

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


def full_frame():
    """构造完整 monitor_data 帧（43 字段全覆盖）。"""
    return {
        "type": "monitor_data", "ts": time.time(),
        "hostname": "DESKTOP-TEST", "connected_clients": 2,
        "system": {"hostname": "DESKTOP-TEST", "local_ip": "192.168.1.100",
                   "uptime_seconds": 3661},
        "cpu": {"name": "Ryzen 9", "total_usage": 45.2,
                "physical_cores": 8, "logical_cores": 16,
                "core_freq_mhz": 4500, "package_temp_c": 65.0,
                "power_w": 65.0, "per_core_usage": [40, 50, 45, 55, 30, 60, 42, 48]},
        "ram": {"total_gb": 32.0, "used_gb": 15.9, "available_gb": 16.1,
                "usage_percent": 49.8, "swap_used_mb": 1200.0},
        "gpu": {"name": "RTX 4070", "usage_percent": 62.1,
                "vram_used_mb": 8192, "vram_total_mb": 12288,
                "core_temp_c": 71.0, "hotspot_temp_c": 82.0,
                "core_freq_mhz": 2400, "power_w": 185.0,
                "engine_usage": {"graphics": 48, "compute": 12}},
        "disk": [
            {"drive": "C:", "read_mb_s": 120.0, "write_mb_s": 85.0,
             "usage_percent": 78.0, "free_gb": 45.0, "queue_depth": 2.5},
            {"drive": "D:", "read_mb_s": 30.0, "write_mb_s": 210.0,
             "usage_percent": 52.0, "free_gb": 230.0, "queue_depth": 1.0},
        ],
        "net": {"interface": "以太网", "upload_mb_s": 12.3,
                "download_mb_s": 45.6, "link_speed_mbps": 1000,
                "errors_sent": 0, "errors_recv": 0},
        "net_quality": {"latency_to_client_ms": 0.45,
                        "latency_to_gateway_ms": 1.2,
                        "packet_loss_percent": 0.0,
                        "quality_score": 95, "quality_grade": "优秀"},
        "fps": {"window_title": "Game", "fps": 142, "frame_time_ms": 7.04,
                "low_1_percent": 118, "source": "presentmon"},
        "processes": {
            "top_cpu": [{"name": "chrome", "usage_percent": 12},
                        {"name": "game", "usage_percent": 8}],
            "top_gpu": [{"name": "game", "usage_percent": 48},
                        {"name": "obs", "usage_percent": 15}],
        },
    }


# ---------- 1. 完整字段映射 ----------

def test_full_mapping():
    print("\n--- 1. 完整字段映射 (43 字段) ---")
    ns = NodeStore(); fs = FrameStore()
    vm = NodeDetailViewModel(ns, fs)
    ns.add_node("test", alias="测试机", ip="192.168.1.100", port=12345)
    ns.update_status("test", "connected")
    ns.update_quality("test", rtt_ms=5.0, loss_percent=0.0)
    frame = full_frame()

    # 直接测试 _build_detail_data（不依赖 Signal）
    data = vm._build_detail_data("test", frame)

    # Identity
    check("identity.node_id", data.identity.node_id == "test")
    check("identity.alias", data.identity.alias == "测试机")
    check("identity.ip", data.identity.ip == "192.168.1.100")
    check("identity.port", data.identity.port == 12345)
    check("identity.status", data.identity.status == "connected")

    # System
    check("system.hostname", data.system.hostname == "DESKTOP-TEST")
    check("system.local_ip", data.system.local_ip == "192.168.1.100")
    check("system.uptime 非 N/A", data.system.uptime != "N/A")

    # CPU (7)
    check("cpu.name", data.cpu.name == "Ryzen 9")
    check("cpu.usage", data.cpu.usage == 45.2)
    check("cpu.cores_phys", data.cpu.cores_phys == 8)
    check("cpu.cores_logic", data.cpu.cores_logic == 16)
    check("cpu.freq_mhz", data.cpu.freq_mhz == 4500)
    check("cpu.temp_c", data.cpu.temp_c == 65.0)
    check("cpu.power_w", data.cpu.power_w == 65.0)

    # Memory (5)
    check("memory.total_gb", data.memory.total_gb == 32.0)
    check("memory.used_gb", data.memory.used_gb == 15.9)
    check("memory.avail_gb", data.memory.avail_gb == 16.1)
    check("memory.usage", data.memory.usage == 49.8)
    check("memory.swap_mb", data.memory.swap_mb == 1200.0)

    # GPU (8)
    check("gpu.name", data.gpu.name == "RTX 4070")
    check("gpu.usage", data.gpu.usage == 62.1)
    check("gpu.vram_used", data.gpu.vram_used == 8192)
    check("gpu.vram_total", data.gpu.vram_total == 12288)
    check("gpu.core_temp", data.gpu.core_temp == 71.0)
    check("gpu.hotspot_temp", data.gpu.hotspot_temp == 82.0)
    check("gpu.freq_mhz", data.gpu.freq_mhz == 2400)
    check("gpu.power_w", data.gpu.power_w == 185.0)

    # Disk (5 + all_disks)
    check("disk.drive", data.disk.drive == "C:")
    check("disk.read_mb_s", data.disk.read_mb_s == 120.0)
    check("disk.write_mb_s", data.disk.write_mb_s == 85.0)
    check("disk.usage", data.disk.usage == 78.0)
    check("disk.free_gb", data.disk.free_gb == 45.0)
    check("disk.all_disks len=2", len(data.disk.all_disks) == 2)

    # Network (4)
    check("network.iface", data.network.iface == "以太网")
    check("network.up_mb_s", data.network.up_mb_s == 12.3)
    check("network.down_mb_s", data.network.down_mb_s == 45.6)
    check("network.link_speed", data.network.link_speed == 1000)

    # Quality (5)
    check("quality.rtt", data.quality.rtt == 0.45)
    check("quality.gw_rtt", data.quality.gw_rtt == 1.2)
    check("quality.loss", data.quality.loss == 0.0)
    check("quality.score", data.quality.score == 100)
    check("quality.grade", data.quality.grade == "优秀")

    # FPS (5)
    check("fps.window", data.fps.window == "Game")
    check("fps.value", data.fps.value == 142)
    check("fps.frame_time", data.fps.frame_time == 7.04)
    check("fps.low1", data.fps.low1 == 118)
    check("fps.source", data.fps.source == "presentmon")

    # Processes (2)
    check("proc.cpu_text", "chrome" in data.processes.cpu_text)
    check("proc.gpu_text", "game" in data.processes.gpu_text)


# ---------- 2. 节点隔离 ----------

def test_node_isolation():
    print("\n--- 2. 节点隔离 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = NodeDetailViewModel(ns, fs)
    ns.add_node("A", alias="A"); ns.add_node("B", alias="B")

    frame_a = full_frame(); frame_a["cpu"]["total_usage"] = 20.0
    frame_b = full_frame(); frame_b["cpu"]["total_usage"] = 80.0

    fs.push("A", frame_a)
    fs.push("B", frame_b)

    data_a = vm.get_data("A")
    data_b = vm.get_data("B")
    check("A.cpu=20", data_a.cpu.usage == 20.0)
    check("B.cpu=80", data_b.cpu.usage == 80.0)

    # 更新 A 不影响 B
    frame_a2 = full_frame(); frame_a2["cpu"]["total_usage"] = 55.0
    fs.push("A", frame_a2)
    check("A 更新后=55", vm.get_data("A").cpu.usage == 55.0)
    check("B 仍=80", vm.get_data("B").cpu.usage == 80.0)


# ---------- 3. 空数据 ----------

def test_empty_data():
    print("\n--- 3. 空数据 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = NodeDetailViewModel(ns, fs)
    ns.add_node("test")

    # 无帧 -> 所有字段 None/"N/A"
    data = vm.get_data("test")
    check("无帧时 data 为 None", data is None)

    # 有帧但无 GPU
    frame = full_frame(); del frame["gpu"]
    fs.push("test", frame)
    data = vm.get_data("test")
    check("无 GPU -> gpu.usage=None", data.gpu.usage is None)
    check("无 GPU -> gpu.name=N/A", data.gpu.name == "N/A")

    # 有帧但无 FPS
    frame2 = full_frame(); del frame2["fps"]
    fs.push("test", frame2)
    data = vm.get_data("test")
    check("无 FPS -> fps.value=None", data.fps.value is None)

    # 有帧但无 disk
    frame3 = full_frame(); frame3["disk"] = []
    fs.push("test", frame3)
    data = vm.get_data("test")
    check("空 disk -> disk.drive=N/A", data.disk.drive == "N/A")
    check("空 disk -> all_disks=[]", data.disk.all_disks == [])


# ---------- 4. 删除 ----------

def test_removal():
    print("\n--- 4. 删除 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = NodeDetailViewModel(ns, fs)
    ns.add_node("A"); ns.add_node("B")
    fs.push("A", full_frame()); fs.push("B", full_frame())
    check("初始 2 缓存", len(vm.node_ids()) == 2)

    removed_ids = []
    vm.data_removed.connect(lambda nid: removed_ids.append(nid))

    ns.remove_node("A")
    check("删除后 1 缓存", len(vm.node_ids()) == 1)
    check("get_data(A) 为 None", vm.get_data("A") is None)
    check("get_data(B) 仍在", vm.get_data("B") is not None)
    check("data_removed 信号触发", removed_ids == ["A"])


# ---------- 5. 缓存 ----------

def test_cache():
    print("\n--- 5. 缓存 ---")
    ns = NodeStore(); fs = FrameStore()
    vm = NodeDetailViewModel(ns, fs)
    ns.add_node("X")

    # frame1 -> 缓存创建
    f1 = full_frame(); f1["cpu"]["total_usage"] = 10.0
    fs.push("X", f1)
    d1 = vm.get_data("X")
    check("frame1 缓存创建", d1 is not None)
    check("frame1 cpu=10", d1.cpu.usage == 10.0)

    # frame2 -> 缓存更新（_build_detail_data 创建新对象替换旧的）
    f2 = full_frame(); f2["cpu"]["total_usage"] = 20.0
    fs.push("X", f2)
    d2 = vm.get_data("X")
    check("frame2 缓存更新", d2 is not None)
    check("frame2 cpu=20", d2.cpu.usage == 20.0)


# ---------- 6. to_dict ----------

def test_to_dict():
    print("\n--- 6. to_dict ---")
    ns = NodeStore(); fs = FrameStore()
    vm = NodeDetailViewModel(ns, fs)
    ns.add_node("test", alias="T", ip="1.2.3.4", port=12345)
    ns.update_quality("test", 5.0, 0.0)
    fs.push("test", full_frame())

    d = vm.get_data("test").to_dict()
    # Identity 无前缀
    check("to_dict node_id", d.get("node_id") == "test")
    check("to_dict alias", d.get("alias") == "T")
    check("to_dict 无 identity_ 前缀", "identity_alias" not in d)
    # Cpu 有 cpu_ 前缀
    check("to_dict cpu_usage", d.get("cpu_usage") == 45.2)
    check("to_dict cpu_name", d.get("cpu_name") == "Ryzen 9")
    # Quality 有 quality_ 前缀
    check("to_dict quality_score", d.get("quality_score") == 100)
    # schema_version
    check("schema_version=1", d.get("schema_version") == 1)


# ---------- 7. get_summary ----------

def test_get_summary():
    print("\n--- 7. get_summary ---")
    ns = NodeStore(); fs = FrameStore()
    vm = NodeDetailViewModel(ns, fs)
    ns.add_node("test"); fs.push("test", full_frame())
    ns.update_quality("test", 5.0, 0.0)

    s = vm.get_summary("test")
    check("summary cpu_usage", s.get("cpu_usage") == 45.2)
    check("summary score 存在", s.get("score") is not None)
    check("summary 空节点", vm.get_summary("nonexistent") == {})


# ---------- 8. refresh_all ----------

def test_refresh_all():
    print("\n--- 8. refresh_all ---")
    ns = NodeStore(); fs = FrameStore()
    vm = NodeDetailViewModel(ns, fs)
    ns.add_node("A"); ns.add_node("B")
    fs.push("A", full_frame()); fs.push("B", full_frame())

    updated_ids = []
    vm.data_updated.connect(lambda nid: updated_ids.append(nid))

    vm.refresh_all()
    check("refresh_all emit 2 次", len(updated_ids) == 2)
    check("A+B 在结果中", set(updated_ids) == {"A", "B"})


# ---------- 9. safe_float / safe_int ----------

def test_safe_converters():
    print("\n--- 9. safe_float / safe_int ---")
    check("float ok", _safe_float(42.5) == 42.5)
    check("float str", _safe_float("33.3") == 33.3)
    check("float None", _safe_float(None) is None)
    check("float N/A", _safe_float("N/A") is None)
    check("float invalid", _safe_float("abc") is None)
    check("int ok", _safe_int(10) == 10)
    check("int str", _safe_int("5") == 5)
    check("int None", _safe_int(None) is None)


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  NodeDetailViewModel 单元测试 (Phase 3-3A)")
    print("=" * 55)

    test_full_mapping()
    test_node_isolation()
    test_empty_data()
    test_removal()
    test_cache()
    test_to_dict()
    test_get_summary()
    test_refresh_all()
    test_safe_converters()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
