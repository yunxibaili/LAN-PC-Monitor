# -*- coding: utf-8 -*-
"""
test_v52_detail_panel.py —— DetailPanel v5.2 接口测试（Phase 3-3D）。

验证 host/gui/widgets/detail_panel.py（基于 NodeDetailData）：
1. update_data(NodeDetailData) 正确刷新 UI（稳定字段 + 精确格式）
2. update_data(None) / clear() → 全部置为 "—"
3. 架构扫描：不直接依赖 monitor_data / Store / Connection

已知遗留问题（RC-4 评审发现，本次不修，见 docs/reports/rc4_final_report.md）：
- 字段键冲突：cpu/gpu 共用 name / usage_percent / core_freq_mhz / power_w，
  后者覆盖前者，故本测试只覆盖不冲突字段。
- None 数值字段直接 f-string 格式化会抛 TypeError（如 gpu.usage=None），
  本测试不构造该路径。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt5.QtWidgets import QApplication
import sys as _sys
if not _sys.argv:
    _sys.argv = ["test"]
_app = QApplication.instance() or QApplication(_sys.argv)

from host.gui.widgets.detail_panel import DetailPanel
from host.viewmodels.node_detail_vm import (
    NodeDetailData, IdentityData, SystemData, CpuData, MemoryData,
    GpuData, DiskData, NetworkData, QualityData, FpsData, ProcessData,
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


def _label_text(panel, field_key):
    """从 DetailPanel 获取指定字段标签文字（_labels 为平铺 dict）。"""
    label = panel._labels.get(field_key)
    return label.text() if label else None


def full_data():
    """构造完整 NodeDetailData。"""
    d = NodeDetailData()
    d.identity = IdentityData()
    d.identity.node_id = "test-pc"
    d.identity.alias = "测试机"
    d.identity.status = "connected"
    d.identity.ip = "192.168.1.100"
    d.identity.port = 12345
    d.system = SystemData()
    d.system.hostname = "DESKTOP-TEST"
    d.system.local_ip = "192.168.1.100"
    d.system.uptime = "1小时"
    d.cpu = CpuData()
    d.cpu.name = "Ryzen 9"
    d.cpu.usage = 45.2
    d.cpu.cores_phys = 8
    d.cpu.cores_logic = 16
    d.cpu.freq_mhz = 4500
    d.cpu.temp_c = 65.0
    d.cpu.power_w = 65.0
    d.memory = MemoryData()
    d.memory.total_gb = 32.0
    d.memory.used_gb = 15.9
    d.memory.avail_gb = 16.1
    d.memory.usage = 49.8
    d.memory.swap_mb = 1200.0
    d.gpu = GpuData()
    d.gpu.name = "RTX 4070"
    d.gpu.usage = 62.1
    d.gpu.vram_used = 8192
    d.gpu.vram_total = 12288
    d.gpu.core_temp = 71.0
    d.gpu.hotspot_temp = 82.0
    d.gpu.freq_mhz = 2400
    d.gpu.power_w = 185.0
    d.disk = DiskData()
    d.disk.drive = "C:"
    d.disk.read_mb_s = 120.0
    d.disk.write_mb_s = 85.0
    d.disk.usage = 78.0
    d.disk.free_gb = 45.0
    d.disk.all_disks = [{"drive": "C:"}, {"drive": "D:"}]
    d.network = NetworkData()
    d.network.iface = "以太网"
    d.network.up_mb_s = 12.3
    d.network.down_mb_s = 45.6
    d.network.link_speed = 1000
    d.quality = QualityData()
    d.quality.rtt = 0.45
    d.quality.gw_rtt = 1.2
    d.quality.loss = 0.0
    d.quality.score = 95
    d.quality.grade = "优秀"
    d.fps = FpsData()
    d.fps.window = "Game"
    d.fps.value = 142
    d.fps.frame_time = 7.04
    d.fps.low1 = 118
    d.fps.source = "presentmon"
    d.processes = ProcessData()
    d.processes.cpu_text = "chrome 12%"
    d.processes.gpu_text = "game 48%"
    return d


# ---------- 1. 完整数据更新 ----------

def test_full_update():
    print("\n--- 1. 完整数据 update_data ---")
    panel = DetailPanel()
    panel.update_data(full_data())

    # CPU（cpu 独占字段）
    check("cpu.physical_cores", _label_text(panel, "physical_cores") == "8")
    check("cpu.logical_cores", _label_text(panel, "logical_cores") == "16")
    check("cpu.package_temp", _label_text(panel, "package_temp_c") == "65°C")

    # RAM
    check("ram.total", _label_text(panel, "total_gb") == "32.0 GB")
    check("ram.used", _label_text(panel, "used_gb") == "15.9 GB")
    check("ram.avail", _label_text(panel, "available_gb") == "16.1 GB")
    check("ram.swap", _label_text(panel, "swap_used_mb") == "1200 MB")

    # GPU（gpu 独占字段）
    check("gpu.core_temp", _label_text(panel, "core_temp_c") == "71°C")
    check("gpu.hotspot", _label_text(panel, "hotspot_temp_c") == "82°C")
    check("gpu.vram_used", _label_text(panel, "vram_used_mb") == "8192 MB")
    check("gpu.vram_total", _label_text(panel, "vram_total_mb") == "12288 MB")

    # Disk
    check("disk.drive", _label_text(panel, "drive") == "C:")
    check("disk.read", _label_text(panel, "read_mb_s") == "120.0 MB/s")
    check("disk.write", _label_text(panel, "write_mb_s") == "85.0 MB/s")
    check("disk.free", _label_text(panel, "free_gb") == "45.0 GB")

    # Network
    check("net.iface", _label_text(panel, "interface") == "以太网")
    check("net.up", _label_text(panel, "upload_mb_s") == "12.3 MB/s")
    check("net.down", _label_text(panel, "download_mb_s") == "45.6 MB/s")
    check("net.link_speed", _label_text(panel, "link_speed_mbps") == "1000 Mbps")

    # Quality
    check("nq.rtt", _label_text(panel, "latency_to_client_ms") == "0.45 ms")
    check("nq.gw_rtt", _label_text(panel, "latency_to_gateway_ms") == "1.20 ms")
    check("nq.loss", _label_text(panel, "packet_loss_percent") == "0.0%")
    check("nq.score", _label_text(panel, "quality_score") == "95")
    check("nq.grade", _label_text(panel, "quality_grade") == "优秀")

    # FPS
    check("fps.window", _label_text(panel, "window_title") == "Game")
    check("fps.value", _label_text(panel, "fps") == "142")
    check("fps.frame_time", _label_text(panel, "frame_time_ms") == "7.04 ms")
    check("fps.low1", _label_text(panel, "low_1_percent") == "118")
    check("fps.source", _label_text(panel, "source") == "presentmon")


# ---------- 2. 空数据 ----------

def test_none_data():
    print("\n--- 2. 空数据 (None) ---")
    panel = DetailPanel()
    panel.update_data(None)
    check("cpu.physical_cores = —", _label_text(panel, "physical_cores") == "—")
    check("ram.total = —", _label_text(panel, "total_gb") == "—")
    check("gpu.core_temp = —", _label_text(panel, "core_temp_c") == "—")


# ---------- 3. clear ----------

def test_clear():
    print("\n--- 3. clear ---")
    panel = DetailPanel()
    panel.update_data(full_data())
    check("更新后 cpu 有值", _label_text(panel, "physical_cores") != "—")

    panel.clear()
    check("clear 后 cpu = —", _label_text(panel, "physical_cores") == "—")
    check("clear 后 quality = —", _label_text(panel, "quality_score") == "—")


# ---------- 4. 架构扫描 ----------

def _scan_file(filepath, patterns, label):
    """扫描文件中是否包含禁止的模式。"""
    if not os.path.isfile(filepath):
        return True, f"文件不存在: {filepath}"
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()
    for pat in patterns:
        if pat in source:
            for line in source.splitlines():
                stripped = line.strip()
                if pat in stripped and not stripped.startswith("#"):
                    return False, f"发现禁止模式 '{pat}' in {filepath}"
    return True, ""


def test_no_monitor_data_in_detail_panel():
    """架构扫描：host DetailPanel 不直接解析 monitor_data。"""
    print("\n--- 4a. host DetailPanel 无 monitor_data 依赖 ---")
    dp = os.path.join(ROOT, "host", "gui", "widgets", "detail_panel.py")
    with open(dp, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()
    check("无 frame.get(", "frame.get(" not in source)
    check("无 import FrameStore", "FrameStore" not in source)
    check("无 import NodeStore", "NodeStore" not in source)
    check("无 import NodeConnection", "NodeConnection" not in source)
    check("无 update_all 定义", "def update_all" not in source)
    check("无 get_summary 定义", "def get_summary" not in source)


def test_no_monitor_data_in_nodes_page():
    """架构扫描：NodesPage 不直接解析 monitor_data。"""
    print("\n--- 4b. NodesPage 无 monitor_data 依赖 ---")
    np = os.path.join(ROOT, "host", "gui", "pages", "nodes_page.py")
    with open(np, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()
    check("无 frame.get(", "frame.get(" not in source)
    check("无 FrameStore import", "FrameStore" not in source)
    check("无 update_all 调用", "update_all" not in source)


def test_no_monitor_data_in_main_window():
    """架构扫描：MainWindow 无直接 frame 解析（DetailPanel 相关）。"""
    print("\n--- 4c. MainWindow 无 detail_panel.get_summary(frame) ---")
    mw = os.path.join(ROOT, "host", "gui", "main_window.py")
    with open(mw, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()
    remaining = []
    for i, line in enumerate(source.splitlines(), 1):
        if "detail_panel.get_summary" in line and not line.strip().startswith("#"):
            remaining.append(f"L{i}: {line.strip()[:60]}")
    check("无 detail_panel.get_summary(frame)", len(remaining) == 0,
          str(remaining))


def test_vm_is_primary_data_source():
    """架构扫描：NodesPage 使用 VM 作为主数据源。"""
    print("\n--- 4d. NodesPage 使用 VM ---")
    np = os.path.join(ROOT, "host", "gui", "pages", "nodes_page.py")
    source = open(np, "r", encoding="utf-8").read()
    check("有 update_data 调用", "update_data" in source)
    check("有 node_detail_vm 引用", "node_detail_vm" in source or "_node_detail_vm" in source)


def main():
    global PASS, FAIL
    print("=" * 55)
    print("  DetailPanel v5.2 测试 (Phase 3-3D)")
    print("=" * 55)

    test_full_update()
    test_none_data()
    test_clear()
    test_no_monitor_data_in_detail_panel()
    test_no_monitor_data_in_nodes_page()
    test_no_monitor_data_in_main_window()
    test_vm_is_primary_data_source()

    print()
    print(f"结果: {PASS} 通过, {FAIL} 失败")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
