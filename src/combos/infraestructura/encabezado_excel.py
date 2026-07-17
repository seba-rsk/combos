from __future__ import annotations

from datetime import datetime

from combos.dominio.modelos import EleccionParametro
from combos.infraestructura.estilos_excel import (
    ajustar_ancho_columna_titulo,
    aplicar_estilo_etiqueta_hoja,
    aplicar_estilo_label_metadata,
    aplicar_estilo_titulo_programa,
    aplicar_estilo_valor_metadata,
)
from combos.infraestructura.sanitizacion_excel import neutralizar_texto_libre

_FORMATO_FECHA_ENCABEZADO = "%d/%m/%Y %H:%M"


def escribir_encabezado_programa(
    hoja,
    fila: int,
    columna: int,
    reglamento: dict,
    nombre_perfil: str,
    version: str,
    etiqueta: str,
    nombre_programa: str = "COMBOS",
    mostrar_reglamento: bool = True,
    mostrar_fecha: bool = True,
    elecciones: list[EleccionParametro] | None = None,
) -> int:
    """
    Escribe el bloque de encabezado (título del programa, perfil usado,
    parámetros elegidos si los hay, datos del reglamento y fecha) que
    comparten la hoja de resumen y la planilla de entrada, con la
    etiqueta de hoja ("SALIDA DE DATOS" / "ENTRADA DE DATOS") como única
    diferencia real entre ambas.

    Returns:
        La fila siguiente a la última escrita.
    """
    fila = _escribir_titulo(
        hoja, fila, columna, nombre_programa, version, etiqueta
    )
    fila = _escribir_fila_metadata(
        hoja, fila, columna,
        "Perfil usado:", neutralizar_texto_libre(nombre_perfil),
    )
    for eleccion in elecciones or []:
        fila = _escribir_fila_metadata(
            hoja, fila, columna,
            neutralizar_texto_libre(f"{eleccion.nombre}:"),
            neutralizar_texto_libre(
                f"{eleccion.valor} — {eleccion.etiqueta}"
            ),
        )
    if mostrar_reglamento:
        fila = _escribir_bloque_reglamento(
            hoja, fila, columna, reglamento.get("metadata", {})
        )
    if mostrar_fecha:
        fila = _escribir_fila_metadata(
            hoja, fila, columna,
            "Fecha:", datetime.now().strftime(_FORMATO_FECHA_ENCABEZADO),
        )
    return fila


def _escribir_titulo(
    hoja, fila: int, columna: int,
    nombre_programa: str, version: str, etiqueta: str,
) -> int:
    celda = hoja.cell(
        row=fila, column=columna, value=f"{nombre_programa} v{version}"
    )
    aplicar_estilo_titulo_programa(celda)
    ajustar_ancho_columna_titulo(hoja, columna, celda.value)

    celda_etiqueta = hoja.cell(row=fila, column=columna + 1, value=etiqueta)
    aplicar_estilo_etiqueta_hoja(celda_etiqueta)
    return fila + 1


def _escribir_fila_metadata(
    hoja, fila: int, columna: int, etiqueta: str, valor: str
) -> int:
    aplicar_estilo_label_metadata(
        hoja.cell(row=fila, column=columna, value=etiqueta)
    )
    aplicar_estilo_valor_metadata(
        hoja.cell(row=fila, column=columna + 1, value=valor)
    )
    return fila + 1


def _escribir_bloque_reglamento(
    hoja, fila: int, columna: int, metadata: dict
) -> int:
    code_name = metadata.get("code_name", "")
    code_version = metadata.get("code_version", "")
    valor_reglamento = (
        f"{code_name} - {code_version}" if code_name or code_version else ""
    )
    fila = _escribir_fila_metadata(
        hoja, fila, columna,
        "Reglamento:", neutralizar_texto_libre(valor_reglamento),
    )
    fila = _escribir_fila_metadata(
        hoja, fila, columna,
        "País:", neutralizar_texto_libre(metadata.get("country", "")),
    )
    fila = _escribir_fila_metadata(
        hoja, fila, columna,
        "Descripción:",
        neutralizar_texto_libre(metadata.get("description", "")),
    )
    return fila
