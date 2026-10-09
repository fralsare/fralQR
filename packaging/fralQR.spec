# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for fralQR (onedir build).
#
# Build from the repo root:
#   pyinstaller packaging/fralQR.spec
#
# Output: dist/fralQR/   (a folder: the executable + the _internal runtime)
#
# The onedir folder is what the Linux packages (.deb/.rpm/.AppImage) and the
# Windows installer wrap. For the Windows *portable* single .exe, build from
# the CLI instead:  pyinstaller --onefile --noconsole --name fralQR fralQR.py

import os

ROOT = os.path.normpath(os.path.join(SPECPATH, os.pardir))
MAIN = os.path.join(ROOT, 'fralQR.py')

a = Analysis(
    [MAIN],
    pathex=[ROOT],
    binaries=[],
    datas=[],
    hiddenimports=['PIL', 'PIL.Image', 'PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter.test', 'tkinter.tix', 'unittest', 'pydoc', 'test',
              'setuptools', 'pip', 'ensurepip'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,        # onedir: keep runtime binaries beside the exe
    name='fralQR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,                # windowed app (no console window on Windows)
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='fralQR',
)
