from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from cli.constantes import (
    ANCHO_DESIGNACIONES_AFECTADAS,
    ANCHO_SEPARADOR_ESTADO,
    FILAS_POR_PAGINA,
    PAUSA_SEPARADOR_SEGUNDOS,
)
from dominio.formateador import formatear_componentes
from dominio.modelos import (
    Combinacion,
    EleccionParametro,
    ParametroReglamento,
)
from dominio.sesion import Sesion

console = Console()


# ── Estructura ────────────────────────────────────────────────────────────────

def mostrar_bienvenida(version: str) -> None:
    """Muestra el panel de bienvenida con la versión y el enlace al repo."""
    console.print()
    console.print(Panel(
        Text.assemble(
            ("COMBOS", "bold white"),
            (f"  v{version}", "dim white"),
            (
                "\nGenerador de combinaciones de carga estructural "
                "para ingeniería civil",
                "dim white",
            ),
            ("\n\n\nRepo: ", "dim white"),
            (
                "github.com/seba-rsk/combos",
                "dim cyan link https://github.com/seba-rsk/combos",
            ),
        ),
        box=box.ROUNDED,
        border_style="grey50",
        padding=(0, 2),
    ))


def mostrar_separador(titulo: str) -> None:
    """Imprime la línea separadora que abre cada sección del flujo."""
    console.print()
    time.sleep(PAUSA_SEPARADOR_SEGUNDOS)
    console.print(Rule(title=titulo, style="grey50", align="left"))


# ── Inicio y sesiones guardadas ───────────────────────────────────────────────

def mostrar_menu_inicio() -> None:
    """Muestra las opciones de la pantalla de inicio del flujo."""
    console.print()
    console.print("  [bold]¿Qué querés hacer?[/bold]")
    console.print()
    console.print("    [dim]1.[/dim]  Empezar una sesión nueva")
    console.print("    [dim]2.[/dim]  Abrir una sesión guardada (.combos)")
    console.print()


def mostrar_resumen_restauracion(
    sesion: Sesion,
    nombre_archivo: str,
    fecha_guardado: str,
    version_combos: str,
) -> None:
    """
    Resume qué se restauró al abrir una sesión guardada: origen y fecha
    del archivo, reglamento, estados de carga, elecciones de parámetros
    y combinaciones regeneradas con sus descartes reaplicados.
    """
    mostrar_exito(f"Sesión abierta: {nombre_archivo}")
    mostrar_info(
        f"[dim]Guardada el {_formatear_fecha_guardado(fecha_guardado)} "
        f"con COMBOS v{escape(version_combos)}.[/dim]"
    )
    nombre_reglamento = sesion.reglamento["metadata"]["code_name"]
    mostrar_info(
        f"Reglamento: [bold]{escape(nombre_reglamento)}[/bold] "
        f"[dim]({escape(sesion.nombre_perfil)})[/dim]"
    )
    mostrar_info(
        f"Estados de carga: [bold]{len(sesion.estados_crudos)}[/bold]"
    )
    for eleccion in sesion.elecciones:
        mostrar_info(
            f"Parámetro — {escape(eleccion.nombre)}: {eleccion.valor} "
            f"[dim]({escape(eleccion.etiqueta)})[/dim]"
        )
    descartes = sum(
        1 for c in sesion.combinaciones if c.descartada_por_usuario
    )
    mostrar_info(
        f"Combinaciones regeneradas: "
        f"[bold]{len(sesion.combinaciones)}[/bold] — "
        f"descartes reaplicados: [bold]{descartes}[/bold]"
    )


def _formatear_fecha_guardado(fecha_iso: str) -> str:
    """
    Convierte la fecha ISO guardada en el archivo a dd/mm/aaaa. Si el
    texto no es una fecha válida, lo devuelve tal cual: la fecha es
    informativa y no justifica rechazar la sesión.
    """
    try:
        return datetime.fromisoformat(fecha_iso).strftime("%d/%m/%Y")
    except ValueError:
        return escape(fecha_iso)


# ── Mensajes de estado ────────────────────────────────────────────────────────
#
# Política de escape de markup: los mensajes que interpolan texto libre
# (de un YAML, de una celda de Excel o del teclado) se escapan acá, en el
# punto de impresión — mostrar_exito, mostrar_error, mostrar_procesando y
# los mensajes de validación. mostrar_info y mostrar_advertencia quedan
# sin escapar porque sus llamadores usan markup a propósito ([bold],
# [dim]) y solo interpolan números o texto propio del programa.

def mostrar_exito(mensaje: str) -> None:
    """Muestra un mensaje de operación completada, con tilde verde."""
    console.print(f"  [green]✓[/green]  {escape(mensaje)}")


def mostrar_info(mensaje: str) -> None:
    """Muestra un mensaje informativo; el llamador puede usar markup."""
    console.print(f"  {mensaje}")


def mostrar_advertencia(mensaje: str) -> None:
    """Muestra una advertencia no fatal; el llamador puede usar markup."""
    console.print(f"  [yellow]![/yellow]  {mensaje}")


def mostrar_error(mensaje: str) -> None:
    """Muestra el error de una operación que no pudo completarse."""
    console.print()
    console.print(f"  [bold red]Error:[/bold red] {escape(mensaje)}")
    console.print()


def mostrar_procesando(mensaje: str) -> None:
    """Muestra en dim qué operación está en curso."""
    console.print(f"  [dim]{escape(mensaje)}[/dim]")


# ── Listas de archivos ────────────────────────────────────────────────────────

def mostrar_lista_archivos(archivos: list[Path], descripcion_tipo: str) -> None:
    """Lista numerada de archivos disponibles para elegir uno."""
    console.print()
    console.print(f"  [bold]Archivos de {descripcion_tipo} disponibles:[/bold]")
    for numero, archivo in enumerate(archivos, start=1):
        console.print(f"    [dim]{numero}.[/dim]  {escape(archivo.name)}")


# ── Parámetros del reglamento ─────────────────────────────────────────────────

def mostrar_cantidad_parametros(cantidad: int) -> None:
    """Anuncia cuántos parámetros del reglamento hay que definir."""
    console.print()
    if cantidad == 1:
        mensaje = "Este reglamento requiere definir 1 parámetro del proyecto."
    else:
        mensaje = (
            f"Este reglamento requiere definir {cantidad} parámetros "
            "del proyecto."
        )
    console.print(f"  {mensaje}")


def mostrar_menu_parametro(
    parametro: ParametroReglamento,
    tipos_afectados: list[str],
    combinaciones_afectadas: dict[str, list[str | int]],
) -> None:
    """
    Muestra el título del parámetro, la línea "Afecta a" con las
    designaciones normativas de las combinaciones que lo referencian
    (agrupadas por estado límite) y sus opciones numeradas, con el
    factor que cada opción representa alineado a la derecha en dim
    (ej. "L × 0.5"), para que el dato técnico quede visible sin competir
    con la etiqueta.
    """
    console.print()
    console.print(f"  [bold]{escape(parametro.nombre)}:[/bold]")
    _mostrar_combinaciones_afectadas(combinaciones_afectadas)
    console.print()
    ancho_etiquetas = max(
        len(opcion.etiqueta) for opcion in parametro.opciones
    )
    tipos = escape(", ".join(tipos_afectados))
    for numero, opcion in enumerate(parametro.opciones, start=1):
        relleno = " " * (ancho_etiquetas - len(opcion.etiqueta))
        console.print(
            f"    [dim]{numero}.[/dim]  {escape(opcion.etiqueta)}{relleno}  "
            f"[dim]{tipos} × {opcion.valor}[/dim]"
        )
    console.print()


def _mostrar_combinaciones_afectadas(
    afectadas: dict[str, list[str | int]],
) -> None:
    """
    Escribe la línea "Afecta a" del menú de parámetros: una línea por
    estado límite con las designaciones normativas de las combinaciones
    afectadas, envueltas con sangría colgante si superan el ancho
    máximo. Las combinaciones sin designación se muestran como "id N".
    """
    if not afectadas:
        return
    etiqueta = "Afecta a:"
    sangria_estado = " " * (2 + len(etiqueta) + 2)
    es_primer_estado = True
    for id_estado, designaciones in afectadas.items():
        lineas = _envolver_designaciones(
            designaciones, ANCHO_DESIGNACIONES_AFECTADAS
        )
        sangria_texto = sangria_estado + " " * (len(id_estado) + 3)
        for numero_linea, linea in enumerate(lineas):
            if numero_linea > 0:
                console.print(f"{sangria_texto}{escape(linea)}")
            elif es_primer_estado:
                console.print(
                    f"  [dim]{etiqueta}[/dim]  "
                    f"[dim]{escape(id_estado)} ·[/dim] {escape(linea)}"
                )
            else:
                console.print(
                    f"{sangria_estado}[dim]{escape(id_estado)} ·[/dim] "
                    f"{escape(linea)}"
                )
        es_primer_estado = False


def _envolver_designaciones(
    designaciones: list[str | int], ancho_maximo: int
) -> list[str]:
    lineas: list[str] = []
    actual = ""
    for designacion in designaciones:
        texto = (
            designacion
            if isinstance(designacion, str)
            else f"id {designacion}"
        )
        candidata = f"{actual}, {texto}" if actual else texto
        if actual and len(candidata) > ancho_maximo:
            lineas.append(f"{actual},")
            actual = texto
        else:
            actual = candidata
    lineas.append(actual)
    return lineas


def mostrar_eleccion_confirmada(eleccion: EleccionParametro) -> None:
    """
    Confirma en pantalla la opción elegida para un parámetro, repitiendo
    nombre, valor y etiqueta para que lo que quedó aplicado nunca sea
    ambiguo. El nombre y la etiqueta son texto libre del YAML.
    """
    console.print(
        f"  [green]✓[/green]  {escape(eleccion.nombre)}: {eleccion.valor} "
        f"— {escape(eleccion.etiqueta)}"
    )


# ── Errores de validación ─────────────────────────────────────────────────────

def mostrar_errores_validacion(errores: list[str]) -> None:
    """Lista con viñetas los errores de validación de la plantilla."""
    console.print()
    console.print(
        f"  [bold red]Se encontraron {len(errores)} error(es) "
        "en la plantilla:[/bold red]"
    )
    for error in errores:
        console.print(f"    [red]•[/red]  {escape(error)}")
    console.print()


# ── Tabla de combinaciones superadas ─────────────────────────────────────────

def mostrar_tabla_superadas(
    superadas: list[Combinacion],
    indice_por_generacion: dict[int, Combinacion],
) -> None:
    """
    Muestra las combinaciones superadas agrupadas por estado límite y
    por la combinación dominante que las supera, paginando cada
    FILAS_POR_PAGINA filas.
    """
    console.print()
    console.print(
        f"  [bold]Combinaciones superadas por preponderancia:[/bold]  "
        f"[yellow]{len(superadas)}[/yellow]"
    )
    for estado_limite, grupo in _agrupar_por_estado_limite(superadas).items():
        _mostrar_grupo_de_superadas(
            estado_limite, grupo, indice_por_generacion
        )


def _mostrar_grupo_de_superadas(
    estado_limite: str,
    grupo: list[Combinacion],
    indice_por_generacion: dict[int, Combinacion],
) -> None:
    console.print()
    console.print(
        f"  [grey50]{escape(estado_limite)} "
        f"{'─' * ANCHO_SEPARADOR_ESTADO}[/grey50]"
    )
    por_dominante = _agrupar_por_dominante(grupo)
    filas_mostradas = 0
    for dominante_id, superadas_por_esta in sorted(por_dominante.items()):
        console.print(_construir_tabla_dominante(
            dominante_id, superadas_por_esta, indice_por_generacion
        ))
        filas_mostradas += 1 + len(superadas_por_esta)
        if filas_mostradas >= FILAS_POR_PAGINA:
            pedir_enter("Presioná Enter para ver más...")
            filas_mostradas = 0


def _agrupar_por_dominante(
    grupo: list[Combinacion],
) -> dict[int, list[Combinacion]]:
    por_dominante: dict[int, list[Combinacion]] = {}
    for combinacion in grupo:
        por_dominante.setdefault(combinacion.superada_por, []).append(
            combinacion
        )
    return por_dominante


def _construir_tabla_dominante(
    dominante_id: int,
    superadas_por_esta: list[Combinacion],
    indice_por_generacion: dict[int, Combinacion],
) -> Table:
    dominante = indice_por_generacion.get(dominante_id)
    componentes_dominante = (
        formatear_componentes(dominante.componentes) if dominante else "?"
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
        tabla.add_row(
            Text(f"  #{combinacion.indice_generacion}", style="yellow"),
            Text(formatear_componentes(combinacion.componentes)),
        )
    return tabla


# ── Ayuda para input de descarte ──────────────────────────────────────────────

def mostrar_ayuda_descartar() -> None:
    """Recuerda las formas válidas de responder al prompt de descarte."""
    console.print()
    console.print(
        "  [dim]all[/dim] · todas    "
        "[dim]Enter[/dim] · ninguna    "
        "IDs separados por [dim]-[/dim]"
    )


def mostrar_error_indices(mensaje: str) -> None:
    """Marca como inválida una entrada del prompt de descarte."""
    console.print(f"  [red]✗[/red]  {escape(mensaje)}")


# ── Prompt de input ───────────────────────────────────────────────────────────

def pedir_input(pregunta: str) -> str:
    """Pide una línea de texto al usuario y la devuelve sin procesar."""
    return console.input(f"  [bold]{pregunta}[/bold] ")


def pedir_seleccion_de_archivo(pregunta: str, al_reimprimir=None) -> str:
    """
    Como pedir_input, pero además vuelve a pedir la selección si el
    usuario escribió la frase de activación de un mensaje oculto (ver
    _chequear_activacion), reimprimiendo antes la lista de archivos.
    """
    while True:
        respuesta = pedir_input(pregunta)
        if al_reimprimir is not None and _chequear_activacion(respuesta):
            al_reimprimir()
            continue
        return respuesta


def pedir_confirmacion(pregunta: str) -> bool:
    """Pregunta sí/no; cualquier respuesta distinta de sí cuenta como no."""
    respuesta = console.input(
        f"  [bold]{pregunta}[/bold] [dim]\\[s/N][/dim]: "
    ).strip().lower()
    return respuesta in ("s", "sí", "si")


def pedir_enter(mensaje: str) -> None:
    """Pausa hasta que el usuario presione Enter."""
    console.input(f"  [dim]{mensaje}[/dim] ")


def mostrar_tabla_resumen(resultantes: list[Combinacion]) -> None:
    """
    Muestra las combinaciones resultantes agrupadas por estado límite,
    paginando cada FILAS_POR_PAGINA filas. Recibe la lista ya filtrada
    (ver dominio.sesion.combinaciones_resultantes).
    """
    console.print()
    console.print(
        f"  [bold]Combinaciones resultantes:[/bold]  "
        f"[green]{len(resultantes)}[/green]"
    )
    for estado_limite, grupo in _agrupar_por_estado_limite(resultantes).items():
        _mostrar_grupo_de_estado_limite(estado_limite, grupo)
    console.print()
    pedir_enter("Presioná Enter para continuar con la exportación:")


def _agrupar_por_estado_limite(
    combinaciones: list[Combinacion],
) -> dict[str, list[Combinacion]]:
    grupos: dict[str, list[Combinacion]] = {}
    for combinacion in combinaciones:
        grupos.setdefault(combinacion.estado_limite, []).append(combinacion)
    return grupos


def _mostrar_grupo_de_estado_limite(
    estado_limite: str, grupo: list[Combinacion]
) -> None:
    console.print()
    console.print(
        f"  [grey50]{escape(estado_limite)} "
        f"{'─' * ANCHO_SEPARADOR_ESTADO}[/grey50]"
    )
    for inicio in range(0, len(grupo), FILAS_POR_PAGINA):
        console.print(_construir_tabla_pagina(
            grupo[inicio:inicio + FILAS_POR_PAGINA]
        ))
        if inicio + FILAS_POR_PAGINA < len(grupo):
            pedir_enter("Presioná Enter para ver más...")


def _construir_tabla_pagina(pagina: list[Combinacion]) -> Table:
    tabla = Table(
        box=box.SIMPLE,
        show_header=False,
        padding=(0, 1),
        show_edge=False,
    )
    tabla.add_column(no_wrap=True)
    tabla.add_column(style="white")
    for combinacion in pagina:
        tabla.add_row(
            Text(f"#{combinacion.indice_generacion}", style="yellow"),
            Text(formatear_componentes(combinacion.componentes)),
        )
    return tabla


def _chequear_activacion(texto: str) -> bool:
    import base64
    import hashlib

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
