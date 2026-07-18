# -*- mode: python ; coding: utf-8 -*-

# Empaquetado de COMBOS con PyInstaller en modo onedir (decisión del
# ítem 4B del plan post-v1.1.0). Se construye con:
#
#   pyinstaller combos.spec
#
# El resultado queda en dist/COMBOS/ y es la entrada del instalador
# (installer/combos.iss). Los perfiles de reglamento y de exportación
# viajan como datos del bundle: en ejecución se resuelven vía
# sys._MEIPASS (ver src/combos/infraestructura/rutas.py).
#
# UPX queda desactivado a propósito: la compresión de binarios dispara
# falsos positivos frecuentes en antivirus, y el instalador ya comprime
# todo con LZMA2.

a = Analysis(
    ["src/combos/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=[
        ("src/combos/profiles/*.yaml", "profiles"),
        ("src/combos/exportadores/*.yaml", "exportadores"),
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
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name="COMBOS",
)
