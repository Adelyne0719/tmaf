# -*- mode: python ; coding: utf-8 -*-
import sys
import os

# certifi 인증서 번들 경로
import certifi
certifi_path = os.path.dirname(certifi.__file__)

a = Analysis(
    ['v7_dual_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(certifi_path, 'cacert.pem'), 'certifi'),
    ],
    hiddenimports=[
        'certifi',
        'PyQt5.sip',
        'pyqtgraph',
        'pyqtgraph.graphicsItems',
        'pyqtgraph.graphicsItems.PlotDataItem',
        'pyqtgraph.graphicsItems.GraphicsObject',
        'pandas',
        'numpy',
        'requests',
        'websockets',
        'psutil',
        'asyncio',
        'decimal',
        'hashlib',
        'hmac',
        'json',
        'math',
        'gc',
        'PyQt5.QtWebEngineWidgets',
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
    name='v7_dual',
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
)
