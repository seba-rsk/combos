from __future__ import annotations

import sys
import traceback
from datetime import datetime

from infraestructura.rutas import RUTA_LOG
from version import VERSION

LOG_PATH = RUTA_LOG


def main() -> None:
    try:
        from cli.flujo import ejecutar_flujo
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
        _escribir_log_error()
        print("\n" + "=" * 52)
        print("  Ocurrió un error inesperado en COMBOS.")
        print(f"  Se guardó un informe en:\n  {LOG_PATH}")
        print("  Enviá ese archivo para recibir soporte.")
        print("=" * 52)
        input("\n  Presioná Enter para cerrar...")
        sys.exit(1)


def _escribir_log_error() -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 60}\n")
        f.write(f"  COMBOS v{VERSION}  —  {timestamp}\n")
        f.write(f"{'=' * 60}\n")
        f.write(traceback.format_exc())


if __name__ == "__main__":
    main()
