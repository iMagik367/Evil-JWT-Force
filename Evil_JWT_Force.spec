# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/yami_/Documents/Tramoias/Evil-Force-JWT-main/Evil-Force-JWT-main/gui/assets/*', 'gui/assets/'), ('C:/Users/yami_/Documents/Tramoias/Evil-Force-JWT-main/Evil-Force-JWT-main/config/*', 'config/')],
    hiddenimports=['tkinter', 'PIL'],
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
    name='Evil_JWT_Force',
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
    icon=['C:\\Users\\yami_\\Documents\\Tramoias\\Evil-Force-JWT-main\\Evil-Force-JWT-main\\gui\\assets\\icon.ico'],
)
