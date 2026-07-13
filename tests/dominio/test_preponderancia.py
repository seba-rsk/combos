from __future__ import annotations

from dominio.preponderancia import marcar_superadas


def test_marcar_superadas_dominancia_estricta_marca_la_dominada(
    hacer_componente, hacer_combinacion
):
    # Ambos factores de D quedan del mismo lado de 1 (Regla 3): son
    # combinaciones de la misma "familia" (ambas amplificadas), por lo
    # que sí resultan comparables entre sí.
    tipos_permanentes = ["D"]
    dominante = hacer_combinacion(
        1, "ELU",
        [hacer_componente("DEAD", "D", 1.4), hacer_componente("SC", "L", 1.6)],
    )
    dominada = hacer_combinacion(
        2, "ELU",
        [hacer_componente("DEAD", "D", 1.2), hacer_componente("SC", "L", 1.0)],
    )

    resultado = marcar_superadas([dominante, dominada], tipos_permanentes)

    assert resultado[0].esta_superada is False
    assert resultado[1].esta_superada is True
    assert resultado[1].superada_por == 1


def test_marcar_superadas_factores_mixtos_no_son_comparables(
    hacer_componente, hacer_combinacion
):
    # x tiene un factor mayor y otro menor que y: ninguna domina a la otra.
    tipos_permanentes = ["D"]
    combo_x = hacer_combinacion(
        1, "ELU",
        [hacer_componente("DEAD", "D", 1.4), hacer_componente("SC", "L", 1.0)],
    )
    combo_y = hacer_combinacion(
        2, "ELU",
        [hacer_componente("DEAD", "D", 1.2), hacer_componente("SC", "L", 1.6)],
    )

    resultado = marcar_superadas([combo_x, combo_y], tipos_permanentes)

    assert resultado[0].esta_superada is False
    assert resultado[1].esta_superada is False


def test_marcar_superadas_distinto_estado_limite_no_se_comparan(
    hacer_componente, hacer_combinacion
):
    tipos_permanentes = ["D"]
    combo_elu = hacer_combinacion(
        1, "ELU", [hacer_componente("DEAD", "D", 1.4)]
    )
    combo_els = hacer_combinacion(
        2, "ELS", [hacer_componente("DEAD", "D", 1.0)]
    )

    resultado = marcar_superadas([combo_elu, combo_els], tipos_permanentes)

    assert not resultado[0].esta_superada
    assert not resultado[1].esta_superada


def test_marcar_superadas_distinto_conjunto_de_estados_no_se_comparan(
    hacer_componente, hacer_combinacion
):
    tipos_permanentes = ["D"]
    combo_d = hacer_combinacion(
        1, "ELU", [hacer_componente("DEAD", "D", 1.4)]
    )
    combo_dl = hacer_combinacion(
        2, "ELU",
        [hacer_componente("DEAD", "D", 1.2), hacer_componente("SC", "L", 1.6)],
    )

    resultado = marcar_superadas([combo_d, combo_dl], tipos_permanentes)

    assert not resultado[0].esta_superada
    assert not resultado[1].esta_superada


def test_marcar_superadas_distinto_signo_no_se_comparan(
    hacer_componente, hacer_combinacion
):
    tipos_permanentes = ["D"]
    combo_positivo = hacer_combinacion(
        1, "ELU", [hacer_componente("DEAD", "D", 1.4, signo=1)]
    )
    combo_negativo = hacer_combinacion(
        2, "ELU", [hacer_componente("DEAD", "D", 1.4, signo=-1)]
    )

    resultado = marcar_superadas(
        [combo_positivo, combo_negativo], tipos_permanentes
    )

    assert not resultado[0].esta_superada
    assert not resultado[1].esta_superada


def test_marcar_superadas_un_solo_tipo_de_carga_permite_comparar(
    hacer_componente, hacer_combinacion
):
    """
    Caso especial documentado en README: combinaciones compuestas por un
    único tipo de carga sí se comparan aunque un factor sea <1 y el otro
    >=1 (ej. 0.9D superada por 1.4D), a diferencia del caso general.
    """
    tipos_permanentes = ["D"]
    combo_09d = hacer_combinacion(
        1, "ELU", [hacer_componente("DEAD", "D", 0.9)]
    )
    combo_14d = hacer_combinacion(
        2, "ELU", [hacer_componente("DEAD", "D", 1.4)]
    )

    resultado = marcar_superadas([combo_09d, combo_14d], tipos_permanentes)

    assert resultado[0].esta_superada is True
    assert resultado[0].superada_por == 2
    assert resultado[1].esta_superada is False


def test_marcar_superadas_direccionales_con_nombres_distintos_no_se_comparan(
    hacer_componente, hacer_combinacion
):
    # Wx y Wy son ambos del grupo direccional W-1, pero son estados
    # distintos (direcciones distintas): no deben tratarse como
    # intercambiables para el análisis de dominancia.
    tipos_permanentes = ["D"]
    combo_wx = hacer_combinacion(
        1, "ELU",
        [
            hacer_componente("DEAD", "D", 1.2),
            hacer_componente("Wx", "W", 1.6),
        ],
    )
    combo_wy = hacer_combinacion(
        2, "ELU",
        [
            hacer_componente("DEAD", "D", 1.2),
            hacer_componente("Wy", "W", 1.6),
        ],
    )

    resultado = marcar_superadas([combo_wx, combo_wy], tipos_permanentes)

    assert not resultado[0].esta_superada
    assert not resultado[1].esta_superada


def test_marcar_superadas_no_reemplaza_una_superacion_ya_marcada(
    hacer_componente, hacer_combinacion
):
    # C es superada tanto por A como por B; debe conservar la primera
    # que la marcó y no sobreescribirla con la segunda.
    tipos_permanentes = ["D"]
    combo_a = hacer_combinacion(1, "ELU", [hacer_componente("DEAD", "D", 1.4)])
    combo_b = hacer_combinacion(2, "ELU", [hacer_componente("DEAD", "D", 1.3)])
    combo_c = hacer_combinacion(3, "ELU", [hacer_componente("DEAD", "D", 1.0)])

    resultado = marcar_superadas(
        [combo_a, combo_b, combo_c], tipos_permanentes
    )

    assert resultado[2].esta_superada is True
    assert resultado[2].superada_por == 1


def test_marcar_superadas_lista_vacia_no_falla():
    assert marcar_superadas([], ["D"]) == []
