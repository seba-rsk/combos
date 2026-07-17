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

from combos.dominio.duplicados import marcar_duplicadas
from combos.dominio.generador import (
    contar_combinaciones_previstas,
    generar_combinaciones,
)
from combos.dominio.modelos import (
    Combinacion,
    EleccionParametro,
    Estado,
    EstadoCrudo,
)
from combos.dominio.preponderancia import marcar_superadas

# Tope de combinaciones que una corrida puede generar. Las variantes de
# los grupos direccionales se multiplican entre sí, así que una entrada
# desmedida (una planilla propia o un archivo .combos de terceros) puede
# crecer a millones y colgar la máquina. El uso real está en el orden de
# los cientos; el límite deja margen de sobra.
LIMITE_COMBINACIONES = 10_000


class ErrorLimiteCombinaciones(Exception):
    """La entrada genera más combinaciones de las que COMBOS procesa."""

    def __init__(self, cantidad: int) -> None:
        self.cantidad = cantidad
        super().__init__(
            f"La entrada genera {_formato_miles(cantidad)} combinaciones "
            f"y el máximo que COMBOS procesa es "
            f"{_formato_miles(LIMITE_COMBINACIONES)}. Revisá la cantidad "
            f"de estados direccionales y de grupos: las variantes se "
            f"multiplican entre sí."
        )


def _formato_miles(numero: int) -> str:
    return f"{numero:,}".replace(",", ".")


@dataclass
class Sesion:
    """
    Estado completo de una corrida. Los campos se completan en el orden
    del flujo: reglamento y perfil al cargar, elecciones al resolver los
    parámetros, estados al leer y validar la planilla, y combinaciones
    al procesar.

    El reglamento se guarda en tres formas: `reglamento_texto` es el
    texto YAML original tal como se leyó del archivo (el formato
    `.combos` lo embebe íntegro), `reglamento_crudo` es su contenido
    validado (con las referencias `{param: X}` en los factores que
    dependen de un parámetro) y `reglamento` es el resuelto (con los
    factores ya numéricos). Todo el pipeline consume el resuelto; el
    crudo se conserva para poder regenerar el resuelto ante un cambio
    de elecciones y para poder persistir la sesión con trazabilidad
    completa hacia adelante (formato `.combos`).
    """

    reglamento_texto: str | None = None
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
        ErrorLimiteCombinaciones: Si la entrada generaría más
            combinaciones que LIMITE_COMBINACIONES (el chequeo corre
            antes de generar nada, así una entrada desmedida no llega
            a consumir memoria ni tiempo).
    """
    if sesion.reglamento is None:
        raise ValueError(
            "La sesión no tiene reglamento cargado; no se puede procesar."
        )
    cantidad_prevista = contar_combinaciones_previstas(
        sesion.estados, sesion.reglamento
    )
    if cantidad_prevista > LIMITE_COMBINACIONES:
        raise ErrorLimiteCombinaciones(cantidad_prevista)
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
