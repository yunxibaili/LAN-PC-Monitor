# -*- mode: python ; coding: utf-8 -*-
# Agent 打包配置（v5.0，见《README.md》§16.5）
# 与 host.spec 严格隔离：不同 entry、不同输出名、不同依赖 hiddenimports。
# - 输出：dist/PC_Monitor_Agent/PC_Monitor_Agent.exe
# - 安装路径建议：%ProgramFiles%\\PC_Monitor\\Agent\\
# - 仅包含 Agent + common + 共用依赖；不包含 PyQt5 与 host/*
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Agent 入口与子模块
hiddenimports = []
hiddenimports += collect_submodules('agent')
hiddenimports += collect_submodules('common')

a = Analysis(
    ['agent/__main__.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('agent_config.json', '.'),
        ('i18n', 'i18n'),
        ('tools', 'tools'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtWidgets', 'PyQt5.QtGui',
        'host',
        'websocket', 'websocket-client', 'requests',  # 仅 Host 依赖
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PC_Monitor_Agent',           # ← 输出名带 Agent 后缀（与 Host 区分）
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                     # 后台服务，无控制台
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PC_Monitor_Agent',           # ← 独立目录
)
