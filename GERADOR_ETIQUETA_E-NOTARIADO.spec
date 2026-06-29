# -*- mode: python ; coding: utf-8 -*-
import os
import glob
from PyInstaller.utils.hooks import collect_all

# Coleta todos os submodulos e dados do qrcode
qrcode_datas, qrcode_binaries, qrcode_hidden = collect_all('qrcode')

# DLLs do pywin32 que o PyInstaller não detecta automaticamente
_p310 = r'C:\Users\lorran.lima\AppData\Local\Programs\Python\Python310\Lib\site-packages\pywin32_system32'
_pywin32_dlls = [(dll, '.') for dll in glob.glob(os.path.join(_p310, '*.dll'))]

a = Analysis(
    ['GERADOR_ETIQUETA_E-NOTARIADO.py'],
    pathex=[],
    binaries=qrcode_binaries + _pywin32_dlls,
    datas=[
        ('LOGO E-NOTARIADO.png', '.'),
        ('ICONE.ico', '.'),
        *qrcode_datas,
    ],
    hiddenimports=[
        *qrcode_hidden,
        'qrcode',
        'qrcode.image.pil',
        'qrcode.image.base',
        'qrcode.image.svg',
        'qrcode.image.styles.moduledrawers',
        'qrcode.image.styles.colormasks',
        'qrcode.constants',
        'qrcode.main',
        'qrcode.util',
        'qrcode.exceptions',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'reportlab',
        'win32print',
        'win32api',
        'win32con',
        'pywintypes',
        'pythoncom',
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
    name='GERADOR_ETIQUETA_E-NOTARIADO',
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
    icon='ICONE.ico',
)
