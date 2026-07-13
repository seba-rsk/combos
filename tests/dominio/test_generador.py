from __future__ import annotations

from dominio.generador import generar_combinaciones


def test_generar_combinaciones_con_todos_los_tipos_presentes_genera_completa(
    reglamento_minimo, hacer_estado_simple
):
    estados = [
        hacer_estado_simple("DEAD", "D"),
        hacer_estado_simple("SC", "L"),
    ]

    combinaciones = generar_combinaciones(estados, reglamento_minimo)

    combo_dl = next(
        c for c in combinaciones
        if c.estado_limite == "ELU" and c.combinacion_base_id == 2
    )
    nombres = {c.nombre_estado for c in combo_dl.componentes}
    assert nombres == {"DEAD", "SC"}


def test_generar_combinaciones_tipo_de_carga_ausente_genera_incompleta(
    reglamento_minimo, hacer_estado_simple
):
    """
    Documenta el comportamiento conocido (ver KNOWN_ISSUES.md): si falta
    un tipo de carga de una combinación multi-término, la combinación se
    genera igual con los términos que sí tienen estados, en vez de
    omitirse por completo.
    """
    estados = [hacer_estado_simple("DEAD", "D")]

    combinaciones = generar_combinaciones(estados, reglamento_minimo)

    combo_dl = next(
        c for c in combinaciones
        if c.estado_limite == "ELU" and c.combinacion_base_id == 2
    )
    assert len(combo_dl.componentes) == 1
    assert combo_dl.componentes[0].nombre_estado == "DEAD"


def test_generar_combinaciones_sin_ningun_estado_del_tipo_requerido_se_omite(
    reglamento_minimo, hacer_estado_simple
):
    # Ningún estado es de tipo W, así que la combinación base 3 (D+W)
    # no debe generarse en absoluto.
    estados = [hacer_estado_simple("SC", "L")]

    combinaciones = generar_combinaciones(estados, reglamento_minimo)

    bases_generadas = {
        c.combinacion_base_id for c in combinaciones
        if c.estado_limite == "ELU"
    }
    assert 3 not in bases_generadas


def test_generar_combinaciones_grupo_direccional_expande_producto_cartesiano(
    reglamento_minimo, hacer_estado_simple, hacer_estado_direccional
):
    estados = [
        hacer_estado_simple("DEAD", "D"),
        hacer_estado_direccional("Wx", "W", "W-1", signo=1),
        hacer_estado_direccional("Wx_neg", "W", "W-1", signo=-1),
        hacer_estado_direccional("Wy", "W", "W-1", signo=1),
        hacer_estado_direccional("Wy_neg", "W", "W-1", signo=-1),
    ]

    combinaciones = generar_combinaciones(estados, reglamento_minimo)

    combos_dw = [
        c for c in combinaciones
        if c.estado_limite == "ELU" and c.combinacion_base_id == 3
    ]
    # 4 variantes direccionales (Wx, -Wx, Wy, -Wy) → 4 combinaciones,
    # cada una con el componente D + una variante de W.
    assert len(combos_dw) == 4
    for combo in combos_dw:
        assert len(combo.componentes) == 2


def test_generar_combinaciones_dos_grupos_direccionales_genera_producto_cruzado(
    reglamento_minimo, hacer_estado_simple, hacer_estado_direccional
):
    reglamento_dos_grupos = dict(reglamento_minimo)
    reglamento_dos_grupos["load_types"] = {
        **reglamento_minimo["load_types"],
        "E": {"name": "Sismo", "description": "Carga sísmica"},
    }
    reglamento_dos_grupos["combinations"] = {
        "ELU": [{"id": 1, "factors": {"D": 1.2, "W": 1.0, "E": 1.0}}],
        "ELS": [],
    }
    estados = [
        hacer_estado_simple("DEAD", "D"),
        hacer_estado_direccional("Wx", "W", "W-1", signo=1),
        hacer_estado_direccional("Wy", "W", "W-1", signo=1),
        hacer_estado_direccional("Ex", "E", "E-1", signo=1),
        hacer_estado_direccional("Ey", "E", "E-1", signo=1),
    ]

    combinaciones = generar_combinaciones(estados, reglamento_dos_grupos)

    # Producto cartesiano de 2 variantes de W x 2 variantes de E = 4.
    assert len(combinaciones) == 4


def test_generar_combinaciones_sin_estados_devuelve_lista_vacia(
    reglamento_minimo,
):
    combinaciones = generar_combinaciones([], reglamento_minimo)

    assert combinaciones == []
