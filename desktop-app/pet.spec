# PyInstaller spec for pet.py (the desktop pet window)
# Run from desktop-app/ with: python -m PyInstaller pet.spec

import os

ENGINE = os.path.join('src', 'engine')

a = Analysis(
    [os.path.join(ENGINE, 'pet.py')],
    pathex=[ENGINE],
    binaries=[],
    datas=[
        # Built-in spritesheets
        (os.path.join(ENGINE, 'interaction_import_pack', 'lamuh_extended_spritesheet_12x8.webp'), 'interaction_import_pack'),
        (os.path.join(ENGINE, 'kairo', 'kairo_extended_spritesheet_12x8.webp'), 'kairo'),
        (os.path.join(ENGINE, 'duo_lamuh_kairo_combat_strip.png'), '.'),
        # Kairo extended interactions for beam clash rows
        (os.path.join(ENGINE, 'interaction_import_pack', 'lamuh_interactions_spritesheet_3x8.webp'), 'interaction_import_pack'),
        (os.path.join(ENGINE, 'kairo', 'interactions', 'kairo_interactions_spritesheet_3x8.webp'), os.path.join('kairo', 'interactions')),
    ],
    hiddenimports=[
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageGrab',
        'PIL.ImageDraw',
        'google.genai',
        'google.generativeai',
        'tkinter',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='pet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pet',
)
