from __future__ import annotations

from combos.dominio.duplicados import marcar_duplicadas


def test_marcar_duplicadas_combinaciones_identicas_se_marcan(
    hacer_componente, hacer_combinacion
):
    componentes = [hacer_componente("DEAD", "D", 1.4)]
    combinaciones = [
        hacer_combinacion(1, "ELU", componentes),
        hacer_combinacion(2, "ELU", [hacer_componente("DEAD", "D", 1.4)]),
    ]

    resultado = marcar_duplicadas(combinaciones)

    assert resultado[0].es_duplicada is False
    assert resultado[1].es_duplicada is True
    assert resultado[1].duplicada_por == 1


def test_marcar_duplicadas_orden_de_componentes_no_importa(
    hacer_componente, hacer_combinacion
):
    componente_dead = hacer_componente("DEAD", "D", 1.2)
    componente_sc = hacer_componente("SC", "L", 1.6)
    combinaciones = [
        hacer_combinacion(1, "ELU", [componente_dead, componente_sc]),
        hacer_combinacion(2, "ELU", [componente_sc, componente_dead]),
    ]

    resultado = marcar_duplicadas(combinaciones)

    assert resultado[1].es_duplicada is True


def test_marcar_duplicadas_distinto_estado_limite_no_son_duplicadas(
    hacer_componente, hacer_combinacion
):
    combinaciones = [
        hacer_combinacion(1, "ELU", [hacer_componente("DEAD", "D", 1.0)]),
        hacer_combinacion(2, "ELS", [hacer_componente("DEAD", "D", 1.0)]),
    ]

    resultado = marcar_duplicadas(combinaciones)

    assert all(not c.es_duplicada for c in resultado)


def test_marcar_duplicadas_distinto_factor_no_son_duplicadas(
    hacer_componente, hacer_combinacion
):
    combinaciones = [
        hacer_combinacion(1, "ELU", [hacer_componente("DEAD", "D", 1.2)]),
        hacer_combinacion(2, "ELU", [hacer_componente("DEAD", "D", 1.4)]),
    ]

    resultado = marcar_duplicadas(combinaciones)

    assert all(not c.es_duplicada for c in resultado)


def test_marcar_duplicadas_distinto_signo_no_son_duplicadas(
    hacer_componente, hacer_combinacion
):
    combinaciones = [
        hacer_combinacion(
            1, "ELU", [hacer_componente("DEAD", "D", 0.9, signo=1)]
        ),
        hacer_combinacion(
            2, "ELU", [hacer_componente("DEAD", "D", 0.9, signo=-1)]
        ),
    ]

    resultado = marcar_duplicadas(combinaciones)

    assert all(not c.es_duplicada for c in resultado)


def test_marcar_duplicadas_lista_vacia_no_falla(hacer_componente):
    assert marcar_duplicadas([]) == []
