from __future__ import annotations

from collections.abc import Iterator
from itertools import product as producto_cartesiano

from dominio.modelos import Combinacion, Componente, Estado


def generar_combinaciones(
    estados: list[Estado], reglamento: dict
) -> list[Combinacion]:
    """
    Genera todas las combinaciones de carga posibles a partir de los estados
    ingresados por el usuario y las combinaciones base definidas en el
    reglamento, expandiendo los grupos direccionales por producto cartesiano.

    Args:
        estados: Estados de carga ya enriquecidos (ver
            dominio.lector_plantilla.leer_plantilla), con variantes de
            signo ya resueltas para los estados direccionales.
        reglamento: Reglamento ya validado (ver
            dominio.lector_yaml.leer_reglamento).

    Returns:
        Lista de combinaciones generadas, cada una sin nombre asignado
        todavía y con los campos de duplicado/superación en su valor
        inicial (ver dominio.duplicados y dominio.preponderancia).
    """
    combinaciones: list[Combinacion] = []
    indice_generacion = 1
    bases_por_estado = reglamento["combinations"].items()
    for id_estado_limite, lista_combinaciones_base in bases_por_estado:
        for combinacion_base in lista_combinaciones_base:
            variantes = _iterar_variantes_de_componentes(
                estados, combinacion_base
            )
            for componentes in variantes:
                combinaciones.append(
                    Combinacion(
                        indice_generacion=indice_generacion,
                        estado_limite=id_estado_limite,
                        combinacion_base_id=combinacion_base["id"],
                        componentes=componentes,
                    )
                )
                indice_generacion += 1
    return combinaciones


# ── Iteración de variantes ────────────────────────────────────────────────────

def _iterar_variantes_de_componentes(
    estados: list[Estado],
    combinacion_base: dict,
) -> Iterator[list[Componente]]:
    factores = combinacion_base["factors"]
    estados_simples = _filtrar_estados_simples(estados, factores)
    grupos_direccionales = _agrupar_estados_direccionales_por_nombre(
        estados, factores
    )

    if not estados_simples and not grupos_direccionales:
        return

    componentes_simples = [
        _construir_componente(estado, factores[estado.tipo_carga])
        for estado in estados_simples
    ]

    if not grupos_direccionales:
        yield componentes_simples
        return

    nombres_grupos_en_orden = _ordenar_grupos_por_aparicion(
        estados, grupos_direccionales
    )
    opciones_por_grupo = [
        grupos_direccionales[nombre] for nombre in nombres_grupos_en_orden
    ]

    for seleccion in producto_cartesiano(*opciones_por_grupo):
        componentes_direccionales = [
            _construir_componente(estado, factores[estado.tipo_carga])
            for estado in seleccion
        ]
        yield componentes_simples + componentes_direccionales


# ── Filtrado y agrupamiento ───────────────────────────────────────────────────

def _filtrar_estados_simples(
    estados: list[Estado], factores: dict
) -> list[Estado]:
    return [
        estado for estado in estados
        if estado.tipo_estado == "simple"
        and estado.tipo_carga in factores
    ]


def _agrupar_estados_direccionales_por_nombre(
    estados: list[Estado],
    factores: dict,
) -> dict[str, list[Estado]]:
    grupos: dict[str, list[Estado]] = {}
    for estado in estados:
        if estado.tipo_estado != "direccional":
            continue
        if estado.tipo_carga not in factores:
            continue
        nombre_grupo = estado.nombre_grupo
        if nombre_grupo not in grupos:
            grupos[nombre_grupo] = []
        grupos[nombre_grupo].append(estado)
    return grupos


def _ordenar_grupos_por_aparicion(
    estados: list[Estado],
    grupos_direccionales: dict,
) -> list[str]:
    nombres_en_orden: list[str] = []
    for estado in estados:
        nombre_grupo = estado.nombre_grupo
        if (
            nombre_grupo in grupos_direccionales
            and nombre_grupo not in nombres_en_orden
        ):
            nombres_en_orden.append(nombre_grupo)
    return nombres_en_orden


# ── Construcción de objetos ───────────────────────────────────────────────────

def _construir_componente(estado: Estado, factor: float) -> Componente:
    return Componente(
        nombre_estado=estado.nombre_estado,
        tipo_carga=estado.tipo_carga,
        factor=factor,
        signo=estado.signo,
    )
