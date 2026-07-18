from __future__ import annotations

import sys
import traceback

from combos.infraestructura.log_errores import anexar_entrada_log
from combos.infraestructura.rutas import RUTA_LOG


def main() -> None:
    """
    Punto de entrada de COMBOS: ejecuta el flujo completo y convierte
    cualquier error inesperado en un mensaje amable más un informe en el
    log, sin exponer detalles técnicos en pantalla.

    Acepta opcionalmente la ruta de un archivo de sesión `.combos` como
    primer argumento del programa (doble click sobre un archivo asociado
    en Windows, o invocación manual): en ese caso el flujo abre esa
    sesión directamente, sin pasar por el menú de inicio.
    """
    try:
        from combos.cli.flujo import ejecutar_flujo
        ejecutar_flujo(ruta_combos=_argumento_ruta_combos())

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


def _argumento_ruta_combos() -> str | None:
    """
    Devuelve el primer argumento del programa (la ruta de una sesión
    `.combos`) o None si no se pasó ninguno. La validación de la ruta,
    con sus mensajes al usuario, vive en el flujo.
    """
    if len(sys.argv) > 1:
        return sys.argv[1]
    return None


def _escribir_log_error() -> bool:
    """
    Intenta registrar el traceback en el log de errores. Devuelve False
    si el log no se puede escribir (ej. carpeta de solo lectura): en ese
    caso el error igual se informa en pantalla con el mensaje amable,
    nunca con el traceback crudo.
    """
    return anexar_entrada_log(
        RUTA_LOG, "error inesperado", traceback.format_exc()
    )


def _mostrar_error_fatal(log_guardado: bool) -> None:
    """Informa en pantalla un error inesperado, sin jerga técnica."""
    print("\n" + "=" * 52)
    print("  Ocurrió un error inesperado en COMBOS.")
    if log_guardado:
        print(f"  Se guardó un informe en:\n  {RUTA_LOG}")
        print("  Enviá ese archivo para recibir soporte.")
    else:
        print("  No se pudo guardar el informe del error: la carpeta")
        print("  del log no permite escribir. Ejecutá COMBOS con permisos")
        print("  de escritura en tu carpeta de usuario y repetí el caso.")
    print("=" * 52)


if __name__ == "__main__":
    main()
