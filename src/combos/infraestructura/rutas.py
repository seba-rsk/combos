from __future__ import annotations

import sys
from pathlib import Path


def _ruta_paquete() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def _ruta_log_base() -> Path:
    # En modo desarrollo el log vive en la raíz del repositorio, no dentro
    # del paquete. Desde src/combos/infraestructura/rutas.py hay que subir
    # cuatro niveles para llegar a la raíz. El destino definitivo en
    # release lo define el ítem 4B del plan post-v1.1.0.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.parent.parent


RUTA_RAIZ = _ruta_paquete()
RUTA_PROFILES = RUTA_RAIZ / "profiles"
RUTA_EXPORTADORES = RUTA_RAIZ / "exportadores"
RUTA_LOG = _ruta_log_base() / "combos_error.log"
