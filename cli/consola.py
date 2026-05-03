from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich import box

import time

from dominio.formateador import formatear_componentes


console = Console()


# ── Estructura ────────────────────────────────────────────────────────────────

def mostrar_bienvenida(version: str) -> None:
    console.print()
    console.print(Panel(
        Text.assemble(
            ("COMBOS", "bold white"),
            (f"  v{version}", "dim white"),
            ("\nGenerador de combinaciones de carga estructural para ingeniería civil", "dim white"),
            ("\n\n\nRepo: ", "dim white"),
            ("github.com/seba-rsk/combos", "dim cyan link https://github.com/seba-rsk/combos"),
        ),
        box=box.ROUNDED,
        border_style="grey50",
        padding=(0, 2),
    ))


def mostrar_separador(titulo: str) -> None:
    console.print()
    time.sleep(0.3)
    console.print(Rule(title=titulo, style="grey50", align="left"))


# ── Mensajes de estado ────────────────────────────────────────────────────────

def mostrar_exito(mensaje: str) -> None:
    console.print(f"  [green]✓[/green]  {mensaje}")


def mostrar_info(mensaje: str) -> None:
    console.print(f"  {mensaje}")


def mostrar_advertencia(mensaje: str) -> None:
    console.print(f"  [yellow]![/yellow]  {mensaje}")


def mostrar_error(mensaje: str) -> None:
    console.print()
    console.print(f"  [bold red]Error:[/bold red] {mensaje}")
    console.print()


def mostrar_procesando(mensaje: str) -> None:
    console.print(f"  [dim]{mensaje}[/dim]")


# ── Listas de archivos ────────────────────────────────────────────────────────

def mostrar_lista_archivos(archivos: list[Path], descripcion_tipo: str) -> None:
    console.print()
    console.print(f"  [bold]Archivos de {descripcion_tipo} disponibles:[/bold]")
    for numero, archivo in enumerate(archivos, start=1):
        console.print(f"    [dim]{numero}.[/dim]  {archivo.name}")


# ── Errores de validación ─────────────────────────────────────────────────────

def mostrar_errores_validacion(errores: list[str]) -> None:
    console.print()
    console.print(f"  [bold red]Se encontraron {len(errores)} error(es) en la plantilla:[/bold red]")
    for error in errores:
        console.print(f"    [red]•[/red]  {error}")
    console.print()


# ── Tabla de combinaciones superadas ─────────────────────────────────────────

def mostrar_tabla_superadas(
    superadas: list[dict],
    indice_por_generacion: dict[int, dict],
) -> None:
    console.print()
    console.print(
        f"  [bold]Combinaciones superadas por preponderancia:[/bold]  "
        f"[yellow]{len(superadas)}[/yellow]"
    )

    por_estado_limite: dict[str, list[dict]] = {}
    for combinacion in superadas:
        estado = combinacion["estado_limite"]
        if estado not in por_estado_limite:
            por_estado_limite[estado] = []
        por_estado_limite[estado].append(combinacion)

    for estado_limite, grupo in por_estado_limite.items():
        console.print()
        console.print(f"  [grey50]{estado_limite} {'─' * 60}[/grey50]")

        por_dominante: dict[int, list[dict]] = {}
        for combinacion in grupo:
            dominante_id = combinacion["superada_por"]
            if dominante_id not in por_dominante:
                por_dominante[dominante_id] = []
            por_dominante[dominante_id].append(combinacion)

        for dominante_id, superadas_por_esta in sorted(por_dominante.items()):
            dominante = indice_por_generacion.get(dominante_id)
            componentes_dominante = (
                formatear_componentes(dominante["componentes"]) if dominante else "?"
            )

            tabla = Table(
                box=box.SIMPLE,
                show_header=False,
                padding=(0, 1),
                show_edge=False,
            )
            tabla.add_column(style="dim white", no_wrap=True)
            tabla.add_column(style="white")

            tabla.add_row(
                Text(f"superada por  #{dominante_id}", style="dim"),
                Text(componentes_dominante, style="bold cyan"),
            )

            for combinacion in superadas_por_esta:
                indice = combinacion["indice_generacion"]
                componentes = formatear_componentes(combinacion["componentes"])
                tabla.add_row(
                    Text(f"  #{indice}", style="yellow"),
                    Text(componentes),
                )

            console.print(tabla)


# ── Ayuda para input de descarte ──────────────────────────────────────────────

def mostrar_ayuda_descartar() -> None:
    console.print()
    console.print(
        "  [dim]all[/dim] · todas    "
        "[dim]Enter[/dim] · ninguna    "
        "IDs separados por [dim]-[/dim]"
    )


def mostrar_error_indices(mensaje: str) -> None:
    console.print(f"  [red]✗[/red]  {mensaje}")


# ── Prompt de input ───────────────────────────────────────────────────────────

def pedir_input(pregunta: str, al_activar=None) -> str:
    while True:
        respuesta = console.input(f"  [bold]{pregunta}[/bold] ")
        if al_activar is not None and _chequear_activacion(respuesta):
            al_activar()
            continue
        return respuesta


def pedir_confirmacion(pregunta: str) -> bool:
    respuesta = console.input(f"  [bold]{pregunta}[/bold] [dim]\\[s/N][/dim]: ").strip().lower()
    return respuesta in ("s", "sí", "si")


def pedir_enter(mensaje: str) -> None:
    console.input(f"  [dim]{mensaje}[/dim] ")


def mostrar_tabla_resumen(combinaciones: list[dict]) -> None:
    validas = [
    c for c in combinaciones
    if not c["es_duplicada"] and not c["descartada_por_usuario"]
    ]

    console.print()
    console.print(
        f"  [bold]Combinaciones resultantes:[/bold]  "
        f"[green]{len(validas)}[/green]"
    )

    por_estado_limite: dict[str, list[dict]] = {}
    for combinacion in validas:
        estado = combinacion["estado_limite"]
        if estado not in por_estado_limite:
            por_estado_limite[estado] = []
        por_estado_limite[estado].append(combinacion)

    for estado_limite, grupo in por_estado_limite.items():
        console.print()
        console.print(f"  [grey50]{estado_limite} {'─' * 60}[/grey50]")

        tabla = Table(
            box=box.SIMPLE,
            show_header=False,
            padding=(0, 1),
            show_edge=False,
        )
        tabla.add_column(no_wrap=True)
        tabla.add_column(style="white")

        for combinacion in grupo:
            componentes = formatear_componentes(combinacion["componentes"])
            tabla.add_row(
                Text(f"#{combinacion['indice_generacion']}", style="yellow"),
                componentes,
            )

        console.print(tabla)

    console.print()
    pedir_enter("Presione Enter para continuar con la exportación:")


def _chequear_activacion(texto: str) -> bool:
    import hashlib
    import base64

    h = "66c0678b0e331c54d77b05176dae0254937fe66d905f628d5859bde341d947c0"
    m = (
            "SGF5IHVuIHB1bnRvIHNpbiBub21icmUgZW4gbGEgZ2VvbG9nw61hIGRvbmRlIGxh"
            "IG1hdGVyaWEgb3Jnw6FuaWNhIGRlamEgZGUgc2VybG8uIE5vIGhheSBldmVudG8s"
            "IG5vIGhheSBmcm9udGVyYSB2aXNpYmxlLiBTb2xvIHByZXNpw7NuLCB0aWVtcG8s"
            "IHkgbGEgZWxpbWluYWNpw7NuIGxlbnRhIGRlIHRvZG8gbG8gcXVlIHNvYnJhLiBM"
            "byBxdWUgZW1lcmdlIGRlbCBvdHJvIGxhZG8gZXMgYW50cmFjaXRhOiBtaW5lcmFs"
            "IHB1cm8sIGRlbnNvLCBzaW4gaGlzdG9yaWEgbGVnaWJsZS4gRWwgY2FyYm9ubyBl"
            "biBzdSBmb3JtYSBtw6FzIGFsdGEuCgpEZSBhaMOtIHZpZW5lIEFOVFJBLiBZIENP"
            "TUJPUyBlcyBlbCBwcmltZXJvLgoKRW5jb250cmFzdGUgZXN0by4gQmllbnZlbmlk"
            "by4="
        )

    if hashlib.sha256(texto.strip().lower().encode()).hexdigest() != h:
        return False

    console.print()
    console.print()
    console.print()
    # console.print(Panel(
    #     Text(base64.b64decode(m).decode(), justify="center"),
    #     box=box.DOUBLE,
    #     border_style="gold1",
    #     padding=(1, 4),
    # ))

    decoded = base64.b64decode(m).decode().strip()

    clave = bytes([65,78,84,82,65]).decode()

    t = Text(justify="center")
    lineas = decoded.strip().splitlines()
    for i, line in enumerate(lineas):
        sufijo = "\n" if i < len(lineas) - 1 else ""
        if clave in line:
            before, match, after = line.partition(clave)
            t.append(before)
            t.append(clave, style="bold cyan")
            t.append(after + sufijo)
        else:
            t.append(line + sufijo)

    console.print(Panel(
            t,
            box=box.DOUBLE,
            border_style="steel_blue1",
            title="· · ·",
            title_align="center",
            padding=(1, 4),
            ))
    console.print()
    console.print()
    console.input("")
    return True
