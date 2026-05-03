from __future__ import annotations

from collections.abc import Iterator
from itertools import product as producto_cartesiano


def generar_combinaciones(estados: list[dict], reglamento: dict) -> list[dict]:
    combinaciones: list[dict] = []
    indice_generacion = 1
    for id_estado_limite, lista_combinaciones_base in reglamento["combinations"].items():
        for combinacion_base in lista_combinaciones_base:
            for componentes in _iterar_variantes_de_componentes(estados, combinacion_base):
                combinaciones.append(
                    _construir_combinacion(
                        indice_generacion,
                        id_estado_limite,
                        combinacion_base["id"],
                        componentes,
                    )
                )
                indice_generacion += 1
    return combinaciones


# ── Iteración de variantes ────────────────────────────────────────────────────

def _iterar_variantes_de_componentes(
    estados: list[dict],
    combinacion_base: dict,
) -> Iterator[list[dict]]:
    factores = combinacion_base["factors"]
    estados_simples = _filtrar_estados_simples(estados, factores)
    grupos_direccionales = _agrupar_estados_direccionales_por_nombre(estados, factores)

    if not estados_simples and not grupos_direccionales:
        return

    componentes_simples = [
        _construir_componente(estado, factores[estado["tipo_carga"]])
        for estado in estados_simples
    ]

    if not grupos_direccionales:
        yield componentes_simples
        return

    nombres_grupos_en_orden = _ordenar_grupos_por_aparicion(estados, grupos_direccionales)
    opciones_por_grupo = [grupos_direccionales[nombre] for nombre in nombres_grupos_en_orden]

    for seleccion in producto_cartesiano(*opciones_por_grupo):
        componentes_direccionales = [
            _construir_componente(estado, factores[estado["tipo_carga"]])
            for estado in seleccion
        ]
        yield componentes_simples + componentes_direccionales


# ── Filtrado y agrupamiento ───────────────────────────────────────────────────

def _filtrar_estados_simples(estados: list[dict], factores: dict) -> list[dict]:
    return [
        estado for estado in estados
        if estado["tipo_estado"] == "simple" and estado["tipo_carga"] in factores
    ]


def _agrupar_estados_direccionales_por_nombre(
    estados: list[dict],
    factores: dict,
) -> dict[str, list[dict]]:
    grupos: dict[str, list[dict]] = {}
    for estado in estados:
        if estado["tipo_estado"] != "direccional":
            continue
        if estado["tipo_carga"] not in factores:
            continue
        nombre_grupo = estado["nombre_grupo"]
        if nombre_grupo not in grupos:
            grupos[nombre_grupo] = []
        grupos[nombre_grupo].append(estado)
    return grupos


def _ordenar_grupos_por_aparicion(
    estados: list[dict],
    grupos_direccionales: dict,
) -> list[str]:
    nombres_en_orden: list[str] = []
    for estado in estados:
        nombre_grupo = estado.get("nombre_grupo")
        if nombre_grupo in grupos_direccionales and nombre_grupo not in nombres_en_orden:
            nombres_en_orden.append(nombre_grupo)
    return nombres_en_orden


# ── Construcción de objetos ───────────────────────────────────────────────────

def _construir_componente(estado: dict, factor: float) -> dict:
    return {
        "nombre_estado": estado["nombre_estado"],
        "tipo_carga": estado["tipo_carga"],
        "factor": factor,
        "signo": estado["signo"],
    }


def _construir_combinacion(
    indice_generacion: int,
    id_estado_limite: str,
    combinacion_base_id: int,
    componentes: list[dict],
) -> dict:
    return {
        "indice_generacion": indice_generacion,
        "estado_limite": id_estado_limite,
        "combinacion_base_id": combinacion_base_id,
        "componentes": componentes,
        "es_duplicada": False,
        "duplicada_por": None,
        "esta_superada": False,
        "superada_por": None,
        "descartada_por_usuario": False,
        "nombre": None,
    }