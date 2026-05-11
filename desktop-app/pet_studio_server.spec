# PyInstaller spec for pet_studio_server.py (the HTTP hatch studio server)
# Run from desktop-app/ with: python -m PyInstaller pet_studio_server.spec

import os

ENGINE = os.path.join('src', 'engine')
RENDERER = os.path.join('src', 'renderer')

a = Analysis(
    [os.path.join(ENGINE, 'pet_studio_server.py')],
    pathex=[ENGINE],
    binaries=[],
    datas=[
        # Main UI HTML
        (os.path.join(RENDERER, 'pet_studio.html'), '.'),
        # Sample atlas served by the UI
        (os.path.join(ENGINE, 'interaction_import_pack', 'lamuh_extended_spritesheet_12x8.webp'), 'interaction_import_pack'),
        (os.path.join(ENGINE, 'interaction_import_pack', 'lamuh_extended_spritesheet_12x8.pre-v2-beam.webp'), 'interaction_import_pack'),
        (os.path.join(ENGINE, 'interaction_import_pack', 'lamuh_interactions_spritesheet_3x8.webp'), 'interaction_import_pack'),
        (os.path.join(ENGINE, 'interaction_import_pack', 'lamuh_interactions_manifest.json'), 'interaction_import_pack'),
        (os.path.join(ENGINE, 'interaction_import_pack', 'pet_shonen_extended.json'), 'interaction_import_pack'),
        (os.path.join(ENGINE, 'interaction_import_pack', 'pet_py_state_map_patch.json'), 'interaction_import_pack'),
    ],
    hiddenimports=[
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
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
    name='pet_studio_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='server',
)
