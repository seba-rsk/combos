from __future__ import annotations


def marcar_duplicadas(combinaciones: list[dict]) -> list[dict]:
    registro: dict[tuple, int] = {}
    for combinacion in combinaciones:
        clave = _construir_clave_canonica(combinacion)
        if clave not in registro:
            registro[clave] = combinacion["indice_generacion"]
        else:
            combinacion["es_duplicada"] = True
            combinacion["duplicada_por"] = registro[clave]
    return combinaciones


def _construir_clave_canonica(combinacion: dict) -> tuple:
    return (
        combinacion["estado_limite"],
        _canonizar_componentes(combinacion["componentes"]),
    )


def _canonizar_componentes(componentes: list[dict]) -> frozenset:
    return frozenset(
        _componente_a_tupla(componente)
        for componente in componentes
    )


def _componente_a_tupla(componente: dict) -> tuple:
    return (
        componente["nombre_estado"].casefold(),
        componente["factor"],
        componente["signo"],
    )