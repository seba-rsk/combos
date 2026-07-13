from __future__ import annotations

from datetime import datetime

from infraestructura.estilos_excel import (
    aplicar_estilo_titulo_programa,
    aplicar_estilo_etiqueta_hoja,
    aplicar_estilo_label_metadata,
    aplicar_estilo_valor_metadata,
    ajustar_ancho_columna_titulo,
)
from infraestructura.sanitizacion_excel import neutralizar_texto_libre


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
) -> int:
    """
    Escribe el bloque de encabezado (título del programa, perfil usado,
    datos del reglamento y fecha) que comparten la hoja de resumen y la
    planilla de entrada, con la etiqueta de hoja ("SALIDA DE DATOS" /
    "ENTRADA DE DATOS") como única diferencia real entre ambas.

    Returns:
        La fila siguiente a la última escrita.
    """
    metadata = reglamento.get("metadata", {})

    celda = hoja.cell(
        row=fila, column=columna, value=f"{nombre_programa} v{version}"
    )
    aplicar_estilo_titulo_programa(celda)
    ajustar_ancho_columna_titulo(hoja, columna, celda.value)

    celda_etiqueta = hoja.cell(row=fila, column=columna + 1, value=etiqueta)
    aplicar_estilo_etiqueta_hoja(celda_etiqueta)
    fila += 1

    aplicar_estilo_label_metadata(
        hoja.cell(row=fila, column=columna, value="Perfil usado:")
    )
    aplicar_estilo_valor_metadata(
        hoja.cell(
            row=fila,
            column=columna + 1,
            value=neutralizar_texto_libre(nombre_perfil),
        )
    )
    fila += 1

    if mostrar_reglamento:
        code_name = metadata.get("code_name", "")
        code_version = metadata.get("code_version", "")
        valor_reglamento = (
            f"{code_name} - {code_version}" if code_name or code_version else ""
        )
        aplicar_estilo_label_metadata(
            hoja.cell(row=fila, column=columna, value="Reglamento:")
        )
        aplicar_estilo_valor_metadata(
            hoja.cell(
                row=fila,
                column=columna + 1,
                value=neutralizar_texto_libre(valor_reglamento),
            )
        )
        fila += 1

        aplicar_estilo_label_metadata(
            hoja.cell(row=fila, column=columna, value="País:")
        )
        aplicar_estilo_valor_metadata(
            hoja.cell(
                row=fila,
                column=columna + 1,
                value=neutralizar_texto_libre(metadata.get("country", "")),
            )
        )
        fila += 1

        aplicar_estilo_label_metadata(
            hoja.cell(row=fila, column=columna, value="Descripción:")
        )
        aplicar_estilo_valor_metadata(
            hoja.cell(
                row=fila,
                column=columna + 1,
                value=neutralizar_texto_libre(metadata.get("description", "")),
            )
        )
        fila += 1

    if mostrar_fecha:
        aplicar_estilo_label_metadata(
            hoja.cell(row=fila, column=columna, value="Fecha:")
        )
        aplicar_estilo_valor_metadata(
            hoja.cell(
                row=fila,
                column=columna + 1,
                value=datetime.now().strftime("%d/%m/%Y %H:%M"),
            )
        )
        fila += 1

    return fila
