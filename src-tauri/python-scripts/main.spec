# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_submodules

# Collect all submodules for data processing libraries
hiddenimports = []
hiddenimports += collect_submodules('pandas')
hiddenimports += collect_submodules('numpy')
hiddenimports += collect_submodules('openpyxl')
hiddenimports += collect_submodules('matplotlib')
hiddenimports += collect_submodules('PIL')
hiddenimports += collect_submodules('contourpy')

# Add custom modules and critical dependencies
hiddenimports += [
    'context',
    'pignat', 
    'chromeleon_online',
    'chromeleon_offline',
    'chromeleon_online_permanent',
    'resume',
    # Critical runtime dependencies
    '_ctypes',
    '_decimal',
    '_multiprocessing',
    '_socket',
    '_ssl',
    'select'
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'test',
        'unittest',
        'pdb',
        'doctest',
        'multiprocessing',
        'distutils',
        'setuptools',
        'pip',
        'pytest',
        'pandas.tests',
        'numpy.f2py.tests', 
        'matplotlib.tests'
    ],
    noarchive=False,
    cipher=None
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='data_processor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging output via stdout/stderr
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=False,
    version=None,
    icon=None,
    contents_directory='.',
)