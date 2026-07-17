"""
Lectura y escritura de archivos de sesión `.combos` en disco.

Qué guarda una sesión y cómo se reconstruye es responsabilidad de
dominio.persistencia_sesion; acá vive solo el acceso a disco:
serializar a JSON UTF-8 con escritura atómica, y leer y parsear con
errores en lenguaje claro.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dominio.persistencia_sesion import MENSAJE_ARCHIVO_DANADO

# Tamaño máximo de un archivo .combos. Una sesión real (reglamento
# embebido incluido) ocupa unos pocos KB; el límite corta archivos
# desmedidos antes de cargarlos completos a memoria.
MAX_BYTES_COMBOS = 10 * 1024 * 1024


class ErrorArchivoCombos(Exception):
    """No se pudo leer o escribir un archivo de sesión `.combos`."""


def leer_combos(ruta: str) -> dict:
    """
    Lee y parsea un archivo `.combos`. Devuelve los datos sin validar:
    la validación de contenido es de
    dominio.persistencia_sesion.sesion_desde_datos.

    Raises:
        ErrorArchivoCombos: Si el archivo no existe, no se puede leer o
            no contiene JSON válido.
    """
    ruta_archivo = Path(ruta)
    if not ruta_archivo.exists():
        raise ErrorArchivoCombos(
            f"No se encontró el archivo: '{ruta}'."
        )
    if ruta_archivo.stat().st_size > MAX_BYTES_COMBOS:
        raise ErrorArchivoCombos(
            f"No se pudo abrir '{ruta_archivo.name}': supera el tamaño "
            f"máximo de una sesión "
            f"({MAX_BYTES_COMBOS // (1024 * 1024)} MB). Una sesión real "
            f"ocupa unos pocos KB; revisá que sea el archivo correcto."
        )
    try:
        contenido = ruta_archivo.read_text(encoding="utf-8")
        return json.loads(contenido)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ErrorArchivoCombos(
            f"No se pudo abrir '{ruta_archivo.name}': "
            f"{MENSAJE_ARCHIVO_DANADO}"
        ) from error


def guardar_combos(datos: dict, ruta: str) -> None:
    """
    Escribe los datos de la sesión como JSON UTF-8 en `ruta`, de forma
    atómica (archivo temporal en el mismo directorio + os.replace): una
    interrupción a mitad de escritura nunca corrompe ni trunca un
    archivo de destino existente.

    Raises:
        ErrorArchivoCombos: Si no se puede escribir en el destino
            (permisos, carpeta inexistente, disco lleno).
    """
    ruta_destino = Path(ruta)
    ruta_temporal = ruta_destino.with_name(f".{ruta_destino.name}.tmp")
    try:
        contenido = json.dumps(datos, ensure_ascii=False, indent=2)
        ruta_temporal.write_text(contenido, encoding="utf-8")
        os.replace(ruta_temporal, ruta_destino)
    except OSError as error:
        if ruta_temporal.exists():
            ruta_temporal.unlink()
        raise ErrorArchivoCombos(
            f"No se pudo guardar la sesión en '{ruta_destino}'. Revisá "
            "que la carpeta exista, que tengas permisos de escritura y "
            "que haya espacio en el disco."
        ) from error
