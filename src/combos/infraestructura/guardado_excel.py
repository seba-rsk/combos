from __future__ import annotations

import os
import secrets
from pathlib import Path


def guardar_excel_atomico(libro, ruta_destino: str) -> None:
    """
    Guarda el libro en un archivo temporal en el mismo directorio que
    ruta_destino y lo renombra sobre el destino final con os.replace,
    una operación atómica a nivel de sistema de archivos.

    Evita que una interrupción a mitad de escritura (corte de energía,
    disco lleno) corrompa o trunque el archivo de destino, o pierda la
    versión anterior sin poder recuperarla. El nombre del temporal
    lleva un sufijo aleatorio: en un directorio compartido, un nombre
    predecible habilitaría a otro proceso a plantar un symlink en esa
    ruta entre la escritura y el renombre.
    """
    ruta = Path(ruta_destino)
    ruta_temporal = ruta.with_name(
        f".{ruta.name}.{secrets.token_hex(8)}.tmp"
    )
    try:
        libro.save(ruta_temporal)
        os.replace(ruta_temporal, ruta)
    except Exception:
        if ruta_temporal.exists():
            ruta_temporal.unlink()
        raise
