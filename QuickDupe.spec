# -*- mode: python ; coding: utf-8 -*-
import os
import pydivert

pydivert_path = os.path.dirname(pydivert.__file__)

a = Analysis(
    ['quickdupe.py'],
    pathex=[],
    binaries=[('WinDivert.dll', '.'), ('WinDivert64.sys', '.')],
    datas=[('icon.ico', '.'), ('icon.png', '.'), (pydivert_path, 'pydivert'),
           ('NONE.png', '.'), ('N.png', '.'), ('NE.png', '.'), ('E.png', '.'),
           ('SE.png', '.'), ('S.png', '.'), ('SW.png', '.')],
    hiddenimports=['pynput', 'pynput.keyboard', 'pynput.mouse', 'pynput.keyboard._win32', 'pynput.mouse._win32', 'pynput._util', 'pynput._util.win32', 'pydivert', 'keyboard'],
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
    name='QuickDupe',
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
    uac_admin=True,
    icon=['icon.ico'],
)
