from __future__ import annotations

import os
import sys
from pathlib import Path


def _ruta_paquete() -> Path:
    # Empaquetado con PyInstaller, los datos del programa (profiles,
    # exportadores) viajan en la carpeta interna del bundle que expone
    # sys._MEIPASS (ver combos.spec). En desarrollo es el paquete mismo.
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", "."))
    return Path(__file__).parent.parent


def _ruta_log_base() -> Path:
    # En release el log vive en %LOCALAPPDATA%\COMBOS (decisión del ítem
    # 4B): siempre escribible, sobrevive a las actualizaciones y no
    # depende de la carpeta de instalación. En modo desarrollo queda en
    # la raíz del repositorio: desde este archivo hay que subir cuatro
    # niveles.
    if getattr(sys, "frozen", False):
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "COMBOS"
        return Path.home() / "AppData" / "Local" / "COMBOS"
    return Path(__file__).parent.parent.parent.parent


RUTA_RAIZ = _ruta_paquete()
RUTA_PROFILES = RUTA_RAIZ / "profiles"
RUTA_EXPORTADORES = RUTA_RAIZ / "exportadores"
RUTA_LOG = _ruta_log_base() / "combos_error.log"
