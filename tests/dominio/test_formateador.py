from __future__ import annotations

from dominio.formateador import formatear_componentes


def test_formatear_componentes_caso_tipico(hacer_componente):
    componentes = [
        hacer_componente("DEAD", "D", 1.4, signo=1),
        hacer_componente("SC", "L", 1.6, signo=1),
    ]

    resultado = formatear_componentes(componentes)

    assert resultado == "1.4 × DEAD  +  1.6 × SC"


def test_formatear_componentes_con_signo_negativo(hacer_componente):
    componentes = [
        hacer_componente("DEAD", "D", 0.9, signo=-1),
        hacer_componente("H", "H", 1.6, signo=1),
    ]

    resultado = formatear_componentes(componentes)

    assert resultado == "-0.9 × DEAD  +  1.6 × H"


def test_formatear_componentes_factor_entero_no_muestra_decimales_de_mas(
    hacer_componente,
):
    componentes = [hacer_componente("DEAD", "D", 1.0)]

    resultado = formatear_componentes(componentes)

    assert resultado == "1.0 × DEAD"


def test_formatear_componentes_lista_vacia_devuelve_cadena_vacia():
    assert formatear_componentes([]) == ""
