# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['GERADOR_ETIQUETA_E-NOTARIADO.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('LOGO E-NOTARIADO.png', '.'),
        ('ICONE.ico', '.'),
    ],
    hiddenimports=[
        'qrcode',
        'qrcode.image.pil',
        'qrcode.image.base',
        'qrcode.constants',
        'PIL',
        'PIL.Image',
        'reportlab',
        'win32print',
        'win32api',
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
