from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter

from dominio.envolventes import construir_envolventes
from dominio.formateador import formatear_componentes
from infraestructura.estilos_excel import (
    aplicar_estilo_titulo_programa,
    aplicar_estilo_label_metadata,
    aplicar_estilo_valor_metadata,
    aplicar_estilo_titulo_seccion,
    aplicar_estilo_encabezado_tabla,
    aplicar_estilo_fila_dato,
    aplicar_estilo_fila_dato_acento,
    aplicar_estilo_mensaje_vacio,
    ajustar_anchos_columnas,
    aplicar_estilo_etiqueta_hoja,
    aplicar_borde_perimetral_tabla,
)


# ── Punto de entrada ──────────────────────────────────────────────────────────

def exportar(
    combinaciones: list[dict],
    estados_crudos: list[dict],
    estados: list[dict],
    reglamento: dict,
    config_resumen: dict,
    config_exportador: dict,
    ruta_destino: str,
    nombre_perfil: str,
    version: str,
) -> None:
    _validar_config_resumen(config_resumen)
    _validar_config_exportador(config_exportador)
    _validar_ruta_destino(ruta_destino)

    _asignar_nombres(combinaciones, reglamento)

    libro = openpyxl.Workbook()
    libro.remove(libro.worksheets[0])

    _escribir_hoja_resumen(
        libro, combinaciones, estados_crudos, reglamento,
        config_resumen, nombre_perfil, version,
    )
    _escribir_hoja_exportacion(libro, combinaciones, config_exportador, reglamento)

    if libro.worksheets:
        libro.active = 0
    try:
        libro.save(ruta_destino)
    except (OSError, PermissionError) as error:
        raise RuntimeError(
            f"No se pudo guardar el archivo en '{ruta_destino}': {error}"
        ) from error


# ── Paso 1: asignación de nombres ─────────────────────────────────────────────

def _asignar_nombres(combinaciones: list[dict], reglamento: dict) -> None:
    combinaciones_validas = [
        c for c in combinaciones
        if not c["es_duplicada"] and not c["descartada_por_usuario"]
    ]

    por_estado_limite: dict[str, list[dict]] = defaultdict(list)
    for combinacion in combinaciones_validas:
        por_estado_limite[combinacion["estado_limite"]].append(combinacion)

    for estado_limite, grupo in por_estado_limite.items():
        prefijo = _obtener_prefijo(reglamento, estado_limite)
        _asignar_nombres_en_grupo(grupo, prefijo)


def _asignar_nombres_en_grupo(grupo: list[dict], prefijo: str) -> None:
    por_base: dict[int, list[dict]] = defaultdict(list)
    for combinacion in grupo:
        por_base[combinacion["combinacion_base_id"]].append(combinacion)

    numero_secuencial = 1
    for variantes in por_base.values():
        if len(variantes) == 1:
            variantes[0]["nombre"] = f"{prefijo}{numero_secuencial}"
        else:
            for indice_variante, variante in enumerate(variantes, start=1):
                variante["nombre"] = f"{prefijo}{numero_secuencial}-{indice_variante}"
        numero_secuencial += 1


def _obtener_prefijo(reglamento: dict, estado_limite: str) -> str:
    config_estado = reglamento.get("limit_states", {}).get(estado_limite, {})
    if isinstance(config_estado, dict):
        return config_estado.get("prefix", estado_limite)
    return estado_limite


# ── Hoja 1: Resumen ───────────────────────────────────────────────────────────

def _escribir_hoja_resumen(
    libro: openpyxl.Workbook,
    combinaciones: list[dict],
    estados_crudos: list[dict],
    reglamento: dict,
    config_resumen: dict,
    nombre_perfil: str,
    version: str,
) -> None:
    hoja = libro.create_sheet(config_resumen["nombre_hoja"])
    fila = config_resumen["fila_inicio"]
    columna = config_resumen["columna_inicio"]

    fila = _escribir_encabezado_programa(
        hoja, fila, columna, config_resumen, reglamento, nombre_perfil, version,
    )

    escritores_por_id = {
        "datos_ingresados": _escribir_seccion_datos_ingresados,
        "combinaciones_generadas": _escribir_seccion_combinaciones_generadas,
        "combinaciones_resultantes": _escribir_seccion_combinaciones_resultantes,
        "duplicados_eliminados": _escribir_seccion_duplicados_eliminados,
        "superadas": _escribir_seccion_superadas,
    }

    for config_seccion in config_resumen["secciones"]:
        if not config_seccion.get("visible", True):
            continue
        escritor = escritores_por_id.get(config_seccion["id"])
        if escritor is None:
            continue
        fila = escritor(hoja, fila, columna, combinaciones, estados_crudos, config_seccion)
        fila += 1

    ajustar_anchos_columnas(hoja, columna)


def _escribir_encabezado_programa(
    hoja,
    fila: int,
    columna: int,
    config_resumen: dict,
    reglamento: dict,
    nombre_perfil: str,
    version: str,
) -> int:
    encabezado = config_resumen.get("encabezado_programa", {})
    metadata = reglamento.get("metadata", {})

    nombre = encabezado.get("nombre", "COMBOS")
    # La version se escribe desde el parametro explícito, no desde el config JSON.
    celda = hoja.cell(row=fila, column=columna, value=f"{nombre} v{version}")
    aplicar_estilo_titulo_programa(celda)
    ancho_requerido = round(len(celda.value) * 1.4) + 2
    hoja.column_dimensions[get_column_letter(columna)].width = ancho_requerido

    columna_etiqueta = columna + 1
    celda_etiqueta = hoja.cell(row=fila, column=columna_etiqueta, value="SALIDA DE DATOS")
    aplicar_estilo_etiqueta_hoja(celda_etiqueta)
    fila += 1

    celda_label = hoja.cell(row=fila, column=columna, value="Perfil usado:")
    aplicar_estilo_label_metadata(celda_label)
    celda_valor = hoja.cell(row=fila, column=columna + 1, value=nombre_perfil)
    aplicar_estilo_valor_metadata(celda_valor)
    fila += 1

    if encabezado.get("mostrar_reglamento"):
        code_name = metadata.get("code_name", "")
        code_version = metadata.get("code_version", "")
        valor = f"{code_name} - {code_version}" if code_name or code_version else ""
        aplicar_estilo_label_metadata(hoja.cell(row=fila, column=columna, value="Reglamento:"))
        aplicar_estilo_valor_metadata(hoja.cell(row=fila, column=columna + 1, value=valor))
        fila += 1

        aplicar_estilo_label_metadata(hoja.cell(row=fila, column=columna, value="País:"))
        aplicar_estilo_valor_metadata(hoja.cell(row=fila, column=columna + 1, value=metadata.get("country", "")))
        fila += 1

        aplicar_estilo_label_metadata(hoja.cell(row=fila, column=columna, value="Descripción:"))
        aplicar_estilo_valor_metadata(hoja.cell(row=fila, column=columna + 1, value=metadata.get("description", "")))
        fila += 1

    if encabezado.get("mostrar_fecha"):
        aplicar_estilo_label_metadata(hoja.cell(row=fila, column=columna, value="Fecha:"))
        aplicar_estilo_valor_metadata(hoja.cell(row=fila, column=columna + 1, value=datetime.now().strftime("%d/%m/%Y %H:%M")))
        fila += 1

    return fila + 1


# ── Secciones del resumen ─────────────────────────────────────────────────────

def _escribir_seccion_datos_ingresados(hoja, fila, columna, combinaciones, estados, config_seccion):
    aplicar_estilo_titulo_seccion(hoja, fila, columna, len(config_seccion.get("columnas", [])))
    hoja.cell(row=fila, column=columna, value=config_seccion["titulo"])
    fila += 1
    encabezados = config_seccion.get("columnas", [])
    for d, t in enumerate(encabezados):
        celda = hoja.cell(row=fila, column=columna + d, value=t)
        aplicar_estilo_encabezado_tabla(celda)
    fila_encabezado = fila
    fila += 1
    for indice, estado in enumerate(estados, start=1):
        es_direccional = estado["tipo_estado"] == "direccional"
        nombre_grupo = f"{estado['tipo_carga']}-{estado['grupo']}" if es_direccional else ""
        opuesto = "" if not es_direccional else ("Sí" if estado.get("incluir_opuesto") else "No")
        valores = {
            "Id": indice,
            "Nombre del estado": estado["nombre_estado"],
            "Tipo de carga": estado["tipo_carga"],
            "Tipo de estado": estado["tipo_estado"].capitalize(),
            "Nombre de grupo": nombre_grupo,
            "Opuesto": opuesto,
        }
        for d, t in enumerate(encabezados):
            celda = hoja.cell(row=fila, column=columna + d, value=valores.get(t, ""))
            aplicar_estilo_fila_dato(celda)
        fila += 1
    aplicar_borde_perimetral_tabla(hoja, fila_encabezado, fila - 1, columna, columna + len(encabezados) - 1)
    return fila


def _escribir_seccion_combinaciones_generadas(hoja, fila, columna, combinaciones, estados, config_seccion):
    aplicar_estilo_titulo_seccion(hoja, fila, columna, len(config_seccion.get("columnas", [])))
    hoja.cell(row=fila, column=columna, value=config_seccion["titulo"])
    fila += 1
    encabezados = config_seccion.get("columnas", [])
    for d, t in enumerate(encabezados):
        celda = hoja.cell(row=fila, column=columna + d, value=t)
        aplicar_estilo_encabezado_tabla(celda)
    fila_encabezado = fila
    fila += 1
    for combinacion in combinaciones:
        valores = {
            "Id": combinacion["indice_generacion"],
            "Componentes": formatear_componentes(combinacion["componentes"]),
            "Estado límite": combinacion["estado_limite"],
            "Combinación base": combinacion["combinacion_base_id"],
            "Duplicada por": combinacion["duplicada_por"] if combinacion["es_duplicada"] else "",
            "Superada por": combinacion["superada_por"] if combinacion["esta_superada"] else "",
            "Decisión": (
                "Descartada" if combinacion["esta_superada"] and combinacion["descartada_por_usuario"]
                else "No descartada" if combinacion["esta_superada"] else ""
            ),
        }
        for d, t in enumerate(encabezados):
            celda = hoja.cell(row=fila, column=columna + d, value=valores.get(t, ""))
            aplicar_estilo_fila_dato(celda)
        fila += 1
    aplicar_borde_perimetral_tabla(hoja, fila_encabezado, fila - 1, columna, columna + len(encabezados) - 1)
    return fila


def _escribir_seccion_combinaciones_resultantes(hoja, fila, columna, combinaciones, estados, config_seccion):
    aplicar_estilo_titulo_seccion(hoja, fila, columna, len(config_seccion.get("columnas", [])))
    hoja.cell(row=fila, column=columna, value=config_seccion["titulo"])
    fila += 1
    resultantes = [c for c in combinaciones if not c["es_duplicada"] and not c["descartada_por_usuario"]]
    if not resultantes:
        celda = hoja.cell(row=fila, column=columna, value="(Sin combinaciones resultantes)")
        aplicar_estilo_mensaje_vacio(celda)
        return fila + 1
    encabezados = config_seccion.get("columnas", [])
    for d, t in enumerate(encabezados):
        celda = hoja.cell(row=fila, column=columna + d, value=t)
        aplicar_estilo_encabezado_tabla(celda)
    fila_encabezado = fila
    fila += 1
    for combinacion in resultantes:
        valores = {
            "Id": combinacion["indice_generacion"],
            "Componentes": formatear_componentes(combinacion["componentes"]),
            "Estado límite": combinacion["estado_limite"],
            "Combinación base": combinacion["combinacion_base_id"],
            "Nombre asignado": combinacion.get("nombre") or "",
        }
        for d, t in enumerate(encabezados):
            celda = hoja.cell(row=fila, column=columna + d, value=valores.get(t, ""))
            if t == "Nombre asignado":
                aplicar_estilo_fila_dato_acento(celda)
            else:
                aplicar_estilo_fila_dato(celda)
        fila += 1
    aplicar_borde_perimetral_tabla(hoja, fila_encabezado, fila - 1, columna, columna + len(encabezados) - 1)
    return fila


def _escribir_seccion_duplicados_eliminados(hoja, fila, columna, combinaciones, estados, config_seccion):
    aplicar_estilo_titulo_seccion(hoja, fila, columna, len(config_seccion.get("columnas", [])))
    hoja.cell(row=fila, column=columna, value=config_seccion["titulo"])
    fila += 1
    duplicadas = [c for c in combinaciones if c["es_duplicada"]]
    if not duplicadas:
        celda = hoja.cell(row=fila, column=columna, value="(Sin combinaciones duplicadas)")
        aplicar_estilo_mensaje_vacio(celda)
        return fila + 1
    encabezados = config_seccion.get("columnas", [])
    for d, t in enumerate(encabezados):
        celda = hoja.cell(row=fila, column=columna + d, value=t)
        aplicar_estilo_encabezado_tabla(celda)
    fila_encabezado = fila
    fila += 1
    for combinacion in duplicadas:
        valores = {
            "Id": combinacion["indice_generacion"],
            "Componentes": formatear_componentes(combinacion["componentes"]),
            "Estado límite": combinacion["estado_limite"],
            "Combinación base": combinacion["combinacion_base_id"],
            "Duplicada por": combinacion["duplicada_por"],
        }
        for d, t in enumerate(encabezados):
            celda = hoja.cell(row=fila, column=columna + d, value=valores.get(t, ""))
            aplicar_estilo_fila_dato(celda)
        fila += 1
    aplicar_borde_perimetral_tabla(hoja, fila_encabezado, fila - 1, columna, columna + len(encabezados) - 1)
    return fila


def _escribir_seccion_superadas(hoja, fila, columna, combinaciones, estados, config_seccion):
    aplicar_estilo_titulo_seccion(hoja, fila, columna, len(config_seccion.get("columnas", [])))
    hoja.cell(row=fila, column=columna, value=config_seccion["titulo"])
    fila += 1
    superadas = [c for c in combinaciones if c["esta_superada"]]
    filtro = config_seccion.get("filtro")
    if filtro == "solo_descartadas":
        superadas = [c for c in superadas if c["descartada_por_usuario"]]
    if not superadas:
        celda = hoja.cell(row=fila, column=columna, value="(Sin combinaciones superadas)")
        aplicar_estilo_mensaje_vacio(celda)
        return fila + 1
    encabezados = config_seccion.get("columnas", [])
    for d, t in enumerate(encabezados):
        celda = hoja.cell(row=fila, column=columna + d, value=t)
        aplicar_estilo_encabezado_tabla(celda)
    fila_encabezado = fila
    fila += 1
    for combinacion in superadas:
        valores = {
            "Id": combinacion["indice_generacion"],
            "Componentes": formatear_componentes(combinacion["componentes"]),
            "Estado límite": combinacion["estado_limite"],
            "Combinación base": combinacion["combinacion_base_id"],
            "Superada por": combinacion["superada_por"],
        }
        for d, t in enumerate(encabezados):
            celda = hoja.cell(row=fila, column=columna + d, value=valores.get(t, ""))
            aplicar_estilo_fila_dato(celda)
        fila += 1
    aplicar_borde_perimetral_tabla(hoja, fila_encabezado, fila - 1, columna, columna + len(encabezados) - 1)
    return fila


# ── Hoja 2: Exportación ───────────────────────────────────────────────────────

def _escribir_hoja_exportacion(
    libro: openpyxl.Workbook,
    combinaciones: list[dict],
    config_exportador: dict,
    reglamento: dict,
) -> None:
    nombre_software = config_exportador["metadata"]["software_name"]
    nombre_hoja_raw = f"Output {nombre_software}".replace("'", "").replace('"', "")
    nombre_hoja = nombre_hoja_raw[:31]
    hoja = libro.create_sheet(nombre_hoja)

    config_hoja = config_exportador["hoja"]
    config_tabla_combinaciones = config_hoja["tabla_combinaciones"]
    layout = config_tabla_combinaciones["layout"]
    fila_inicio = config_tabla_combinaciones.get("fila_inicio", 1)
    columna_inicio = config_tabla_combinaciones.get("columna_inicio", 1)

    combinaciones_validas = [
        c for c in combinaciones
        if not c["es_duplicada"] and not c["descartada_por_usuario"]
    ]

    if layout == "por_componente":
        ancho_tabla_1 = _escribir_layout_por_componente(
            hoja, combinaciones_validas, config_tabla_combinaciones, fila_inicio, columna_inicio
        )
    elif layout == "por_combinacion":
        ancho_tabla_1 = _escribir_layout_por_combinacion(
            hoja, combinaciones_validas, config_tabla_combinaciones, fila_inicio, columna_inicio
        )
    else:
        ancho_tabla_1 = 0

    columna_siguiente = columna_inicio + ancho_tabla_1

    config_tabla_nombres = config_hoja.get("tabla_nombres")
    if config_tabla_nombres:
        separacion = config_tabla_nombres.get("separacion_columnas", 1)
        columna_tabla_nombres = columna_siguiente + separacion
        _escribir_tabla_nombres(
            hoja, combinaciones_validas, config_tabla_nombres, fila_inicio, columna_tabla_nombres
        )
        columna_siguiente = columna_tabla_nombres + 1

    config_tabla_envolventes = config_hoja.get("tabla_envolventes")
    if config_tabla_envolventes:
        separacion = config_tabla_envolventes.get("separacion_columnas", 1)
        columna_tabla_envolventes = columna_siguiente + separacion
        filas_envolventes = construir_envolventes(
            combinaciones_validas,
            reglamento,
            config_tabla_envolventes.get("prefijo_nombre", "ENV"),
        )
        _escribir_tabla_envolventes(
            hoja, filas_envolventes, config_tabla_envolventes, fila_inicio, columna_tabla_envolventes
        )

    ajustar_anchos_columnas(hoja, columna_inicio)


# ── Layout por_componente ─────────────────────────────────────────────────────

def _escribir_layout_por_componente(
    hoja, combinaciones_validas, config_hoja, fila_inicio, columna_inicio
) -> int:
    columnas = config_hoja["columnas"]
    for desplazamiento, columna in enumerate(columnas):
        celda = hoja.cell(
            row=fila_inicio,
            column=columna_inicio + desplazamiento,
            value=columna["titulo"],
        )
        aplicar_estilo_encabezado_tabla(celda)
    fila = fila_inicio + 1
    for combinacion in combinaciones_validas:
        for componente in combinacion["componentes"]:
            for desplazamiento, columna in enumerate(columnas):
                valor = _resolver_fuente(columna["fuente"], combinacion, componente)
                celda = hoja.cell(row=fila, column=columna_inicio + desplazamiento, value=valor)
                aplicar_estilo_fila_dato(celda)
            fila += 1
    return len(columnas)


# ── Layout por_combinacion ────────────────────────────────────────────────────

def _escribir_layout_por_combinacion(
    hoja, combinaciones_validas, config_hoja, fila_inicio, columna_inicio
) -> int:
    titulo_combinacion = config_hoja.get("titulo_combinacion", "Case")

    nombres_estados = _extraer_nombres_estados_en_orden(combinaciones_validas)

    celda = hoja.cell(row=fila_inicio, column=columna_inicio, value=titulo_combinacion)
    aplicar_estilo_encabezado_tabla(celda)
    for desplazamiento, nombre in enumerate(nombres_estados, start=1):
        celda = hoja.cell(row=fila_inicio, column=columna_inicio + desplazamiento, value=nombre)
        aplicar_estilo_encabezado_tabla(celda)

    fila = fila_inicio + 1
    for combinacion in combinaciones_validas:
        celda = hoja.cell(row=fila, column=columna_inicio, value=combinacion["nombre"])
        aplicar_estilo_fila_dato_acento(celda)
        indice_por_estado = {
            c["nombre_estado"]: c["factor"] * c["signo"]
            for c in combinacion["componentes"]
        }
        for desplazamiento, nombre in enumerate(nombres_estados, start=1):
            valor = indice_por_estado.get(nombre, None)
            celda = hoja.cell(row=fila, column=columna_inicio + desplazamiento, value=valor)
            aplicar_estilo_fila_dato(celda)
        fila += 1

    return 1 + len(nombres_estados)


def _extraer_nombres_estados_en_orden(combinaciones_validas: list[dict]) -> list[str]:
    vistos = set()
    nombres = []
    for combinacion in combinaciones_validas:
        for componente in combinacion["componentes"]:
            nombre = componente["nombre_estado"]
            if nombre not in vistos:
                vistos.add(nombre)
                nombres.append(nombre)
    return nombres


def _resolver_fuente(fuente: str, combinacion: dict, componente: dict):
    if fuente == "nombre_combinacion":
        return combinacion["nombre"]
    if fuente == "nombre_estado":
        return componente["nombre_estado"]
    if fuente == "factor_por_signo":
        return componente["factor"] * componente["signo"]
    raise ValueError(f"Fuente de columna desconocida: '{fuente}'")


# ── Tabla 2: nombres de combinaciones ─────────────────────────────────────────

def _escribir_tabla_nombres(
    hoja,
    combinaciones_validas: list[dict],
    config_tabla: dict,
    fila_inicio: int,
    columna_inicio: int,
) -> None:
    celda = hoja.cell(row=fila_inicio, column=columna_inicio, value=config_tabla["titulo"])
    aplicar_estilo_encabezado_tabla(celda)
    fila = fila_inicio + 1
    for combinacion in combinaciones_validas:
        celda = hoja.cell(row=fila, column=columna_inicio, value=combinacion["nombre"])
        aplicar_estilo_fila_dato(celda)
        fila += 1


# ── Tabla 3: envolventes ──────────────────────────────────────────────────────

def _escribir_tabla_envolventes(
    hoja,
    filas_envolventes: list[dict],
    config_tabla: dict,
    fila_inicio: int,
    columna_inicio: int,
) -> None:
    columnas = config_tabla["columnas"]
    for desplazamiento, columna in enumerate(columnas):
        celda = hoja.cell(
            row=fila_inicio,
            column=columna_inicio + desplazamiento,
            value=columna["titulo"],
        )
        aplicar_estilo_encabezado_tabla(celda)

    fuentes_por_id = {
        "envelope": "nombre_envolvente",
        "combination": "nombre_combinacion",
        "factor": "factor",
    }

    fila = fila_inicio + 1
    for fila_dato in filas_envolventes:
        for desplazamiento, columna in enumerate(columnas):
            clave = fuentes_por_id.get(columna["id"])
            valor = fila_dato.get(clave) if clave else None
            celda = hoja.cell(row=fila, column=columna_inicio + desplazamiento, value=valor)
            aplicar_estilo_fila_dato(celda)
        fila += 1


# ── Validaciones ──────────────────────────────────────────────────────────────

def _validar_config_resumen(config_resumen: dict) -> None:
    campos_requeridos = ["nombre_hoja", "fila_inicio", "columna_inicio", "secciones"]
    for campo in campos_requeridos:
        if campo not in config_resumen:
            raise ValueError(f"config_resumen: falta el campo obligatorio '{campo}'.")
    for seccion in config_resumen["secciones"]:
        if "id" not in seccion or "titulo" not in seccion:
            raise ValueError(
                "config_resumen: cada sección debe tener los campos 'id' y 'titulo'."
            )


def _validar_config_exportador(config_exportador: dict) -> None:
    if "metadata" not in config_exportador:
        raise ValueError("config_exportador: falta el campo 'metadata'.")
    if "software_name" not in config_exportador["metadata"]:
        raise ValueError("config_exportador: falta el campo 'metadata.software_name'.")
    if "hoja" not in config_exportador:
        raise ValueError("config_exportador: falta el campo 'hoja'.")

    config_hoja = config_exportador["hoja"]

    if "tabla_combinaciones" not in config_hoja:
        raise ValueError("config_exportador: falta el campo 'hoja.tabla_combinaciones'.")

    config_tabla_combinaciones = config_hoja["tabla_combinaciones"]

    if "layout" not in config_tabla_combinaciones:
        raise ValueError("config_exportador: falta el campo 'hoja.tabla_combinaciones.layout'.")

    layouts_validos = ("por_componente", "por_combinacion")
    if config_tabla_combinaciones["layout"] not in layouts_validos:
        raise ValueError(
            f"config_exportador: 'hoja.tabla_combinaciones.layout' tiene un valor inválido: "
            f"'{config_tabla_combinaciones['layout']}'. Valores posibles: {layouts_validos}."
        )

    if config_tabla_combinaciones["layout"] == "por_componente":
        if "columnas" not in config_tabla_combinaciones:
            raise ValueError(
                "config_exportador: layout 'por_componente' requiere el campo "
                "'hoja.tabla_combinaciones.columnas'."
            )
        for columna in config_tabla_combinaciones["columnas"]:
            for campo in ("id", "titulo", "fuente"):
                if campo not in columna:
                    raise ValueError(
                        f"config_exportador: la columna '{columna.get('id', '?')}' "
                        f"no tiene el campo obligatorio '{campo}'."
                    )


def _validar_ruta_destino(ruta_destino: str) -> None:
    ruta = Path(ruta_destino)
    if not ruta.parent.exists():
        raise ValueError(f"El directorio de destino no existe: '{ruta.parent}'.")
    if ruta.exists() and not ruta.is_file():
        raise ValueError(f"La ruta de destino existe pero no es un archivo: '{ruta_destino}'.")
