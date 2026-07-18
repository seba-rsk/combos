"""
Escritura del log técnico de errores.

Centraliza el formato de las entradas, la creación de la carpeta del
log, el saneo de caracteres de control y el tope de tamaño del archivo.
Los llamadores (`cli/main.py`, `cli/flujo.py`) solo aportan el contexto
y el cuerpo de cada entrada; qué ruta usa el log lo decide
`infraestructura/rutas.py`.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from combos.version import VERSION

# Tamaño máximo del log de errores. Al superarlo se conserva solo la
# mitad más reciente: el archivo nunca crece sin límite.
MAX_BYTES_LOG = 1024 * 1024

# Formato de fecha y hora de las entradas del log de errores.
FORMATO_TIMESTAMP_LOG = "%Y-%m-%d %H:%M:%S"

# Aviso que encabeza el log después de un recorte por tamaño.
_MARCA_RECORTE = "(entradas más viejas eliminadas por tamaño)\n"

# Caracteres de control, salvo el salto de línea que estructura los
# tracebacks. Un nombre de archivo hostil podría usarlos para inyectar
# líneas falsas en el log o corromper su lectura.
_CONTROL_SIN_SALTO = re.compile(r"[\x00-\x09\x0b-\x1f\x7f]")

# Variante estricta para el encabezado de cada entrada, que es una
# única línea por diseño: neutraliza también los saltos de línea, para
# que la garantía anti-inyección no dependa de qué interpolen los
# llamadores en el contexto.
_CONTROL_TODOS = re.compile(r"[\x00-\x1f\x7f]")


def sanear_texto_log(texto: str) -> str:
    """
    Reemplaza los caracteres de control del texto por el marcador
    visible «�», conservando los saltos de línea.

    Args:
        texto: Texto libre que va a escribirse en el log.

    Returns:
        El texto con los caracteres de control neutralizados.
    """
    return _CONTROL_SIN_SALTO.sub("�", texto)


def anexar_entrada_log(ruta_log: Path, contexto: str, cuerpo: str) -> bool:
    """
    Agrega una entrada al log de errores, creando la carpeta si no
    existe y recortando el archivo si superó el tamaño máximo.

    Args:
        ruta_log: Ruta del archivo de log.
        contexto: Descripción breve de dónde ocurrió el error.
        cuerpo: Detalle técnico (traceback o mensaje de la excepción).

    Returns:
        True si la entrada quedó escrita; False si el log no se pudo
        escribir (carpeta de solo lectura, disco lleno). El llamador
        decide si eso amerita avisarle algo al usuario.
    """
    timestamp = datetime.now().strftime(FORMATO_TIMESTAMP_LOG)
    try:
        ruta_log.parent.mkdir(parents=True, exist_ok=True)
        _acotar_tamano(ruta_log)
        with open(ruta_log, "a", encoding="utf-8") as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(
                f"  COMBOS v{VERSION}  —  {timestamp}  —  "
                f"{_CONTROL_TODOS.sub('�', contexto)}\n"
            )
            f.write(f"{'=' * 60}\n")
            f.write(sanear_texto_log(cuerpo))
            if not cuerpo.endswith("\n"):
                f.write("\n")
        return True
    except OSError:
        return False


def _acotar_tamano(ruta_log: Path) -> None:
    """
    Si el log supera MAX_BYTES_LOG, conserva solo la mitad más reciente
    con un aviso al inicio. Se corta por bytes y se decodifica con
    reemplazo: perder medio carácter en el borde del recorte no importa
    en un archivo de diagnóstico.
    """
    if not ruta_log.exists() or ruta_log.stat().st_size <= MAX_BYTES_LOG:
        return
    cola = ruta_log.read_bytes()[-(MAX_BYTES_LOG // 2):]
    texto = cola.decode("utf-8", errors="replace")
    ruta_log.write_text(_MARCA_RECORTE + texto, encoding="utf-8")
