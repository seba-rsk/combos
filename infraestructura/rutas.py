from __future__ import annotations

import sys
from pathlib import Path


def _ruta_base() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


RUTA_RAIZ = _ruta_base()
RUTA_PROFILES = RUTA_RAIZ / "profiles"
RUTA_EXPORTADORES = RUTA_RAIZ / "exportadores"
RUTA_LOG = RUTA_RAIZ / "combos_error.log"
