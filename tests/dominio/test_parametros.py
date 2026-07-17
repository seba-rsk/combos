from __future__ import annotations

import pytest

from combos.dominio.modelos import (
    EleccionParametro,
    OpcionParametro,
    ParametroReglamento,
)
from combos.dominio.parametros import (
    combinaciones_que_referencian,
    crear_eleccion,
    numero_opcion_default,
    parametros_que_aplican,
    resolver_parametros,
    tipos_de_carga_que_referencian,
)


@pytest.fixture
def parametro_l_factor() -> ParametroReglamento:
    return ParametroReglamento(
        id_parametro="L_factor",
        nombre="Factor de sobrecarga L",
        opciones=[
            OpcionParametro(etiqueta="Sobrecarga alta", valor=1.0),
            OpcionParametro(etiqueta="Resto de los destinos", valor=0.5),
        ],
        valor_default=0.5,
    )


@pytest.fixture
def reglamento_con_parametro(
    reglamento_minimo, parametro_l_factor
) -> dict:
    reglamento_minimo["parameters"] = {"L_factor": parametro_l_factor}
    reglamento_minimo["combinations"]["ELU"].append(
        {
            "id": 4,
            "name": "U9.9",
            "factors": {"D": 1.2, "L": {"param": "L_factor"}},
        }
    )
    return reglamento_minimo


# ── resolver_parametros ───────────────────────────────────────────────────────

def test_resolver_reemplaza_referencias_por_el_valor_elegido(
    reglamento_con_parametro,
):
    eleccion = EleccionParametro(
        id_parametro="L_factor",
        nombre="Factor de sobrecarga L",
        valor=0.5,
        etiqueta="Resto de los destinos",
    )

    resuelto = resolver_parametros(reglamento_con_parametro, [eleccion])

    factores = resuelto["combinations"]["ELU"][3]["factors"]
    assert factores == {"D": 1.2, "L": 0.5}


def test_resolver_no_modifica_el_reglamento_original(
    reglamento_con_parametro,
):
    eleccion = EleccionParametro(
        id_parametro="L_factor",
        nombre="Factor de sobrecarga L",
        valor=1.0,
        etiqueta="Sobrecarga alta",
    )

    resolver_parametros(reglamento_con_parametro, [eleccion])

    factores_originales = (
        reglamento_con_parametro["combinations"]["ELU"][3]["factors"]
    )
    assert factores_originales["L"] == {"param": "L_factor"}


def test_resolver_sin_parametros_devuelve_combinaciones_equivalentes(
    reglamento_minimo,
):
    resuelto = resolver_parametros(reglamento_minimo, [])

    assert resuelto["combinations"] == reglamento_minimo["combinations"]


def test_resolver_con_eleccion_faltante_lanza_value_error(
    reglamento_con_parametro,
):
    with pytest.raises(ValueError, match="L_factor"):
        resolver_parametros(reglamento_con_parametro, [])


# ── crear_eleccion ────────────────────────────────────────────────────────────

def test_crear_eleccion_devuelve_valor_y_etiqueta_de_la_opcion(
    parametro_l_factor,
):
    eleccion = crear_eleccion(parametro_l_factor, 2)

    assert eleccion.id_parametro == "L_factor"
    assert eleccion.nombre == "Factor de sobrecarga L"
    assert eleccion.valor == 0.5
    assert eleccion.etiqueta == "Resto de los destinos"


def test_crear_eleccion_fuera_de_rango_lanza_value_error(
    parametro_l_factor,
):
    with pytest.raises(ValueError, match="opción 3"):
        crear_eleccion(parametro_l_factor, 3)


# ── numero_opcion_default ─────────────────────────────────────────────────────

def test_numero_opcion_default_encuentra_la_opcion_del_default(
    parametro_l_factor,
):
    assert numero_opcion_default(parametro_l_factor) == 2


def test_resolver_preserva_los_nombres_de_las_combinaciones(
    reglamento_con_parametro,
):
    eleccion = EleccionParametro(
        id_parametro="L_factor",
        nombre="Factor de sobrecarga L",
        valor=0.5,
        etiqueta="Resto de los destinos",
    )

    resuelto = resolver_parametros(reglamento_con_parametro, [eleccion])

    assert resuelto["combinations"]["ELU"][3]["name"] == "U9.9"
    assert resuelto["combinations"]["ELU"][0]["name"] is None


# ── parametros_que_aplican ────────────────────────────────────────────────────

def test_parametro_aplica_si_hay_estados_del_tipo_referenciado(
    reglamento_con_parametro, parametro_l_factor
):
    aplican, no_aplican = parametros_que_aplican(
        reglamento_con_parametro, {"D", "L"}
    )

    assert aplican == [parametro_l_factor]
    assert no_aplican == []


def test_parametro_no_aplica_sin_estados_del_tipo_referenciado(
    reglamento_con_parametro, parametro_l_factor
):
    aplican, no_aplican = parametros_que_aplican(
        reglamento_con_parametro, {"D", "W"}
    )

    assert aplican == []
    assert no_aplican == [parametro_l_factor]


def test_parametros_que_aplican_sin_parametros_devuelve_vacio(
    reglamento_minimo,
):
    assert parametros_que_aplican(reglamento_minimo, {"D"}) == ([], [])


# ── combinaciones_que_referencian ─────────────────────────────────────────────

def test_combinaciones_afectadas_usa_el_nombre_normativo(
    reglamento_con_parametro,
):
    afectadas = combinaciones_que_referencian(
        reglamento_con_parametro, "L_factor"
    )

    assert afectadas == {"ELU": ["U9.9"]}


def test_combinaciones_afectadas_sin_nombre_usa_el_id(
    reglamento_con_parametro,
):
    reglamento_con_parametro["combinations"]["ELS"].append(
        {"id": 2, "factors": {"D": 1.0, "L": {"param": "L_factor"}}}
    )

    afectadas = combinaciones_que_referencian(
        reglamento_con_parametro, "L_factor"
    )

    assert afectadas == {"ELU": ["U9.9"], "ELS": [2]}


def test_combinaciones_afectadas_sin_referencias_devuelve_vacio(
    reglamento_minimo,
):
    afectadas = combinaciones_que_referencian(reglamento_minimo, "L_factor")

    assert afectadas == {}


# ── tipos_de_carga_que_referencian ────────────────────────────────────────────

def test_tipos_que_referencian_devuelve_los_tipos_sin_repetir(
    reglamento_con_parametro,
):
    reglamento_con_parametro["combinations"]["ELS"].append(
        {"id": 2, "factors": {"D": 1.0, "L": {"param": "L_factor"}}}
    )

    tipos = tipos_de_carga_que_referencian(
        reglamento_con_parametro, "L_factor"
    )

    assert tipos == ["L"]


def test_tipos_que_referencian_sin_referencias_devuelve_lista_vacia(
    reglamento_minimo,
):
    tipos = tipos_de_carga_que_referencian(reglamento_minimo, "L_factor")

    assert tipos == []
