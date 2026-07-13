from __future__ import annotations

import sys
import traceback
from datetime import datetime
from pathlib import Path

import yaml
import tkinter as tk
from tkinter import filedialog

from dominio.lector_yaml import leer_reglamento
from dominio.lector_plantilla import leer_plantilla, ErrorValidacionPlantilla
from dominio.modelos import Combinacion, Estado, EstadoCrudo
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
from version import VERSION
from infraestructura.rutas import (
    RUTA_PROFILES,
    RUTA_EXPORTADORES,
    RUTA_LOG,
)
from infraestructura.config_interna import CONFIG_PLANTILLA, CONFIG_RESUMEN
from cli.constantes import (
    NOMBRE_CARPETA_ESCRITORIO,
    PREFIJO_PLANTILLA,
    PREFIJO_EXPORTACION,
    EXTENSION_EXCEL,
    EXTENSION_YAML,
    FORMATO_FECHA_ARCHIVO,
)
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
    pedir_seleccion_de_archivo,
    pedir_confirmacion,
    pedir_enter,
)


# ── Punto de entrada ──────────────────────────────────────────────────────────

def ejecutar_flujo() -> None:
    mostrar_bienvenida(VERSION)

    reglamento, nombre_perfil = _paso_cargar_reglamento()

    _paso_generar_plantilla_si_el_usuario_lo_desea(
        reglamento, nombre_perfil, nombre_perfil
    )

    estados_crudos = _paso_leer_excel_del_usuario(reglamento)

    estados_enriquecidos = _paso_validar_plantilla(estados_crudos, reglamento)

    combinaciones = _paso_generar_combinaciones(
        estados_enriquecidos, reglamento
    )

    combinaciones = _paso_marcar_duplicadas(combinaciones)

    combinaciones = _paso_marcar_superadas(combinaciones, reglamento)

    _paso_resolver_combinaciones_superadas(combinaciones)

    _paso_mostrar_resumen(combinaciones)

    if not _hay_combinaciones_validas(combinaciones):
        if not _confirmar_continuar_sin_combinaciones():
            mostrar_info("Operación finalizada sin exportar.")
            pedir_enter("Presioná Enter para cerrar COMBOS...")
            return

    _paso_exportar(
        combinaciones, estados_crudos, estados_enriquecidos,
        reglamento, nombre_perfil,
    )


# ── Paso 2 ────────────────────────────────────────────────────────────────────

def _paso_cargar_reglamento() -> tuple[dict, str]:
    mostrar_separador("Reglamento")
    ruta_yaml = _pedir_archivo_de_directorio(
        directorio=RUTA_PROFILES,
        extension=EXTENSION_YAML,
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

def _paso_generar_plantilla_si_el_usuario_lo_desea(
    reglamento: dict, nombre_yaml: str, nombre_perfil: str
) -> None:
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
    ruta_escritorio = Path.home() / NOMBRE_CARPETA_ESCRITORIO
    fecha = datetime.now().strftime(FORMATO_FECHA_ARCHIVO)
    nombre_archivo = (
        f"{PREFIJO_PLANTILLA}{nombre_sin_extension}_{fecha}{EXTENSION_EXCEL}"
    )
    ruta_por_defecto = ruta_escritorio / nombre_archivo

    ruta = _pedir_ruta_con_dialogo(
        titulo="Guardar plantilla de estados de carga",
        modo="guardar",
        tipos_archivo=[("Excel", f"*{EXTENSION_EXCEL}")],
        ruta_por_defecto=ruta_por_defecto,
    )
    if ruta is not None:
        return ruta

    entrada = pedir_input(
        f"Ruta de destino para la plantilla [Enter = {ruta_por_defecto}]:"
    ).strip()
    if not entrada:
        return ruta_por_defecto
    ruta = Path(entrada)
    if ruta.suffix.lower() != EXTENSION_EXCEL:
        ruta = ruta.with_suffix(EXTENSION_EXCEL)
    return ruta


# ── Paso 4-5 ──────────────────────────────────────────────────────────────────

def _paso_leer_excel_del_usuario(reglamento: dict) -> list[EstadoCrudo]:
    mostrar_separador("Datos de entrada")
    config_plantilla = _leer_config_plantilla()
    ruta_excel = _pedir_ruta_excel_completado()

    mostrar_procesando(f"Leyendo archivo: {ruta_excel} ...")
    try:
        estados = leer_excel(str(ruta_excel), config_plantilla)
    except ErrorArchivoExcel as error:
        _loguear_error_tecnico(
            f"apertura de la planilla Excel '{ruta_excel}'",
            error.__cause__ or error,
        )
        _terminar_con_error(str(error))
    except (ErrorFormatoPlantilla, ErrorDatoFila) as error:
        _terminar_con_error(str(error))

    mostrar_exito(f"Se leyeron {len(estados)} estado(s) de carga.")
    return estados


def _leer_config_plantilla() -> dict:
    return CONFIG_PLANTILLA


def _pedir_ruta_excel_completado() -> Path:
    pedir_enter(
        "Presione Enter para abrir el explorador de archivos y "
        "seleccionar la planilla completada:"
    )
    ruta_por_defecto = Path.home() / NOMBRE_CARPETA_ESCRITORIO

    nombre_archivo_ejemplo = f"estados_de_carga{EXTENSION_EXCEL}"
    ruta = _pedir_ruta_con_dialogo(
        titulo="Seleccionar archivo Excel completado",
        modo="abrir",
        tipos_archivo=[("Excel", f"*{EXTENSION_EXCEL}")],
        ruta_por_defecto=ruta_por_defecto / nombre_archivo_ejemplo,
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

def _paso_validar_plantilla(
    estados_crudos: list[EstadoCrudo], reglamento: dict
) -> list[Estado]:
    try:
        estados_enriquecidos = leer_plantilla(estados_crudos, reglamento)
    except ErrorValidacionPlantilla as error:
        mostrar_errores_validacion(error.errores)
        sys.exit(1)

    return estados_enriquecidos


# ── Paso 7 ────────────────────────────────────────────────────────────────────

def _paso_generar_combinaciones(
    estados: list[Estado], reglamento: dict
) -> list[Combinacion]:
    mostrar_separador("Procesamiento")
    combinaciones = generar_combinaciones(estados, reglamento)
    mostrar_info(f"Combinaciones generadas: [bold]{len(combinaciones)}[/bold]")
    return combinaciones


# ── Paso 8 ────────────────────────────────────────────────────────────────────

def _paso_marcar_duplicadas(
    combinaciones: list[Combinacion],
) -> list[Combinacion]:
    combinaciones = marcar_duplicadas(combinaciones)
    cantidad_duplicadas = sum(1 for c in combinaciones if c.es_duplicada)
    if cantidad_duplicadas == 0:
        mostrar_info("Duplicados encontrados: ninguno.")
    else:
        mostrar_advertencia(
            f"Duplicados encontrados: [bold]{cantidad_duplicadas}[/bold]  "
            "[dim](serán eliminadas del resultado)[/dim]"
        )
    return combinaciones


# ── Paso 9 ────────────────────────────────────────────────────────────────────

def _paso_marcar_superadas(
    combinaciones: list[Combinacion], reglamento: dict
) -> list[Combinacion]:
    combinaciones = marcar_superadas(
        combinaciones, reglamento["permanent_load_types"]
    )
    superadas = [c for c in combinaciones if c.esta_superada]

    if not superadas:
        mostrar_info("Combinaciones superadas por preponderancia: ninguna.")

    return combinaciones


# ── Paso 10 ───────────────────────────────────────────────────────────────────

def _paso_resolver_combinaciones_superadas(
    combinaciones: list[Combinacion],
) -> None:
    superadas = [c for c in combinaciones if c.esta_superada]
    if not superadas:
        return

    mostrar_separador("Combinaciones superadas")
    indice_por_generacion = {c.indice_generacion: c for c in combinaciones}
    mostrar_tabla_superadas(superadas, indice_por_generacion)

    while True:
        indices_a_descartar = _pedir_indices_a_descartar(superadas)
        if not indices_a_descartar or _confirmar_descarte(indices_a_descartar):
            break

    for combinacion in superadas:
        combinacion.descartada_por_usuario = (
            combinacion.indice_generacion in indices_a_descartar
        )


def _confirmar_descarte(indices_a_descartar: set[int]) -> bool:
    lista = ", ".join(f"#{i}" for i in sorted(indices_a_descartar))
    mostrar_info(f"Se van a descartar: {lista}")
    return pedir_confirmacion("¿Confirma este descarte?")


def _pedir_indices_a_descartar(superadas: list[Combinacion]) -> set[int]:
    indices_validos = {c.indice_generacion for c in superadas}
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


def _parsear_indices(
    entrada: str, indices_validos: set[int]
) -> tuple[set[int], str | None]:
    partes = entrada.split("-")
    indices = set()
    for parte in partes:
        parte = parte.strip()
        if not parte.isdigit():
            return set(), f"'{parte}' no es un número válido."
        numero = int(parte)
        if numero not in indices_validos:
            return set(), (
                f"#{numero} no está en la lista de combinaciones superadas."
            )
        indices.add(numero)
    return indices, None


def _paso_mostrar_resumen(combinaciones: list[Combinacion]) -> None:
    mostrar_separador("Resumen")
    mostrar_tabla_resumen(combinaciones)


def _hay_combinaciones_validas(combinaciones: list[Combinacion]) -> bool:
    return any(
        not c.es_duplicada and not c.descartada_por_usuario
        for c in combinaciones
    )


def _confirmar_continuar_sin_combinaciones() -> bool:
    mostrar_advertencia(
        "No quedó ninguna combinación resultante para exportar."
    )
    return pedir_confirmacion("¿Desea elegir un exportador igualmente?")


# ── Paso 11 ───────────────────────────────────────────────────────────────────

def _paso_exportar(
    combinaciones: list[Combinacion],
    estados_crudos: list[EstadoCrudo],
    estados: list[Estado],
    reglamento: dict,
    nombre_perfil: str,
) -> None:
    mostrar_separador("Exportación")
    config_resumen = _leer_config_resumen()

    ruta_exportador = _pedir_archivo_de_directorio(
        directorio=RUTA_EXPORTADORES,
        extension=EXTENSION_YAML,
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
        if not c.es_duplicada and not c.descartada_por_usuario
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
        _loguear_error_tecnico(
            f"lectura del perfil de exportación '{ruta_yaml.name}'",
            error,
        )
        _terminar_con_error(
            f"El perfil de exportación '{ruta_yaml.name}' tiene un "
            f"formato inválido. Revisá el YAML o pedí una versión "
            f"corregida a quien te lo compartió."
        )


def _pedir_ruta_destino_exportacion(ruta_exportador: Path) -> Path:
    nombre_software = ruta_exportador.stem
    fecha = datetime.now().strftime(FORMATO_FECHA_ARCHIVO)
    nombre_archivo_por_defecto = (
        f"{PREFIJO_EXPORTACION}{nombre_software}_{fecha}{EXTENSION_EXCEL}"
    )
    ruta_por_defecto = (
        Path.home() / NOMBRE_CARPETA_ESCRITORIO / nombre_archivo_por_defecto
    )

    ruta_dialogo = _pedir_ruta_con_dialogo(
        titulo="Guardar archivo de exportación",
        modo="guardar",
        tipos_archivo=[("Excel", f"*{EXTENSION_EXCEL}")],
        ruta_por_defecto=ruta_por_defecto,
    )

    viene_del_dialogo = ruta_dialogo is not None

    while True:
        if ruta_dialogo is not None:
            ruta = ruta_dialogo
            ruta_dialogo = None
        else:
            entrada = pedir_input(
                "Ruta de destino para el archivo de exportación "
                f"[Enter = {ruta_por_defecto}]:"
            ).strip()
            viene_del_dialogo = False
            if not entrada:
                ruta = ruta_por_defecto
            else:
                ruta = Path(entrada)
                if ruta.suffix.lower() != EXTENSION_EXCEL:
                    ruta = ruta.with_suffix(EXTENSION_EXCEL)

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
        entrada = pedir_seleccion_de_archivo(
            f"Elija un {descripcion_tipo} (1-{len(archivos)}):",
            al_reimprimir=reimprimir if seccion else None,
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
        _loguear_fallo_dialogo()
        return None


def _loguear_fallo_dialogo() -> None:
    """
    Registra en el log de errores que el diálogo gráfico de selección de
    archivo falló. El flujo continúa pidiendo la ruta por teclado; este
    registro solo evita que el fallo quede oculto sin rastro.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(RUTA_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 60}\n")
        f.write(
            f"  COMBOS v{VERSION}  —  {timestamp}  —  falló el diálogo de "
            "selección de archivo, se pidió la ruta por teclado\n"
        )
        f.write(f"{'=' * 60}\n")
        f.write(traceback.format_exc())


def _loguear_error_tecnico(contexto: str, error: BaseException) -> None:
    """
    Registra en el log de errores el detalle técnico de una excepción que
    se le presentó al usuario con un mensaje amable. Permite que el
    reporte de soporte tenga la información técnica sin ensuciar la
    pantalla del usuario final.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(RUTA_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 60}\n")
        f.write(
            f"  COMBOS v{VERSION}  —  {timestamp}  —  error técnico "
            f"durante {contexto}\n"
        )
        f.write(f"{'=' * 60}\n")
        f.write(f"  {type(error).__name__}: {error}\n")
