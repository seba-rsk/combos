# -*- mode: python ; coding: utf-8 -*-

# DESACTUALIZADO desde la migración a Nivel 3 (2026-07-17): las rutas
# "main.py", "profiles" y "exportadores" ya no existen en la raíz del
# repo. El código vive ahora en src/combos/. Este .spec se rehace desde
# cero como parte del ítem 4B del plan post-v1.1.0 (decisiones de
# instalación: instalador, empaquetador y destino). Hasta entonces
# `pyinstaller combos.spec` va a fallar — es esperable.

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("profiles", "profiles"),
        ("exportadores", "exportadores"),
    ],
    hiddenimports=[],
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
    name="COMBOS",
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
    icon="combos.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="COMBOS",
)
