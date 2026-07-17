from __future__ import annotations

import pytest

from combos.dominio.lector_plantilla import (
    ErrorValidacionPlantilla,
    leer_plantilla,
)
from combos.dominio.modelos import EstadoCrudo


def _estado_crudo_simple(nombre: str, tipo_carga: str) -> EstadoCrudo:
    return EstadoCrudo(
        nombre_estado=nombre,
        tipo_carga=tipo_carga,
        tipo_estado="simple",
        grupo=None,
        incluir_opuesto=False,
    )


def _estado_crudo_direccional(
    nombre: str, tipo_carga: str, grupo: int, incluir_opuesto: bool
) -> EstadoCrudo:
    return EstadoCrudo(
        nombre_estado=nombre,
        tipo_carga=tipo_carga,
        tipo_estado="direccional",
        grupo=grupo,
        incluir_opuesto=incluir_opuesto,
    )


def test_leer_plantilla_estado_simple_no_genera_variantes(reglamento_minimo):
    estados = [_estado_crudo_simple("DEAD", "D")]

    resultado = leer_plantilla(estados, reglamento_minimo)

    assert len(resultado) == 1
    assert resultado[0].signo == 1
    assert resultado[0].nombre_grupo is None


def test_leer_plantilla_direccional_con_opuesto_genera_dos_variantes(
    reglamento_minimo,
):
    estados = [
        _estado_crudo_direccional("Wx", "W", grupo=1, incluir_opuesto=True),
        _estado_crudo_direccional("Wy", "W", grupo=1, incluir_opuesto=False),
    ]

    resultado = leer_plantilla(estados, reglamento_minimo)

    # Wx genera 2 variantes (+1 y -1), Wy genera solo 1 (sin opuesto).
    assert len(resultado) == 3
    signos_wx = sorted(
        v.signo for v in resultado if v.nombre_estado == "Wx"
    )
    assert signos_wx == [-1, 1]
    assert all(v.nombre_grupo == "W-1" for v in resultado)


def test_leer_plantilla_direccional_sin_opuesto_genera_una_sola_variante(
    reglamento_minimo,
):
    # El grupo necesita al menos dos estados para pasar la validación;
    # ninguno de los dos activa "incluir opuesto".
    estados = [
        _estado_crudo_direccional("Wx", "W", grupo=1, incluir_opuesto=False),
        _estado_crudo_direccional("Wy", "W", grupo=1, incluir_opuesto=False),
    ]

    resultado = leer_plantilla(estados, reglamento_minimo)

    assert len(resultado) == 2
    assert all(v.signo == 1 for v in resultado)


def test_leer_plantilla_tipo_de_carga_desconocido_lanza_error(
    reglamento_minimo,
):
    estados = [_estado_crudo_simple("VIENTO", "Z")]

    with pytest.raises(ErrorValidacionPlantilla) as exc_info:
        leer_plantilla(estados, reglamento_minimo)

    assert any("Z" in error for error in exc_info.value.errores)


def test_leer_plantilla_grupo_direccional_con_un_solo_estado_lanza_error(
    reglamento_minimo,
):
    estados = [
        _estado_crudo_direccional("Wx", "W", grupo=1, incluir_opuesto=False),
    ]
    # Forzamos que el grupo quede con un solo estado enriquecido eliminando
    # la posibilidad de que genere su propio opuesto: ya cubierto arriba,
    # así que agregamos un segundo estado de un grupo distinto para
    # asegurar que el chequeo es por grupo y no global.
    estados_con_grupo_incompleto = estados + [
        _estado_crudo_direccional("Ey", "E", grupo=2, incluir_opuesto=False)
    ]
    reglamento_con_e = dict(reglamento_minimo)
    reglamento_con_e["load_types"] = {
        **reglamento_minimo["load_types"],
        "E": {"name": "Sismo", "description": "Carga sísmica"},
    }

    with pytest.raises(ErrorValidacionPlantilla) as exc_info:
        leer_plantilla(estados_con_grupo_incompleto, reglamento_con_e)

    assert any("W-1" in error for error in exc_info.value.errores)
    assert any("E-2" in error for error in exc_info.value.errores)


def test_leer_plantilla_nombres_duplicados_lanza_error(reglamento_minimo):
    estados = [
        _estado_crudo_simple("DEAD", "D"),
        _estado_crudo_simple("dead", "D"),
    ]

    with pytest.raises(ErrorValidacionPlantilla) as exc_info:
        leer_plantilla(estados, reglamento_minimo)

    assert any("duplicado" in error for error in exc_info.value.errores)
