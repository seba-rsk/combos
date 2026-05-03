from __future__ import annotations

import sys
from pathlib import Path

import yaml
import tkinter as tk
from tkinter import filedialog

from dominio.lector_yaml import leer_reglamento
from dominio.lector_plantilla import leer_plantilla, ErrorValidacionPlantilla
from dominio.generador import generar_combinaciones
from dominio.duplicados import marcar_duplicadas
from dominio.preponderancia import marcar_superadas
from infraestructura.generador_plantilla import generar_plantilla
from infraestructura.lector_excel import (
    leer_excel,
    ErrorArchivoExcel,
    ErrorFormatoPlantilla,
    ErrorDatoFila,
)
from infraestructura.exportador import exportar
from dominio.formateador import formatear_componentes
from version import VERSION
from infraestructura.rutas import (
    RUTA_PROFILES,
    RUTA_EXPORTADORES,
)
from infraestructura.config_interna import CONFIG_PLANTILLA, CONFIG_RESUMEN
from cli.consola import (
    mostrar_bienvenida,
    mostrar_separador,
    mostrar_exito,
    mostrar_info,
    mostrar_advertencia,
    mostrar_error,
    mostrar_procesando,
    mostrar_lista_archivos,
    mostrar_errores_validacion,
    mostrar_tabla_superadas,
    mostrar_ayuda_descartar,
    mostrar_error_indices,
    mostrar_tabla_resumen,
    pedir_input,
    pedir_confirmacion,
    pedir_enter,
)


# ── Punto de entrada ──────────────────────────────────────────────────────────

def ejecutar_flujo() -> None:
    mostrar_bienvenida(VERSION)

    reglamento, nombre_perfil = _paso_cargar_reglamento()

    _paso_generar_plantilla_si_el_usuario_lo_desea(reglamento, nombre_perfil, nombre_perfil)

    estados_crudos = _paso_leer_excel_del_usuario(reglamento)

    estados_enriquecidos = _paso_validar_plantilla(estados_crudos, reglamento)

    combinaciones = _paso_generar_combinaciones(estados_enriquecidos, reglamento)

    combinaciones = _paso_marcar_duplicadas(combinaciones)

    combinaciones = _paso_marcar_superadas(combinaciones, reglamento)

    _paso_resolver_combinaciones_superadas(combinaciones)

    _paso_mostrar_resumen(combinaciones)

    _paso_exportar(combinaciones, estados_crudos, estados_enriquecidos, reglamento, nombre_perfil)


# ── Paso 2 ────────────────────────────────────────────────────────────────────

def _paso_cargar_reglamento() -> tuple[dict, str]:
    mostrar_separador("Reglamento")
    ruta_yaml = _pedir_archivo_de_directorio(
        directorio=RUTA_PROFILES,
        extension=".yaml",
        descripcion_tipo="reglamento",
        seccion="Reglamento",
    )
    mostrar_procesando(f"Cargando reglamento: {ruta_yaml.name} ...")
    try:
        reglamento = leer_reglamento(str(ruta_yaml))
    except (FileNotFoundError, ValueError) as error:
        _terminar_con_error(str(error))

    nombre_reglamento = reglamento["metadata"]["code_name"]
    mostrar_exito(f"Reglamento cargado: {nombre_reglamento}")
    return reglamento, ruta_yaml.name


# ── Paso 3 ────────────────────────────────────────────────────────────────────

def _paso_generar_plantilla_si_el_usuario_lo_desea(reglamento: dict, nombre_yaml: str, nombre_perfil: str) -> None:
    mostrar_separador("Plantilla")
    respuesta = pedir_confirmacion("¿Desea generar la plantilla Excel ahora?")
    if not respuesta:
        return

    ruta_destino = _pedir_ruta_destino_plantilla(nombre_yaml)
    mostrar_procesando(f"Generando plantilla en: {ruta_destino} ...")
    try:
        generar_plantilla(reglamento, str(ruta_destino), nombre_perfil, VERSION)
    except (FileNotFoundError, PermissionError, OSError) as error:
        _terminar_con_error(str(error))

    mostrar_exito(f"Plantilla generada: {ruta_destino}")


def _pedir_ruta_destino_plantilla(nombre_yaml: str) -> Path:
    nombre_sin_extension = Path(nombre_yaml).stem
    ruta_escritorio = Path.home() / "Desktop"
    ruta_por_defecto = ruta_escritorio / f"Input_COMBOS_{nombre_sin_extension}.xlsx"

    ruta = _pedir_ruta_con_dialogo(
        titulo="Guardar plantilla de estados de carga",
        modo="guardar",
        tipos_archivo=[("Excel", "*.xlsx")],
        ruta_por_defecto=ruta_por_defecto,
    )
    if ruta is not None:
        return ruta

    entrada = pedir_input(f"Ruta de destino para la plantilla [Enter = {ruta_por_defecto}]:").strip()
    if not entrada:
        return ruta_por_defecto
    ruta = Path(entrada)
    if ruta.suffix.lower() != ".xlsx":
        ruta = ruta.with_suffix(".xlsx")
    return ruta


# ── Paso 4-5 ──────────────────────────────────────────────────────────────────

def _paso_leer_excel_del_usuario(reglamento: dict) -> list[dict]:
    mostrar_separador("Datos de entrada")
    config_plantilla = _leer_config_plantilla()
    ruta_excel = _pedir_ruta_excel_completado()

    mostrar_procesando(f"Leyendo archivo: {ruta_excel} ...")
    try:
        estados = leer_excel(str(ruta_excel), config_plantilla)
    except (ErrorArchivoExcel, ErrorFormatoPlantilla, ErrorDatoFila) as error:
        _terminar_con_error(str(error))

    mostrar_exito(f"Se leyeron {len(estados)} estado(s) de carga.")
    return estados


def _leer_config_plantilla() -> dict:
    return CONFIG_PLANTILLA


def _pedir_ruta_excel_completado() -> Path:
    pedir_enter("Presione Enter para abrir el explorador de archivos y seleccionar la planilla completada:")
    ruta_por_defecto = Path.home() / "Desktop"

    ruta = _pedir_ruta_con_dialogo(
        titulo="Seleccionar archivo Excel completado",
        modo="abrir",
        tipos_archivo=[("Excel", "*.xlsx")],
        ruta_por_defecto=ruta_por_defecto / "estados_de_carga.xlsx",
    )
    if ruta is not None:
        return ruta

    while True:
        entrada = pedir_input("Ruta del archivo Excel completado:").strip()
        if not entrada:
            mostrar_advertencia("La ruta no puede estar vacía.")
            continue
        ruta = Path(entrada)
        if not ruta.exists():
            mostrar_advertencia(f"No se encontró el archivo: '{ruta}'")
            continue
        return ruta


# ── Paso 6 ────────────────────────────────────────────────────────────────────

def _paso_validar_plantilla(estados_crudos: list[dict], reglamento: dict) -> list[dict]:
    try:
        estados_enriquecidos = leer_plantilla(estados_crudos, reglamento)
    except ErrorValidacionPlantilla as error:
        mostrar_errores_validacion(error.errores)
        sys.exit(1)

    return estados_enriquecidos


# ── Paso 7 ────────────────────────────────────────────────────────────────────

def _paso_generar_combinaciones(estados: list[dict], reglamento: dict) -> list[dict]:
    mostrar_separador("Procesamiento")
    combinaciones = generar_combinaciones(estados, reglamento)
    mostrar_info(f"Combinaciones generadas: [bold]{len(combinaciones)}[/bold]")
    return combinaciones


# ── Paso 8 ────────────────────────────────────────────────────────────────────

def _paso_marcar_duplicadas(combinaciones: list[dict]) -> list[dict]:
    combinaciones = marcar_duplicadas(combinaciones)
    cantidad_duplicadas = sum(1 for c in combinaciones if c["es_duplicada"])
    if cantidad_duplicadas == 0:
        mostrar_info("Duplicados encontrados: ninguno.")
    else:
        mostrar_advertencia(
            f"Duplicados encontrados: [bold]{cantidad_duplicadas}[/bold]  "
            "[dim](serán eliminadas del resultado)[/dim]"
        )
    return combinaciones


# ── Paso 9 ────────────────────────────────────────────────────────────────────

def _paso_marcar_superadas(combinaciones: list[dict], reglamento: dict) -> list[dict]:
    combinaciones = marcar_superadas(combinaciones, reglamento["permanent_load_types"])
    superadas = [c for c in combinaciones if c["esta_superada"]]

    if not superadas:
        mostrar_info("Combinaciones superadas por preponderancia: ninguna.")

    return combinaciones


# ── Paso 10 ───────────────────────────────────────────────────────────────────

def _paso_resolver_combinaciones_superadas(combinaciones: list[dict]) -> None:
    superadas = [c for c in combinaciones if c["esta_superada"]]
    if not superadas:
        return

    mostrar_separador("Combinaciones superadas")
    indice_por_generacion = {c["indice_generacion"]: c for c in combinaciones}
    mostrar_tabla_superadas(superadas, indice_por_generacion)
    indices_a_descartar = _pedir_indices_a_descartar(superadas)

    for combinacion in superadas:
        combinacion["descartada_por_usuario"] = (
            combinacion["indice_generacion"] in indices_a_descartar
        )


def _pedir_indices_a_descartar(superadas: list[dict]) -> set[int]:
    indices_validos = {c["indice_generacion"] for c in superadas}
    mostrar_ayuda_descartar()

    while True:
        entrada = pedir_input("Descartar #:").strip().lower()

        if entrada == "":
            return set()

        if entrada == "all":
            return set(indices_validos)

        indices, error = _parsear_indices(entrada, indices_validos)
        if error:
            mostrar_error_indices(error)
            continue
        return indices


def _parsear_indices(entrada: str, indices_validos: set[int]) -> tuple[set[int], str | None]:
    partes = entrada.split("-")
    indices = set()
    for parte in partes:
        parte = parte.strip()
        if not parte.isdigit():
            return set(), f"'{parte}' no es un número válido."
        numero = int(parte)
        if numero not in indices_validos:
            return set(), f"#{numero} no está en la lista de combinaciones superadas."
        indices.add(numero)
    return indices, None


def _paso_mostrar_resumen(combinaciones: list[dict]) -> None:
    mostrar_separador("Resumen")
    mostrar_tabla_resumen(combinaciones)


# ── Paso 11 ───────────────────────────────────────────────────────────────────

def _paso_exportar(
    combinaciones: list[dict],
    estados_crudos: list[dict],
    estados: list[dict],
    reglamento: dict,
    nombre_perfil: str,
) -> None:
    mostrar_separador("Exportación")
    config_resumen = _leer_config_resumen()

    ruta_exportador = _pedir_archivo_de_directorio(
        directorio=RUTA_EXPORTADORES,
        extension=".yaml",
        descripcion_tipo="exportador",
    )
    config_exportador = _leer_config_exportador(ruta_exportador)

    ruta_destino = _pedir_ruta_destino_exportacion(ruta_exportador)

    mostrar_procesando(f"Exportando combinaciones a: {ruta_destino} ...")
    try:
        exportar(
            combinaciones, estados_crudos, estados, reglamento,
            config_resumen, config_exportador, str(ruta_destino),
            nombre_perfil, VERSION,
        )
    except (ValueError, RuntimeError) as error:
        _terminar_con_error(str(error))

    cantidad_validas = sum(
        1 for c in combinaciones
        if not c["es_duplicada"] and not c["descartada_por_usuario"]
    )
    mostrar_exito(f"{cantidad_validas} combinación(es) exportada(s).")
    mostrar_exito(f"Archivo generado: {ruta_destino}")
    pedir_enter("Presioná Enter para cerrar COMBOS...")


def _leer_config_resumen() -> dict:
    return CONFIG_RESUMEN


def _leer_config_exportador(ruta_yaml: Path) -> dict:
    try:
        return yaml.safe_load(ruta_yaml.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        _terminar_con_error(f"Error al leer el perfil de exportación '{ruta_yaml.name}': {error}")


def _pedir_ruta_destino_exportacion(ruta_exportador: Path) -> Path:
    nombre_software = ruta_exportador.stem
    nombre_archivo_por_defecto = f"Output_COMBOS_{nombre_software}.xlsx"
    ruta_por_defecto = Path.home() / "Desktop" / nombre_archivo_por_defecto

    ruta_dialogo = _pedir_ruta_con_dialogo(
        titulo="Guardar archivo de exportación",
        modo="guardar",
        tipos_archivo=[("Excel", "*.xlsx")],
        ruta_por_defecto=ruta_por_defecto,
    )

    viene_del_dialogo = ruta_dialogo is not None

    while True:
        if ruta_dialogo is not None:
            ruta = ruta_dialogo
            ruta_dialogo = None
        else:
            entrada = pedir_input(
                f"Ruta de destino para el archivo de exportación [Enter = {ruta_por_defecto}]:"
            ).strip()
            viene_del_dialogo = False
            if not entrada:
                ruta = ruta_por_defecto
            else:
                ruta = Path(entrada)
                if ruta.suffix.lower() != ".xlsx":
                    ruta = ruta.with_suffix(".xlsx")

        if ruta.exists():
            if _archivo_esta_abierto(ruta):
                mostrar_advertencia(
                    f"El archivo '{ruta.name}' está abierto. "
                    "Cerralo e intentá de nuevo, o ingresá otra ruta."
                )
                viene_del_dialogo = False
                continue
            if not viene_del_dialogo:
                confirmacion = pedir_confirmacion(
                    f"El archivo '{ruta.name}' ya existe. ¿Sobreescribir?"
                )
                if not confirmacion:
                    continue

        return ruta


# ── Helpers de interacción ────────────────────────────────────────────────────

def _pedir_archivo_de_directorio(
    directorio: Path,
    extension: str,
    descripcion_tipo: str,
    seccion: str | None = None,
) -> Path:
    archivos = sorted(directorio.glob(f"*{extension}"))
    if not archivos:
        _terminar_con_error(
            f"No se encontraron archivos {extension} en '{directorio}'."
        )

    mostrar_lista_archivos(archivos, descripcion_tipo)

    def reimprimir():
        mostrar_separador(seccion)
        mostrar_lista_archivos(archivos, descripcion_tipo)

    while True:
        entrada = pedir_input(
            f"Elija un {descripcion_tipo} (1-{len(archivos)}):",
            al_activar=reimprimir if seccion else None,
        ).strip()
        if not entrada.isdigit():
            mostrar_advertencia(f"Ingrese un número entre 1 y {len(archivos)}.")
            continue
        indice = int(entrada) - 1
        if not (0 <= indice < len(archivos)):
            mostrar_advertencia(f"Ingrese un número entre 1 y {len(archivos)}.")
            continue
        return archivos[indice]


def _terminar_con_error(mensaje: str) -> None:
    mostrar_error(mensaje)
    input("\n  Presioná Enter para cerrar...")
    sys.exit(1)


def _archivo_esta_abierto(ruta: Path) -> bool:
    try:
        ruta.rename(ruta)
        return False
    except OSError:
        return True


def _pedir_ruta_con_dialogo(
    titulo: str,
    modo: str,
    tipos_archivo: list[tuple],
    ruta_por_defecto: Path,
) -> Path | None:
    try:
        raiz = tk.Tk()
        raiz.withdraw()
        raiz.attributes("-topmost", True)
        if modo == "abrir":
            ruta = filedialog.askopenfilename(
                title=titulo,
                filetypes=tipos_archivo,
                initialdir=str(ruta_por_defecto.parent),
            )
        else:
            ruta = filedialog.asksaveasfilename(
                title=titulo,
                filetypes=tipos_archivo,
                initialdir=str(ruta_por_defecto.parent),
                initialfile=ruta_por_defecto.name,
                defaultextension=tipos_archivo[0][1].replace("*", ""),
            )
        raiz.destroy()
        return Path(ruta) if ruta else None
    except Exception:
        return None
