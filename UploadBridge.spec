# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['PIL', 'cv2', 'numpy', 'PySide6', 'cryptography', 'ui', 'ui.main_window', 'ui.tabs.preview_tab', 'ui.tabs.flash_tab', 'ui.tabs.media_upload_tab', 'ui.tabs.wifi_upload_tab', 'ui.tabs.arduino_ide_tab', 'ui.dialogs.activation_dialog', 'core', 'core.pattern', 'parsers.parser_registry', 'uploaders.uploader_registry']
hiddenimports += collect_submodules('ui')
hiddenimports += collect_submodules('core')
hiddenimports += collect_submodules('parsers')
hiddenimports += collect_submodules('uploaders')


a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('config/chip_database.yaml', 'config'), ('config/app_config.yaml', 'config'), ('firmware/templates', 'firmware/templates'), ('config', 'config'), ('ui', 'ui'), ('core', 'core'), ('parsers', 'parsers'), ('uploaders', 'uploaders'), ('LEDMatrixStudio_icon.ico', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'pandas'],
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
    name='UploadBridge',
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
    icon=['LEDMatrixStudio_icon.ico'],
)
