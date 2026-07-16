"""
Estado de una corrida de COMBOS y operaciones del pipeline sobre él.

La `Sesion` concentra los insumos y decisiones del usuario (reglamento
resuelto, perfil, elecciones de parámetros, estados de carga) y las
combinaciones derivadas de procesarlos. Es la fuente única de estado
que comparte la CLI hoy y que van a consumir el formato `.combos` y la
GUI: cualquier interfaz completa una sesión y llama a estas funciones,
sin conocer el orden interno del pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dominio.duplicados import marcar_duplicadas
from dominio.generador import generar_combinaciones
from dominio.modelos import (
    Combinacion,
    EleccionParametro,
    Estado,
    EstadoCrudo,
)
from dominio.preponderancia import marcar_superadas


@dataclass
class Sesion:
    """
    Estado completo de una corrida. Los campos se completan en el orden
    del flujo: reglamento y perfil al cargar, elecciones al resolver los
    parámetros, estados al leer y validar la planilla, y combinaciones
    al procesar.

    El reglamento se guarda en dos formas: `reglamento_crudo` es el YAML
    original tal como se cargó (con las referencias `{param: X}` en los
    factores que dependen de un parámetro) y `reglamento` es el resuelto
    (con los factores ya numéricos). Todo el pipeline consume el
    resuelto; el crudo se conserva para poder regenerar el resuelto ante
    un cambio de elecciones y para poder persistir la sesión con
    trazabilidad completa hacia adelante (formato `.combos`).
    """

    reglamento_crudo: dict | None = None
    reglamento: dict | None = None
    nombre_perfil: str | None = None
    elecciones: list[EleccionParametro] = field(default_factory=list)
    estados_crudos: list[EstadoCrudo] = field(default_factory=list)
    estados: list[Estado] = field(default_factory=list)
    combinaciones: list[Combinacion] = field(default_factory=list)


def procesar(sesion: Sesion) -> None:
    """
    Ejecuta el pipeline de procesamiento sobre la sesión: genera las
    combinaciones a partir de los estados y el reglamento, marca las
    duplicadas y marca las superadas por preponderancia. Deja el
    resultado en sesion.combinaciones.

    Raises:
        ValueError: Si la sesión no tiene reglamento cargado.
    """
    if sesion.reglamento is None:
        raise ValueError(
            "La sesión no tiene reglamento cargado; no se puede procesar."
        )
    combinaciones = generar_combinaciones(sesion.estados, sesion.reglamento)
    combinaciones = marcar_duplicadas(combinaciones)
    combinaciones = marcar_superadas(
        combinaciones, sesion.reglamento["permanent_load_types"]
    )
    sesion.combinaciones = combinaciones


def aplicar_descartes(
    sesion: Sesion, indices_a_descartar: set[int]
) -> None:
    """
    Aplica la decisión del usuario sobre las combinaciones superadas:
    queda descartada toda superada cuyo índice de generación esté en el
    conjunto, y mantenida el resto. Aplicarla de nuevo con otro conjunto
    reemplaza la decisión anterior.
    """
    for combinacion in combinaciones_superadas(sesion):
        combinacion.descartada_por_usuario = (
            combinacion.indice_generacion in indices_a_descartar
        )


def combinaciones_resultantes(sesion: Sesion) -> list[Combinacion]:
    """
    Las combinaciones que integran el resultado final: ni duplicadas ni
    descartadas por el usuario. Es lo que se muestra en el resumen y lo
    que se exporta.
    """
    return [
        c for c in sesion.combinaciones
        if not c.es_duplicada and not c.descartada_por_usuario
    ]


def combinaciones_superadas(sesion: Sesion) -> list[Combinacion]:
    """Las combinaciones marcadas como superadas por preponderancia."""
    return [c for c in sesion.combinaciones if c.esta_superada]
