from __future__ import annotations

import sys
import traceback
from datetime import datetime

from combos.cli.constantes import FORMATO_TIMESTAMP_LOG
from combos.infraestructura.rutas import RUTA_LOG
from combos.version import VERSION


def main() -> None:
    """
    Punto de entrada de COMBOS: ejecuta el flujo completo y convierte
    cualquier error inesperado en un mensaje amable más un informe en el
    log, sin exponer detalles técnicos en pantalla.
    """
    try:
        from combos.cli.flujo import ejecutar_flujo
        ejecutar_flujo()

    except KeyboardInterrupt:
        from rich.console import Console
        Console().print(
            "\n\n  [dim]Operación cancelada por el usuario.[/dim]\n"
        )
        sys.exit(0)

    except SystemExit:
        # sys.exit() lanzado por _terminar_con_error en flujo.py —
        # dejar pasar.
        raise

    except Exception:
        _mostrar_error_fatal(log_guardado=_escribir_log_error())
        input("\n  Presioná Enter para cerrar...")
        sys.exit(1)


def _escribir_log_error() -> bool:
    """
    Intenta registrar el traceback en el log de errores. Devuelve False
    si el log no se puede escribir (ej. carpeta de solo lectura): en ese
    caso el error igual se informa en pantalla con el mensaje amable,
    nunca con el traceback crudo.
    """
    timestamp = datetime.now().strftime(FORMATO_TIMESTAMP_LOG)
    try:
        with open(RUTA_LOG, "a", encoding="utf-8") as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"  COMBOS v{VERSION}  —  {timestamp}\n")
            f.write(f"{'=' * 60}\n")
            f.write(traceback.format_exc())
        return True
    except OSError:
        return False


def _mostrar_error_fatal(log_guardado: bool) -> None:
    """Informa en pantalla un error inesperado, sin jerga técnica."""
    print("\n" + "=" * 52)
    print("  Ocurrió un error inesperado en COMBOS.")
    if log_guardado:
        print(f"  Se guardó un informe en:\n  {RUTA_LOG}")
        print("  Enviá ese archivo para recibir soporte.")
    else:
        print("  No se pudo guardar el informe del error: la carpeta")
        print("  del programa no permite escribir. Ejecutá COMBOS desde")
        print("  una carpeta con permisos de escritura y repetí el caso.")
    print("=" * 52)


if __name__ == "__main__":
    main()
