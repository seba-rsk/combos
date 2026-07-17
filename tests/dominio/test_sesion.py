from __future__ import annotations

import pytest

from dominio.modelos import EleccionParametro
from dominio.parametros import resolver_parametros
from dominio.sesion import (
    Sesion,
    aplicar_descartes,
    combinaciones_resultantes,
    combinaciones_superadas,
    procesar,
)


@pytest.fixture
def sesion_lista_para_procesar(
    reglamento_minimo, hacer_estado_simple
) -> Sesion:
    """
    Sesión con el reglamento mínimo y estados D y L: produce cuatro
    combinaciones (tres de ELU, una de ELS), de las cuales 1.2D queda
    superada por 1.4D (regla de combinaciones de un solo tipo de carga).
    """
    return Sesion(
        reglamento=reglamento_minimo,
        nombre_perfil="reglamento.yaml",
        estados=[
            hacer_estado_simple("DEAD", "D"),
            hacer_estado_simple("SC", "L"),
        ],
    )


# ── procesar ──────────────────────────────────────────────────────────────────

def test_procesar_genera_y_marca_las_combinaciones(
    sesion_lista_para_procesar,
):
    sesion = sesion_lista_para_procesar

    procesar(sesion)

    assert len(sesion.combinaciones) == 4
    superadas = combinaciones_superadas(sesion)
    assert len(superadas) == 1
    assert superadas[0].componentes[0].factor == 1.2


def test_procesar_sin_reglamento_lanza_value_error():
    with pytest.raises(ValueError, match="reglamento"):
        procesar(Sesion())


def test_procesar_de_nuevo_reemplaza_las_combinaciones(
    sesion_lista_para_procesar,
):
    sesion = sesion_lista_para_procesar
    procesar(sesion)
    primeras = sesion.combinaciones

    procesar(sesion)

    assert len(sesion.combinaciones) == len(primeras)
    assert sesion.combinaciones is not primeras


# ── aplicar_descartes ─────────────────────────────────────────────────────────

def test_aplicar_descartes_marca_solo_los_indices_indicados(
    sesion_lista_para_procesar,
):
    sesion = sesion_lista_para_procesar
    procesar(sesion)
    indice_superada = combinaciones_superadas(sesion)[0].indice_generacion

    aplicar_descartes(sesion, {indice_superada})

    descartadas = [
        c for c in sesion.combinaciones if c.descartada_por_usuario
    ]
    assert [c.indice_generacion for c in descartadas] == [indice_superada]


def test_aplicar_descartes_de_nuevo_reemplaza_la_decision(
    sesion_lista_para_procesar,
):
    sesion = sesion_lista_para_procesar
    procesar(sesion)
    indice_superada = combinaciones_superadas(sesion)[0].indice_generacion
    aplicar_descartes(sesion, {indice_superada})

    aplicar_descartes(sesion, set())

    assert not any(c.descartada_por_usuario for c in sesion.combinaciones)


def test_aplicar_descartes_no_toca_combinaciones_no_superadas(
    sesion_lista_para_procesar,
):
    sesion = sesion_lista_para_procesar
    procesar(sesion)
    indices_no_superadas = {
        c.indice_generacion
        for c in sesion.combinaciones
        if not c.esta_superada
    }

    aplicar_descartes(sesion, indices_no_superadas)

    assert not any(c.descartada_por_usuario for c in sesion.combinaciones)


# ── combinaciones_resultantes ─────────────────────────────────────────────────

def test_resultantes_excluye_descartadas_pero_no_superadas_mantenidas(
    sesion_lista_para_procesar,
):
    sesion = sesion_lista_para_procesar
    procesar(sesion)
    indice_superada = combinaciones_superadas(sesion)[0].indice_generacion

    assert len(combinaciones_resultantes(sesion)) == 4

    aplicar_descartes(sesion, {indice_superada})
    assert len(combinaciones_resultantes(sesion)) == 3


def test_resultantes_excluye_duplicadas(
    reglamento_minimo, hacer_estado_simple
):
    sesion = Sesion(
        reglamento=reglamento_minimo,
        estados=[
            hacer_estado_simple("DEAD", "D"),
            hacer_estado_simple("CP", "D"),
        ],
    )
    procesar(sesion)

    duplicadas = [c for c in sesion.combinaciones if c.es_duplicada]
    assert duplicadas
    resultantes = combinaciones_resultantes(sesion)
    assert not any(c.es_duplicada for c in resultantes)


def test_sesion_vacia_no_tiene_resultantes_ni_superadas():
    sesion = Sesion()

    assert combinaciones_resultantes(sesion) == []
    assert combinaciones_superadas(sesion) == []


# ── reglamento_crudo vs. reglamento ───────────────────────────────────────────

def test_reglamento_crudo_se_preserva_al_resolver_parametros():
    """
    Al resolver los parámetros de un reglamento con parámetros, el
    reglamento crudo de la sesión debe quedar intacto (con la referencia
    `{param: X}` original) para que `.combos` pueda reabrirse y
    regenerar las combinaciones desde el mismo punto de partida aunque
    cambien las elecciones.
    """
    crudo = {
        "parameters": {
            "K": {
                "name": "Factor K",
                "options": [
                    {"label": "opción 1", "value": 1.0, "default": True},
                    {"label": "opción 2", "value": 0.5},
                ],
            }
        },
        "combinations": {
            "ELU": [
                {
                    "id": 1,
                    "name": "U1",
                    "factors": {"D": 1.2, "L": {"param": "K"}},
                }
            ]
        },
    }
    eleccion = EleccionParametro(
        id_parametro="K", nombre="Factor K",
        valor=0.5, etiqueta="opción 2",
    )

    sesion = Sesion(reglamento_crudo=crudo)
    sesion.reglamento = resolver_parametros(sesion.reglamento_crudo, [eleccion])

    factor_crudo = sesion.reglamento_crudo["combinations"]["ELU"][0]["factors"]
    factor_resuelto = sesion.reglamento["combinations"]["ELU"][0]["factors"]
    assert factor_crudo["L"] == {"param": "K"}
    assert factor_resuelto["L"] == 0.5


# ── Límite de combinaciones ───────────────────────────────────────────────────

def test_procesar_rechaza_entradas_desmedidas(
    sesion_lista_para_procesar, monkeypatch
):
    """
    El tope corta antes de generar: una entrada cuyo producto cartesiano
    excede el límite no debe llegar a construir ninguna combinación.
    """
    import dominio.sesion as modulo_sesion
    monkeypatch.setattr(modulo_sesion, "LIMITE_COMBINACIONES", 3)

    with pytest.raises(
        modulo_sesion.ErrorLimiteCombinaciones, match="máximo"
    ) as info:
        procesar(sesion_lista_para_procesar)

    assert info.value.cantidad == 4
    assert sesion_lista_para_procesar.combinaciones == []
