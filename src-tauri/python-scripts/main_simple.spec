# -*- mode: python ; coding: utf-8 -*-

# Version simplifiée pour debug PyInstaller
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Seulement les modules critiques
        'json',
        'sys', 
        'os',
        'io',
        'base64',
        # Nos modules custom
        'context',
        'pignat', 
        'chromeleon_online',
        'chromeleon_offline',
        'chromeleon_online_permanent',
        'resume'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclure les modules lourds pour test
        'matplotlib',
        'tkinter',
        'test',
        'unittest',
        'pdb',
        'doctest'
    ],
    noarchive=False,
    optimize=0,  # Pas d'optimisation pour debug
    cipher=None
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='data_processor_simple',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
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