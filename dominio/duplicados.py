from __future__ import annotations

from dominio.modelos import Combinacion, Componente


def marcar_duplicadas(
    combinaciones: list[Combinacion],
) -> list[Combinacion]:
    """
    Marca como duplicada toda combinación cuyos componentes (nombre de
    estado, factor y signo) coincidan exactamente con los de otra ya vista
    dentro del mismo estado límite, sin importar el orden de los componentes.

    Args:
        combinaciones: Combinaciones generadas por
            dominio.generador.generar_combinaciones.

    Returns:
        La misma lista de combinaciones, modificada in place: cada
        duplicada queda con "es_duplicada" en True y "duplicada_por"
        apuntando al índice de generación de la primera combinación
        equivalente.
    """
    registro: dict[tuple, int] = {}
    for combinacion in combinaciones:
        clave = _construir_clave_canonica(combinacion)
        if clave not in registro:
            registro[clave] = combinacion.indice_generacion
        else:
            combinacion.es_duplicada = True
            combinacion.duplicada_por = registro[clave]
    return combinaciones


def _construir_clave_canonica(combinacion: Combinacion) -> tuple:
    return (
        combinacion.estado_limite,
        _canonizar_componentes(combinacion.componentes),
    )


def _canonizar_componentes(componentes: list[Componente]) -> frozenset:
    return frozenset(
        _componente_a_tupla(componente)
        for componente in componentes
    )


def _componente_a_tupla(componente: Componente) -> tuple:
    return (
        componente.nombre_estado.casefold(),
        componente.factor,
        componente.signo,
    )
