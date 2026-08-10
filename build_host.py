# -*- coding: utf-8 -*-
"""
打包 Host（v5.0，见《README.md》§16.5）

用法：
    python build_host.py

依赖：
    pip install pyinstaller

产物：
    dist/PC_Monitor_Host/PC_Monitor_Host.exe
    dist/PC_Monitor_Host/  （含 host_config.json、i18n 等）

隔离规则（红线）：
- 只打包 host + common，不包含 aiohttp/websockets/agent（见 host.spec 的 excludes）
- 与 Agent 打包（build_agent.py）严格分离，可并行执行。
- Host GUI 仅渲染与本地缓存，不发起任何 TCP 长连接（仅 WS 客户端）。
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    print("[build_host] 清理旧产物 ...")
    for d in ('build', 'dist'):
        p = os.path.join(ROOT, d)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)

    print("[build_host] 调用 PyInstaller（host.spec）...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        os.path.join(ROOT, "host.spec"),
    ]
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print("[build_host] PyInstaller 失败", file=sys.stderr)
        return r.returncode

    out_dir = os.path.join(ROOT, "dist", "PC_Monitor_Host")
    print(f"[build_host] 完成：{out_dir}")
    print("[build_host] 安装路径建议：%LocalAppData%\\PC_Monitor\\Host\\")
    return 0


if __name__ == "__main__":
    sys.exit(main())
