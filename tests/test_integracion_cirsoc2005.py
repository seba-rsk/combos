from __future__ import annotations

from pathlib import Path

import pytest

from dominio.duplicados import marcar_duplicadas
from dominio.generador import generar_combinaciones
from dominio.lector_plantilla import leer_plantilla
from dominio.lector_yaml import leer_reglamento
from dominio.modelos import EstadoCrudo
from dominio.preponderancia import marcar_superadas

RUTA_CIRSOC2005 = Path(__file__).parent.parent / "profiles" / "cirsoc2005.yaml"


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
