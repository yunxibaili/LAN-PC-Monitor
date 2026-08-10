# -*- coding: utf-8 -*-
"""
打包 Agent（v5.0，见《README.md》§16.5）

用法：
    python build_agent.py

依赖：
    pip install pyinstaller

产物：
    dist/PC_Monitor_Agent/PC_Monitor_Agent.exe
    dist/PC_Monitor_Agent/  （含 agent_config.json、i18n、tools 等）

隔离规则（红线）：
- 只打包 agent + common，不包含 PyQt5/host（见 agent.spec 的 excludes）
- 与 Host 打包（build_host.py）严格分离，可并行执行。
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    print("[build_agent] 清理旧产物 ...")
    for d in ('build', 'dist'):
        p = os.path.join(ROOT, d)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)

    print("[build_agent] 调用 PyInstaller（agent.spec）...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        os.path.join(ROOT, "agent.spec"),
    ]
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print("[build_agent] PyInstaller 失败", file=sys.stderr)
        return r.returncode

    out_dir = os.path.join(ROOT, "dist", "PC_Monitor_Agent")
    print(f"[build_agent] 完成：{out_dir}")
    print("[build_agent] 安装路径建议：%ProgramFiles%\\PC_Monitor\\Agent\\")
    return 0


if __name__ == "__main__":
    sys.exit(main())
