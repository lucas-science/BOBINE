# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# Approche ultra-robuste : collecter TOUT de pandas et ses dépendances
datas = []
binaries = []
hiddenimports = []

# Collecter ABSOLUMENT TOUT de pandas (plus lourd mais plus sûr)
pandas_datas, pandas_binaries, pandas_hiddenimports = collect_all('pandas')
datas.extend(pandas_datas)
binaries.extend(pandas_binaries) 
hiddenimports.extend(pandas_hiddenimports)

# Collecter TOUT de pytz
try:
    pytz_datas, pytz_binaries, pytz_hiddenimports = collect_all('pytz')
    datas.extend(pytz_datas)
    binaries.extend(pytz_binaries)
    hiddenimports.extend(pytz_hiddenimports)
except:
    # Fallback si collect_all échoue
    hiddenimports.extend(collect_submodules('pytz'))

# Collecter TOUT de dateutil
try:
    dateutil_datas, dateutil_binaries, dateutil_hiddenimports = collect_all('dateutil')
    datas.extend(dateutil_datas)
    binaries.extend(dateutil_binaries)
    hiddenimports.extend(dateutil_hiddenimports)
except:
    hiddenimports.extend(collect_submodules('dateutil'))

# Collecter les autres librairies normalement
hiddenimports.extend(collect_submodules('numpy'))
hiddenimports.extend(collect_submodules('openpyxl'))
hiddenimports.extend(collect_submodules('matplotlib'))
hiddenimports.extend(collect_submodules('PIL'))

# Ajouter explicitement TOUS les modules pytz possibles
hiddenimports += [
    # PyTZ complet
    'pytz',
    'pytz.tzinfo',
    'pytz.tzfile',
    'pytz.lazy',
    'pytz._FixedOffset',
    'pytz._DstTzInfo',
    'pytz._StaticTzInfo',
    'pytz._UTCclass',
    'pytz.reference',
    'pytz.exceptions',
    
    # DateUtil complet
    'dateutil',
    'dateutil.tz',
    'dateutil.tz.tz',
    'dateutil.tz.tzfile',
    'dateutil.tz.tzlocal',
    'dateutil.tz.tzwin',
    'dateutil.tz.gettz',
    'dateutil.parser',
    'dateutil.parser._parser',
    'dateutil.relativedelta',
    'dateutil.rrule',
    'dateutil.utils',
    
    # Modules Python standard critiques
    'secrets',
    'hashlib',
    'hmac',
    'uuid',
    'json',
    'base64',
    'io',
    'os',
    'sys',
    'datetime',
    'collections',
    'itertools',
    'functools',
    'warnings',
    'weakref',
    'copy',
    'pickle',
    'struct',
    'array',
    'math',
    'random',
    'threading',
    'queue',
    'zoneinfo',
    
    # Runtime dependencies
    '_ctypes',
    '_decimal',
    '_multiprocessing',
    '_socket',
    '_ssl',
    'select',
    '_hashlib',
    '_uuid',
    '_json',
    '_pickle',
    '_random',
    '_struct',
    '_thread',
    '_locale',
    '_codecs',
    
    # Modules customs
    'context',
    'pignat',
    'chromeleon_online',
    'chromeleon_offline', 
    'chromeleon_online_permanent',
    'resume',
    
    # Autres dépendances pandas souvent manquées
    'six',
    'packaging',
    'packaging.version',
    'packaging.specifiers',
    'packaging.requirements',
]

# Données additionnelles pour pytz (fuseaux horaires)
try:
    import pytz
    pytz_data_path = pytz.__path__[0]
    datas.append((pytz_data_path, 'pytz'))
except:
    pass

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclure seulement les modules vraiment inutiles
        'tkinter',
        'test',
        'unittest',
        'pdb',
        'doctest',
        'IPython',
        'jupyter',
        'notebook',
        'sphinx',
        'pytest',
        'pandas.tests',
        'numpy.f2py.tests',
        'matplotlib.tests',
    ],
    noarchive=False,
    cipher=None,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
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
