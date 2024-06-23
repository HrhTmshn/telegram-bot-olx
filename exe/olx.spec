# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

fake_useragent_data_path = Path(__import__('fake_useragent').__file__).parent / 'data'
block_cipher = None

project_root = '..'

a = Analysis(
    ['../main.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        (fake_useragent_data_path, 'fake_useragent/data')
    ],
    hiddenimports=[
        'telebot',
        'bs4',
        'fake_useragent',
        'requests',
        'sqlite3',
        'hashlib'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OLX_Telegram_Bot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon='icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
