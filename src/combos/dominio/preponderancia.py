from __future__ import annotations

from combos.dominio.modelos import Combinacion, Componente


def marcar_superadas(
    combinaciones: list[Combinacion], tipos_permanentes: list[str]
) -> list[Combinacion]:
    """
    Detecta relaciones de dominancia entre combinaciones comparables del
    mismo estado límite y marca como superada a la combinación dominada.

    Dos combinaciones son comparables cuando pasan las reglas 0 a 4 (mismo
    estado límite, mismo conjunto de estados, mismo signo por estado,
    coherencia de magnitud sobre cargas permanentes y estados
    direccionales idénticos). Entre comparables, la regla 5 determina cuál
    domina: la que tiene todos sus factores mayores o iguales, con al
    menos uno estrictamente mayor.

    Args:
        combinaciones: Combinaciones ya marcadas por
            dominio.duplicados.marcar_duplicadas (las duplicadas quedan
            excluidas de la comparación).
        tipos_permanentes: Tipos de carga permanente declarados en el
            reglamento ("permanent_load_types"), usados por la regla 3.

    Returns:
        La misma lista de combinaciones, modificada in place: cada
        combinación superada queda con "esta_superada" en True y
        "superada_por" apuntando al índice de generación de la dominante.
    """
    candidatas = [c for c in combinaciones if not c.es_duplicada]

    for i, combinacion_x in enumerate(candidatas):
        for combinacion_y in candidatas[i + 1:]:
            _evaluar_par(combinacion_x, combinacion_y, tipos_permanentes)

    return combinaciones


def _evaluar_par(
    combinacion_x: Combinacion,
    combinacion_y: Combinacion,
    tipos_permanentes: list[str],
) -> None:
    if not _son_comparables(combinacion_x, combinacion_y, tipos_permanentes):
        return

    dominancia = _aplicar_regla_5(combinacion_x, combinacion_y)

    if dominancia == "x_supera_y":
        _marcar_como_superada(combinacion_y, combinacion_x.indice_generacion)
    elif dominancia == "y_supera_x":
        _marcar_como_superada(combinacion_x, combinacion_y.indice_generacion)


def _marcar_como_superada(
    combinacion: Combinacion, indice_superador: int
) -> None:
    if not combinacion.esta_superada:
        combinacion.esta_superada = True
        combinacion.superada_por = indice_superador


def _son_comparables(
    combinacion_x: Combinacion,
    combinacion_y: Combinacion,
    tipos_permanentes: list[str],
) -> bool:
    if not _regla_0_mismo_estado_limite(combinacion_x, combinacion_y):
        return False

    componentes_x = combinacion_x.componentes
    componentes_y = combinacion_y.componentes

    if not _regla_1_mismo_conjunto_estados(componentes_x, componentes_y):
        return False

    pares = _parear_por_grupo(componentes_x, componentes_y)

    if not _regla_2_mismo_signo_por_estado(pares):
        return False

    if not _es_combinacion_de_un_tipo_de_carga(combinacion_x) \
            and not _es_combinacion_de_un_tipo_de_carga(combinacion_y):
        if not _regla_3_coherencia_magnitud(pares, tipos_permanentes):
            return False

    if not _regla_4_estados_direccionales_identicos(pares):
        return False

    return True


def _regla_0_mismo_estado_limite(
    combinacion_x: Combinacion, combinacion_y: Combinacion
) -> bool:
    return combinacion_x.estado_limite == combinacion_y.estado_limite


def _regla_1_mismo_conjunto_estados(
    componentes_x: list[Componente], componentes_y: list[Componente]
) -> bool:
    grupos_x = frozenset(_obtener_clave_grupo(c) for c in componentes_x)
    grupos_y = frozenset(_obtener_clave_grupo(c) for c in componentes_y)
    return grupos_x == grupos_y


def _regla_2_mismo_signo_por_estado(
    pares: list[tuple[Componente, Componente]],
) -> bool:
    return all(cx.signo == cy.signo for cx, cy in pares)


def _regla_3_coherencia_magnitud(
    pares: list[tuple[Componente, Componente]],
    tipos_permanentes: list[str],
) -> bool:
    for cx, cy in pares:
        if cx.tipo_carga not in tipos_permanentes:
            continue
        factor_x = cx.factor
        factor_y = cy.factor
        if (factor_x > 1) != (factor_y > 1):
            return False
    return True


def _regla_4_estados_direccionales_identicos(
    pares: list[tuple[Componente, Componente]],
) -> bool:
    return all(
        cx.nombre_estado.casefold() == cy.nombre_estado.casefold()
        for cx, cy in pares
    )


def _aplicar_regla_5(
    combinacion_x: Combinacion, combinacion_y: Combinacion
) -> str | None:
    pares = _parear_por_nombre(
        combinacion_x.componentes, combinacion_y.componentes
    )
    x_mayor_en_alguno = any(cx.factor > cy.factor for cx, cy in pares)
    y_mayor_en_alguno = any(cy.factor > cx.factor for cx, cy in pares)

    if x_mayor_en_alguno and not y_mayor_en_alguno:
        return "x_supera_y"
    if y_mayor_en_alguno and not x_mayor_en_alguno:
        return "y_supera_x"
    return None


def _parear_por_grupo(
    componentes_x: list[Componente], componentes_y: list[Componente]
) -> list[tuple[Componente, Componente]]:
    indice_y = {_obtener_clave_grupo(c): c for c in componentes_y}
    return [(cx, indice_y[_obtener_clave_grupo(cx)]) for cx in componentes_x]


def _parear_por_nombre(
    componentes_x: list[Componente], componentes_y: list[Componente]
) -> list[tuple[Componente, Componente]]:
    indice_y = {c.nombre_estado.casefold(): c for c in componentes_y}
    return [
        (cx, indice_y[cx.nombre_estado.casefold()]) for cx in componentes_x
    ]


def _obtener_clave_grupo(componente: Componente) -> str:
    """
    Variantes direccionales distintas (ej. Wx y Wy del mismo grupo W-1)
    se agrupan por su propio nombre de estado, no por el grupo: son
    acciones físicamente distintas y no deben tratarse como
    intercambiables para el análisis de dominancia.
    """
    return componente.nombre_estado.casefold()


def _es_combinacion_de_un_tipo_de_carga(combinacion: Combinacion) -> bool:
    return len({c.tipo_carga for c in combinacion.componentes}) == 1
