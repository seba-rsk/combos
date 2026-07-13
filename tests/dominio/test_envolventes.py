from __future__ import annotations

from dominio.envolventes import construir_envolventes


def test_construir_envolventes_agrupa_por_estado_limite(
    reglamento_minimo, hacer_combinacion
):
    combinaciones_validas = [
        hacer_combinacion(1, "ELU", [], nombre="U1"),
        hacer_combinacion(2, "ELU", [], nombre="U2"),
        hacer_combinacion(3, "ELS", [], nombre="S1"),
    ]

    envolventes = construir_envolventes(
        combinaciones_validas, reglamento_minimo, "ENV"
    )

    nombres_envolvente = {e.nombre_envolvente for e in envolventes}
    assert nombres_envolvente == {"ENVU", "ENVS"}
    assert sum(1 for e in envolventes if e.nombre_envolvente == "ENVU") == 2
    assert sum(1 for e in envolventes if e.nombre_envolvente == "ENVS") == 1
    assert all(e.factor == 1 for e in envolventes)


def test_construir_envolventes_usa_prefijo_personalizado(
    reglamento_minimo, hacer_combinacion
):
    combinaciones_validas = [hacer_combinacion(1, "ELU", [], nombre="U1")]

    envolventes = construir_envolventes(
        combinaciones_validas, reglamento_minimo, "ENVOLVENTE_"
    )

    assert envolventes[0].nombre_envolvente == "ENVOLVENTE_U"


def test_construir_envolventes_estado_limite_sin_prefijo_usa_su_propio_id(
    hacer_combinacion,
):
    reglamento_sin_prefijo = {"limit_states": {}}
    combinaciones_validas = [hacer_combinacion(1, "X", [], nombre="X1")]

    envolventes = construir_envolventes(
        combinaciones_validas, reglamento_sin_prefijo, "ENV"
    )

    assert envolventes[0].nombre_envolvente == "ENVX"


def test_construir_envolventes_lista_vacia_devuelve_lista_vacia(
    reglamento_minimo,
):
    assert construir_envolventes([], reglamento_minimo, "ENV") == []
