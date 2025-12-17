# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

# Resolve project root (two levels up from this spec file: installer/windows → installer → project root)
BASE_DIR = Path(SPEC).resolve().parents[2]


a = Analysis(
    [str(BASE_DIR / 'installer' / 'installer.py')],
    pathex=[str(BASE_DIR)],
    binaries=[],
    datas=[
        (str(BASE_DIR / 'config'), 'config'),
        (str(BASE_DIR / 'LICENSE_KEYS.txt'), '.'),
        (str(BASE_DIR / 'dist' / 'UploadBridge.exe'), 'payload'),
        (str(BASE_DIR / 'windows'), 'windows'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='UploadBridgeInstaller',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(BASE_DIR / 'LEDMatrixStudio_icon.ico')],
)
