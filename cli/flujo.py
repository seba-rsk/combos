from __future__ import annotations

import sys
import tkinter as tk
import traceback
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

import yaml

from cli.consola import (
    mostrar_advertencia,
    mostrar_ayuda_descartar,
    mostrar_bienvenida,
    mostrar_cantidad_parametros,
    mostrar_eleccion_confirmada,
    mostrar_error,
    mostrar_error_indices,
    mostrar_errores_validacion,
    mostrar_exito,
    mostrar_info,
    mostrar_lista_archivos,
    mostrar_menu_parametro,
    mostrar_procesando,
    mostrar_separador,
    mostrar_tabla_resumen,
    mostrar_tabla_superadas,
    pedir_confirmacion,
    pedir_enter,
    pedir_input,
    pedir_seleccion_de_archivo,
)
from cli.constantes import (
    EXTENSION_EXCEL,
    EXTENSION_YAML,
    FORMATO_FECHA_ARCHIVO,
    FORMATO_TIMESTAMP_LOG,
    NOMBRE_CARPETA_ESCRITORIO,
    PREFIJO_EXPORTACION,
    PREFIJO_PLANTILLA,
)
from dominio.lector_plantilla import ErrorValidacionPlantilla, leer_plantilla
from dominio.lector_yaml import leer_reglamento
from dominio.modelos import (
    Combinacion,
    EleccionParametro,
    ParametroReglamento,
)
from dominio.parametros import (
    combinaciones_que_referencian,
    crear_eleccion,
    numero_opcion_default,
    parametros_que_aplican,
    resolver_parametros,
    tipos_de_carga_que_referencian,
)
from dominio.sesion import (
    Sesion,
    aplicar_descartes,
    combinaciones_resultantes,
    combinaciones_superadas,
    procesar,
)
from infraestructura.config_interna import CONFIG_PLANTILLA, CONFIG_RESUMEN
from infraestructura.exportador import exportar
from infraestructura.generador_plantilla import generar_plantilla
from infraestructura.lector_excel import (
    ErrorArchivoExcel,
    ErrorDatoFila,
    ErrorFormatoPlantilla,
    leer_excel,
)
from infraestructura.rutas import (
    RUTA_EXPORTADORES,
    RUTA_LOG,
    RUTA_PROFILES,
)
from version import VERSION

# ── Punto de entrada ──────────────────────────────────────────────────────────

def ejecutar_flujo() -> None:
    """
    Orquesta el flujo completo de COMBOS sobre una única Sesion:
    reglamento → plantilla → lectura y validación de estados →
    parámetros → procesamiento → superadas → resumen → exportación.
    Cada paso completa la sesión; la lógica vive en dominio.sesion.
    """
    mostrar_bienvenida(VERSION)

    sesion = Sesion()

    _paso_cargar_reglamento(sesion)

    _paso_generar_plantilla_si_el_usuario_lo_desea(sesion)

    _paso_leer_excel_del_usuario(sesion)

    _paso_validar_plantilla(sesion)

    _paso_resolver_parametros(sesion)

    _paso_procesar(sesion)

    _paso_resolver_combinaciones_superadas(sesion)

    _paso_mostrar_resumen(sesion)

    if not combinaciones_resultantes(sesion):
        if not _confirmar_continuar_sin_combinaciones():
            mostrar_info("Operación finalizada sin exportar.")
            pedir_enter("Presioná Enter para cerrar COMBOS...")
            return

    _paso_exportar(sesion)


# ── Paso 2 ────────────────────────────────────────────────────────────────────

def _paso_cargar_reglamento(sesion: Sesion) -> None:
    mostrar_separador("Reglamento")
    ruta_yaml = _pedir_archivo_de_directorio(
        directorio=RUTA_PROFILES,
        extension=EXTENSION_YAML,
        descripcion_tipo="reglamento",
        seccion="Reglamento",
    )
    mostrar_procesando(f"Cargando reglamento: {ruta_yaml.name} ...")
    try:
        sesion.reglamento_crudo = leer_reglamento(str(ruta_yaml))
    except (FileNotFoundError, ValueError) as error:
        _terminar_con_error(str(error))

    sesion.reglamento = sesion.reglamento_crudo
    sesion.nombre_perfil = ruta_yaml.name
    nombre_reglamento = sesion.reglamento["metadata"]["code_name"]
    mostrar_exito(f"Reglamento cargado: {nombre_reglamento}")


# ── Paso 3 ────────────────────────────────────────────────────────────────────

def _paso_generar_plantilla_si_el_usuario_lo_desea(sesion: Sesion) -> None:
    mostrar_separador("Plantilla")
    respuesta = pedir_confirmacion("¿Desea generar la plantilla Excel ahora?")
    if not respuesta:
        return

    ruta_destino = _pedir_ruta_destino_plantilla(sesion.nombre_perfil)
    mostrar_procesando(f"Generando plantilla en: {ruta_destino} ...")
    try:
        generar_plantilla(
            sesion.reglamento, str(ruta_destino),
            sesion.nombre_perfil, VERSION,
        )
    except (FileNotFoundError, PermissionError, OSError) as error:
        _terminar_con_error(str(error))

    mostrar_exito(f"Plantilla generada: {ruta_destino}")


def _pedir_ruta_destino_plantilla(nombre_yaml: str) -> Path:
    ruta_por_defecto = _ruta_por_defecto_plantilla(nombre_yaml)
    return _pedir_ruta_destino_excel(
        titulo_dialogo="Guardar plantilla de estados de carga",
        prompt_consola="Ruta de destino para la plantilla",
        ruta_por_defecto=ruta_por_defecto,
    )


def _ruta_por_defecto_plantilla(nombre_yaml: str) -> Path:
    ruta_escritorio = Path.home() / NOMBRE_CARPETA_ESCRITORIO
    fecha = datetime.now().strftime(FORMATO_FECHA_ARCHIVO)
    nombre_archivo = (
        f"{PREFIJO_PLANTILLA}{Path(nombre_yaml).stem}_{fecha}"
        f"{EXTENSION_EXCEL}"
    )
    return ruta_escritorio / nombre_archivo


def _pedir_ruta_destino_excel(
    titulo_dialogo: str, prompt_consola: str, ruta_por_defecto: Path
) -> Path:
    """
    Pide al usuario una ruta de destino .xlsx: primero abre el diálogo
    del sistema; si el usuario lo cancela o no está disponible, cae al
    prompt de consola. Repite si el archivo elegido está abierto o si el
    usuario cancela el sobrescribir de un archivo existente.
    """
    ruta_dialogo = _pedir_ruta_con_dialogo(
        titulo=titulo_dialogo,
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
            ruta = _leer_ruta_excel_por_consola(
                prompt_consola, ruta_por_defecto
            )
            viene_del_dialogo = False
        if not _confirmar_destino_excel(ruta, viene_del_dialogo):
            viene_del_dialogo = False
            continue
        return ruta


def _leer_ruta_excel_por_consola(prompt: str, ruta_por_defecto: Path) -> Path:
    entrada = pedir_input(
        f"{prompt} [Enter = {ruta_por_defecto}]:"
    ).strip()
    if not entrada:
        return ruta_por_defecto
    ruta = Path(entrada)
    if ruta.suffix.lower() != EXTENSION_EXCEL:
        ruta = ruta.with_suffix(EXTENSION_EXCEL)
    return ruta


def _confirmar_destino_excel(ruta: Path, viene_del_dialogo: bool) -> bool:
    """
    Devuelve True si `ruta` es un destino aceptable; False si hay que
    pedirla de nuevo (archivo abierto o el usuario canceló el sobrescribir).
    """
    if not ruta.exists():
        return True
    if _archivo_esta_abierto(ruta):
        mostrar_advertencia(
            f"El archivo '{ruta.name}' está abierto. "
            "Cerralo e intentá de nuevo, o ingresá otra ruta."
        )
        return False
    if viene_del_dialogo:
        return True
    return pedir_confirmacion(
        f"El archivo '{ruta.name}' ya existe. ¿Sobreescribir?"
    )


# ── Paso 4-5 ──────────────────────────────────────────────────────────────────

def _paso_leer_excel_del_usuario(sesion: Sesion) -> None:
    mostrar_separador("Datos de entrada")
    config_plantilla = _leer_config_plantilla()
    ruta_excel = _pedir_ruta_excel_completado()

    mostrar_procesando(f"Leyendo archivo: {ruta_excel} ...")
    try:
        sesion.estados_crudos = leer_excel(str(ruta_excel), config_plantilla)
    except ErrorArchivoExcel as error:
        _loguear_error_tecnico(
            f"apertura de la planilla Excel '{ruta_excel}'",
            error.__cause__ or error,
        )
        _terminar_con_error(str(error))
    except (ErrorFormatoPlantilla, ErrorDatoFila) as error:
        _terminar_con_error(str(error))

    mostrar_exito(
        f"Se leyeron {len(sesion.estados_crudos)} estado(s) de carga."
    )


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

def _paso_validar_plantilla(sesion: Sesion) -> None:
    try:
        sesion.estados = leer_plantilla(
            sesion.estados_crudos, sesion.reglamento
        )
    except ErrorValidacionPlantilla as error:
        mostrar_errores_validacion(error.errores)
        sys.exit(1)


# ── Paso 6b: parámetros del reglamento ────────────────────────────────────────

def _paso_resolver_parametros(sesion: Sesion) -> None:
    """
    Pregunta al usuario los parámetros del reglamento que aplican a sus
    estados de carga y deja en la sesión el reglamento con los factores
    ya resueltos a números, junto con las elecciones para registrarlas
    en la exportación. Los parámetros que no aplican (ningún estado
    ingresado usa los tipos de carga que los referencian) se resuelven
    con su valor por defecto sin preguntar ni registrar, porque su
    valor no participa de ninguna combinación generada.
    """
    if not sesion.reglamento["parameters"]:
        return

    tipos_presentes = {estado.tipo_carga for estado in sesion.estados}
    aplicables, no_aplicables = parametros_que_aplican(
        sesion.reglamento, tipos_presentes
    )

    if aplicables:
        sesion.elecciones = _preguntar_parametros(
            sesion.reglamento, aplicables
        )

    elecciones_internas = [
        crear_eleccion(parametro, numero_opcion_default(parametro))
        for parametro in no_aplicables
    ]
    sesion.reglamento = resolver_parametros(
        sesion.reglamento_crudo, sesion.elecciones + elecciones_internas
    )


def _preguntar_parametros(
    reglamento: dict, parametros: list[ParametroReglamento]
) -> list[EleccionParametro]:
    mostrar_separador("Parámetros del reglamento")
    mostrar_cantidad_parametros(len(parametros))

    elecciones: list[EleccionParametro] = []
    for parametro in parametros:
        tipos_afectados = tipos_de_carga_que_referencian(
            reglamento, parametro.id_parametro
        )
        combinaciones_afectadas = combinaciones_que_referencian(
            reglamento, parametro.id_parametro
        )
        mostrar_menu_parametro(
            parametro, tipos_afectados, combinaciones_afectadas
        )
        numero_elegido = _pedir_numero_de_opcion(parametro)
        eleccion = crear_eleccion(parametro, numero_elegido)
        elecciones.append(eleccion)
        mostrar_eleccion_confirmada(eleccion)
    return elecciones


def _pedir_numero_de_opcion(parametro: ParametroReglamento) -> int:
    cantidad = len(parametro.opciones)
    numero_default = numero_opcion_default(parametro)
    while True:
        entrada = pedir_input(
            f"Elija una opción (1-{cantidad}) [Enter = {numero_default}]:"
        ).strip()
        if entrada == "":
            return numero_default
        if entrada.isdigit() and 1 <= int(entrada) <= cantidad:
            return int(entrada)
        mostrar_advertencia(
            f"Ingrese un número entre 1 y {cantidad}, o Enter para la "
            "opción por defecto."
        )


# ── Paso 7: procesamiento ─────────────────────────────────────────────────────

def _paso_procesar(sesion: Sesion) -> None:
    """
    Corre el pipeline de dominio (generar, marcar duplicadas, marcar
    superadas) e informa los resultados de cada etapa en pantalla.
    """
    mostrar_separador("Procesamiento")
    procesar(sesion)
    mostrar_info(
        f"Combinaciones generadas: "
        f"[bold]{len(sesion.combinaciones)}[/bold]"
    )
    _informar_duplicadas(sesion)
    if not combinaciones_superadas(sesion):
        mostrar_info("Combinaciones superadas por preponderancia: ninguna.")


def _informar_duplicadas(sesion: Sesion) -> None:
    cantidad_duplicadas = sum(
        1 for c in sesion.combinaciones if c.es_duplicada
    )
    if cantidad_duplicadas == 0:
        mostrar_info("Duplicados encontrados: ninguno.")
    else:
        mostrar_advertencia(
            f"Duplicados encontrados: [bold]{cantidad_duplicadas}[/bold]  "
            "[dim](serán eliminadas del resultado)[/dim]"
        )


# ── Paso 8: combinaciones superadas ───────────────────────────────────────────

def _paso_resolver_combinaciones_superadas(sesion: Sesion) -> None:
    superadas = combinaciones_superadas(sesion)
    if not superadas:
        return

    mostrar_separador("Combinaciones superadas")
    indice_por_generacion = {
        c.indice_generacion: c for c in sesion.combinaciones
    }
    mostrar_tabla_superadas(superadas, indice_por_generacion)

    while True:
        indices_a_descartar = _pedir_indices_a_descartar(superadas)
        if not indices_a_descartar or _confirmar_descarte(indices_a_descartar):
            break

    aplicar_descartes(sesion, indices_a_descartar)


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


def _paso_mostrar_resumen(sesion: Sesion) -> None:
    mostrar_separador("Resumen")
    mostrar_tabla_resumen(combinaciones_resultantes(sesion))


def _confirmar_continuar_sin_combinaciones() -> bool:
    mostrar_advertencia(
        "No quedó ninguna combinación resultante para exportar."
    )
    return pedir_confirmacion("¿Desea elegir un exportador igualmente?")


# ── Paso 11 ───────────────────────────────────────────────────────────────────

def _paso_exportar(sesion: Sesion) -> None:
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
            sesion, config_resumen, config_exportador,
            str(ruta_destino), VERSION,
        )
    except (ValueError, RuntimeError) as error:
        _terminar_con_error(str(error))

    cantidad_validas = len(combinaciones_resultantes(sesion))
    mostrar_exito(f"{cantidad_validas} combinación(es) exportada(s).")
    mostrar_exito(f"Archivo generado: {ruta_destino}")
    pedir_enter("Presioná Enter para cerrar COMBOS...")


def _leer_config_resumen() -> dict:
    return CONFIG_RESUMEN


def _leer_config_exportador(ruta_yaml: Path) -> dict:
    try:
        config = yaml.safe_load(ruta_yaml.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        _loguear_error_tecnico(
            f"lectura del perfil de exportación '{ruta_yaml.name}'",
            error,
        )
        config = None
    if not isinstance(config, dict):
        _terminar_con_error(
            f"El perfil de exportación '{ruta_yaml.name}' tiene un "
            f"formato inválido. Revisá el YAML o pedí una versión "
            f"corregida a quien te lo compartió."
        )
    return config


def _pedir_ruta_destino_exportacion(ruta_exportador: Path) -> Path:
    fecha = datetime.now().strftime(FORMATO_FECHA_ARCHIVO)
    nombre_archivo = (
        f"{PREFIJO_EXPORTACION}{ruta_exportador.stem}_{fecha}"
        f"{EXTENSION_EXCEL}"
    )
    ruta_por_defecto = (
        Path.home() / NOMBRE_CARPETA_ESCRITORIO / nombre_archivo
    )
    return _pedir_ruta_destino_excel(
        titulo_dialogo="Guardar archivo de exportación",
        prompt_consola="Ruta de destino para el archivo de exportación",
        ruta_por_defecto=ruta_por_defecto,
    )


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
    timestamp = datetime.now().strftime(FORMATO_TIMESTAMP_LOG)
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
    timestamp = datetime.now().strftime(FORMATO_TIMESTAMP_LOG)
    with open(RUTA_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 60}\n")
        f.write(
            f"  COMBOS v{VERSION}  —  {timestamp}  —  error técnico "
            f"durante {contexto}\n"
        )
        f.write(f"{'=' * 60}\n")
        f.write(f"  {type(error).__name__}: {error}\n")
