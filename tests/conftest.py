from __future__ import annotations

import pytest

from dominio.modelos import Combinacion, Componente, Estado


@pytest.fixture
def reglamento_minimo() -> dict:
    """
    Reglamento sintético mínimo, con la misma forma que produce
    dominio.lector_yaml.leer_reglamento, para tests de dominio que no
    necesitan la complejidad completa de un reglamento real como CIRSOC.
    """
    return {
        "metadata": {
            "code_name": "TEST",
            "code_version": "1",
            "country": "Testland",
            "description": "Reglamento de prueba",
        },
        "limit_states": {
            "ELU": {"name": "Estado límite último", "prefix": "U"},
            "ELS": {"name": "Estado límite de servicio", "prefix": "S"},
        },
        "load_types": {
            "D": {"name": "Permanente", "description": "Carga permanente"},
            "L": {"name": "Viva", "description": "Sobrecarga de uso"},
            "W": {"name": "Viento", "description": "Carga de viento"},
        },
        "combinations": {
            "ELU": [
                {"id": 1, "factors": {"D": 1.4}},
                {"id": 2, "factors": {"D": 1.2, "L": 1.6}},
                {"id": 3, "factors": {"D": 1.2, "W": 1.6}},
            ],
            "ELS": [
                {"id": 1, "factors": {"D": 1.0, "L": 1.0}},
            ],
        },
        "permanent_load_types": ["D"],
    }


@pytest.fixture
def hacer_estado_simple():
    """Fábrica de estados enriquecidos simples (ver lector_plantilla)."""

    def construir(
        nombre_estado: str, tipo_carga: str, signo: int = 1
    ) -> Estado:
        return Estado(
            nombre_estado=nombre_estado,
            tipo_carga=tipo_carga,
            tipo_estado="simple",
            nombre_grupo=None,
            signo=signo,
        )

    return construir


@pytest.fixture
def hacer_estado_direccional():
    """Fábrica de estados enriquecidos direccionales."""

    def construir(
        nombre_estado: str, tipo_carga: str, nombre_grupo: str, signo: int
    ) -> Estado:
        return Estado(
            nombre_estado=nombre_estado,
            tipo_carga=tipo_carga,
            tipo_estado="direccional",
            nombre_grupo=nombre_grupo,
            signo=signo,
        )

    return construir


@pytest.fixture
def hacer_componente():
    """Fábrica de componentes de combinación (ver dominio.generador)."""

    def construir(
        nombre_estado: str,
        tipo_carga: str,
        factor: float,
        signo: int = 1,
    ) -> Componente:
        return Componente(
            nombre_estado=nombre_estado,
            tipo_carga=tipo_carga,
            factor=factor,
            signo=signo,
        )

    return construir


@pytest.fixture
def hacer_combinacion():
    """Fábrica de combinaciones (ver dominio.modelos.Combinacion)."""

    def construir(
        indice_generacion: int,
        estado_limite: str,
        componentes: list[Componente],
        combinacion_base_id: int = 1,
        nombre: str | None = None,
    ) -> Combinacion:
        return Combinacion(
            indice_generacion=indice_generacion,
            estado_limite=estado_limite,
            combinacion_base_id=combinacion_base_id,
            componentes=componentes,
            nombre=nombre,
        )

    return construir
