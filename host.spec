# -*- mode: python ; coding: utf-8 -*-
# Host 打包配置（v5.0，见《README.md》§16.5）
# 与 agent.spec 严格隔离：不同 entry、不同输出名、不同依赖 hiddenimports。
# - 输出：dist/PC_Monitor_Host/PC_Monitor_Host.exe
# - 安装路径建议：%LocalAppData%\\PC_Monitor\\Host\\
# - 仅包含 Host + common + 共用依赖；不包含 aiohttp/websockets 与 agent/*
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = []
hiddenimports += collect_submodules('host')
hiddenimports += collect_submodules('common')

a = Analysis(
    ['host/__main__.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('host_config.json', '.'),
        ('i18n', 'i18n'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'aiohttp', 'websockets',         # 仅 Agent 依赖
        'agent',                         # Host 不依赖 agent
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
    name='PC_Monitor_Host',            # ← 输出名带 Host 后缀（与 Agent 区分）
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                     # GUI 应用，无控制台
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
    name='PC_Monitor_Host',            # ← 独立目录
)
