# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

datas = [
    ("assets", "assets"),
]
datas += collect_data_files("certifi")


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
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
    [],
    exclude_binaries=True,
    name="LifeXP",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="LifeXP",
)

app = BUNDLE(
    coll,
    name="LifeXP.app",
    icon="assets/app_icon/lifexp_icon.icns",
    bundle_identifier="com.lifexp.app",
    info_plist={
        "CFBundleDisplayName": "LifeXP",
        "CFBundleName": "LifeXP",
        "CFBundleShortVersionString": "1.0.4",
        "CFBundleVersion": "1.0.4",
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
    },
)
