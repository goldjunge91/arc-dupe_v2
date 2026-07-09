# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# When PyInstaller executes a spec file, __file__ may not be defined; fall back to cwd
try:
    here = os.path.dirname(os.path.abspath(__file__))
    if not here:
        here = os.path.abspath('.')
except NameError:
    here = os.path.abspath('.')

# Root of the repo is one level up from duper/
root = os.path.dirname(here)

icon_path = os.path.join(here, 'icon.ico')

datas = []
if os.path.exists(icon_path):
    datas.append((icon_path, '.'))

a = Analysis(
    [os.path.join(here, 'slot_swap_tool.py')],
    pathex=[root],          # ensures 'utils' package is importable at build time
    binaries=[],
    datas=datas,
    hiddenimports=[
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'pynput._util',
        'pynput._util.win32',
        'keyboard',
        'utils',
        'utils.timing',
    ],
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
    name='SlotSwapTool',
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
    icon=[icon_path],
)
