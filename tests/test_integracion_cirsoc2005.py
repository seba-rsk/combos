from __future__ import annotations

from pathlib import Path

import pytest

from combos.dominio.duplicados import marcar_duplicadas
from combos.dominio.generador import generar_combinaciones
from combos.dominio.lector_plantilla import leer_plantilla
from combos.dominio.lector_yaml import leer_reglamento
from combos.dominio.modelos import EstadoCrudo
from combos.dominio.parametros import (
    crear_eleccion,
    numero_opcion_default,
    resolver_parametros,
)
from combos.dominio.preponderancia import marcar_superadas

RUTA_PROFILES = Path(__file__).parent.parent / "src" / "combos" / "profiles"
RUTA_CIRSOC2005 = RUTA_PROFILES / "cirsoc2005.yaml"
RUTA_CIRSOC2005_ACTUALIZADO = RUTA_PROFILES / "cirsoc2005_actualizado.yaml"


@pytest.mark.integration
def test_ejemplo_del_readme_con_cirsoc2005():
    """
    Reproduce el ejemplo paso a paso documentado en README.md: con los
    estados DEAD (D), SC (L) y CP (D), el reglamento CIRSOC 2005 debe
    producir 26 combinaciones generadas, 17 duplicadas, 5 superadas
    y 4 combinaciones finales (si el usuario descarta todas las superadas).
    """
    reglamento = leer_reglamento(str(RUTA_CIRSOC2005))
    estados_crudos = [
        EstadoCrudo(
            nombre_estado="DEAD", tipo_carga="D", tipo_estado="simple",
            grupo=None, incluir_opuesto=False,
        ),
        EstadoCrudo(
            nombre_estado="SC", tipo_carga="L", tipo_estado="simple",
            grupo=None, incluir_opuesto=False,
        ),
        EstadoCrudo(
            nombre_estado="CP", tipo_carga="D", tipo_estado="simple",
            grupo=None, incluir_opuesto=False,
        ),
    ]

    estados = leer_plantilla(estados_crudos, reglamento)
    combinaciones = generar_combinaciones(estados, reglamento)
    assert len(combinaciones) == 26

    combinaciones = marcar_duplicadas(combinaciones)
    assert sum(1 for c in combinaciones if c.es_duplicada) == 17

    combinaciones = marcar_superadas(
        combinaciones, reglamento["permanent_load_types"]
    )
    assert sum(1 for c in combinaciones if c.esta_superada) == 5

    finales = [
        c for c in combinaciones
        if not c.es_duplicada and not c.esta_superada
    ]
    assert len(finales) == 4


def _ids_y_factores(combinations: dict) -> dict:
    """
    Proyección de las combinaciones sin el campo name, para comparar el
    contenido normativo entre perfiles que difieren solo en nombres.
    """
    return {
        id_estado: [
            {"id": c["id"], "factors": c["factors"]}
            for c in lista_combinaciones
        ]
        for id_estado, lista_combinaciones in combinations.items()
    }


@pytest.mark.integration
def test_cirsoc2005_actualizado_con_default_equivale_al_original():
    """
    El perfil cirsoc2005_actualizado.yaml parametriza el factor de L en
    las combinaciones ELU U3-U5 (`L_factor`: 1.0 default / 0.5). Con la
    opción default, el reglamento resuelto debe producir exactamente los
    mismos resultados que el CIRSOC 2005 original (que no tiene nombres
    normativos, por eso se comparan ids y factores).
    """
    reglamento = leer_reglamento(str(RUTA_CIRSOC2005_ACTUALIZADO))
    parametro = reglamento["parameters"]["L_factor"]
    eleccion_default = crear_eleccion(
        parametro, numero_opcion_default(parametro)
    )
    assert eleccion_default.valor == 1.0

    resuelto = resolver_parametros(reglamento, [eleccion_default])
    original = leer_reglamento(str(RUTA_CIRSOC2005))
    assert _ids_y_factores(resuelto["combinations"]) == _ids_y_factores(
        original["combinations"]
    )


@pytest.mark.integration
def test_cirsoc2005_actualizado_tiene_designaciones_normativas():
    """
    Las 26 combinaciones del perfil actualizado llevan su designación
    del reglamento (U1.1-U7.1 y S1.1-S3.1), y la resolución del
    parámetro las preserva.
    """
    reglamento = leer_reglamento(str(RUTA_CIRSOC2005_ACTUALIZADO))
    nombres_elu = [c["name"] for c in reglamento["combinations"]["ELU"]]
    nombres_els = [c["name"] for c in reglamento["combinations"]["ELS"]]
    assert None not in nombres_elu + nombres_els
    assert nombres_elu[0] == "U1.1"
    assert nombres_elu[4] == "U3.1"
    assert nombres_els[-1] == "S3.1"

    parametro = reglamento["parameters"]["L_factor"]
    eleccion = crear_eleccion(parametro, numero_opcion_default(parametro))
    resuelto = resolver_parametros(reglamento, [eleccion])
    assert [c["name"] for c in resuelto["combinations"]["ELU"]] == nombres_elu


@pytest.mark.integration
def test_cirsoc2005_actualizado_resuelve_l_reducido_en_u3_a_u5():
    """
    Con la opción reducida (0.5), el factor de L debe cambiar solo en
    las combinaciones ELU que la excepción del reglamento habilita
    (ids 5, 7, 9, 11, 12, 13 y 15); el resto queda intacto, incluido
    todo el ELS.
    """
    reglamento = leer_reglamento(str(RUTA_CIRSOC2005_ACTUALIZADO))
    parametro = reglamento["parameters"]["L_factor"]
    eleccion_reducida = crear_eleccion(parametro, 2)
    assert eleccion_reducida.valor == 0.5

    resuelto = resolver_parametros(reglamento, [eleccion_reducida])
    original = leer_reglamento(str(RUTA_CIRSOC2005))

    ids_con_l_reducido = {5, 7, 9, 11, 12, 13, 15}
    for combinacion, combinacion_original in zip(
        resuelto["combinations"]["ELU"], original["combinations"]["ELU"]
    ):
        if combinacion["id"] in ids_con_l_reducido:
            assert combinacion["factors"]["L"] == 0.5
        else:
            assert combinacion["factors"] == combinacion_original["factors"]

    assert _ids_y_factores(resuelto["combinations"])["ELS"] == (
        _ids_y_factores(original["combinations"])["ELS"]
    )
