# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all submodules for data processing libraries
hiddenimports = []

# Core Python modules that might not be detected
hiddenimports += [
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
    'concurrent.futures',
]

# Critical runtime dependencies  
hiddenimports += [
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
]

# Collect comprehensive submodules
hiddenimports += collect_submodules('pandas')
hiddenimports += collect_submodules('numpy')
hiddenimports += collect_submodules('openpyxl')
hiddenimports += collect_submodules('matplotlib')
hiddenimports += collect_submodules('PIL')
hiddenimports += collect_submodules('contourpy')

# Specific pandas/numpy modules that often cause issues
hiddenimports += [
    'pandas._libs.tslibs.timedeltas',
    'pandas._libs.tslibs.np_datetime', 
    'pandas._libs.tslibs.nattype',
    'pandas._libs.skiplist',
    'pandas._libs.hashtable',
    'pandas._libs.lib',
    'pandas._libs.properties',
    'pandas._libs.algos',
    'pandas._libs.parsers',
    'pandas._libs.writers',
    'pandas._libs.reduction',
    'pandas._libs.testing',
    'pandas._libs.sparse',
    'pandas._libs.ops',
    'pandas._libs.join',
    'pandas._libs.groupby',
    'pandas._libs.window',
    'pandas._libs.reshape',
    'pandas._libs.internals',
    'pandas._libs.interval',
    'pandas._libs.tslib',
    'pandas._libs.json',
    'pandas._libs.index',
    'pandas.util._decorators',
    'pandas.compat.numpy',
    'pandas.core.dtypes.common',
    'pandas.core.dtypes.generic',
    'pandas.core.dtypes.inference',
]

# NumPy random modules (fix for the specific error)
hiddenimports += [
    'numpy.random._common',
    'numpy.random._bounded_integers',
    'numpy.random._mt19937',
    'numpy.random._pcg64', 
    'numpy.random._philox',
    'numpy.random._sfc64',
    'numpy.random.bit_generator',
    'numpy.random._pickle',
    'numpy.random._generator',
    'numpy.core._multiarray_umath',
    'numpy.core._multiarray_tests',
    'numpy.linalg._umath_linalg',
    'numpy.fft._pocketfft_internal',
]

# OpenPyXL specific modules
hiddenimports += [
    'openpyxl.xml.functions',
    'openpyxl.workbook.external_link.external',
    'openpyxl.formatting.rule',
    'openpyxl.packaging.manifest',
    'openpyxl.packaging.extended',
]

# Add custom modules
hiddenimports += [
    'context',
    'pignat',
    'chromeleon_online', 
    'chromeleon_offline',
    'chromeleon_online_permanent',
    'resume',
]

# Collect data files for libraries that need them
datas = []
try:
    datas += collect_data_files('pandas')
except:
    pass
try:
    datas += collect_data_files('numpy')
except:
    pass
try:
    datas += collect_data_files('matplotlib')
except:
    pass

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
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
        'matplotlib.tests',
        'IPython',
        'jupyter',
        'notebook',
        'sphinx',
        'alabaster',
        'babel',
        'jinja2',
        'markupsafe',
        'pygments',
        'pytz',
        'tornado',
        'zmq',
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
    upx=False,  # Désactiver UPX car il peut causer des problèmes avec NumPy/Pandas
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
