"""
Objetos de dominio de COMBOS con forma fija.

Definir aquí todos los objetos que circulan por el pipeline de dominio
(entrada, procesamiento y salida) garantiza que cualquier campo mal
tipeado o inexistente falle en el momento de la construcción, en vez de
propagarse como una clave silenciosa dentro de un dict.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EstadoCrudo:
    """
    Estado de carga tal como fue leído de la planilla del usuario, sin
    enriquecer todavía con las variantes de signo.
    """

    nombre_estado: str
    tipo_carga: str
    tipo_estado: str
    grupo: int | None
    incluir_opuesto: bool


@dataclass
class Estado:
    """
    Estado de carga enriquecido: una fila por cada variante de signo
    (los direccionales con "incluir opuesto" generan dos).
    """

    nombre_estado: str
    tipo_carga: str
    tipo_estado: str
    nombre_grupo: str | None
    signo: int


@dataclass
class Componente:
    """
    Un término dentro de una combinación (ej. "1.4 × DEAD"): el estado
    referenciado, el factor de ponderación y el signo con el que entra.
    """

    nombre_estado: str
    tipo_carga: str
    factor: float
    signo: int


@dataclass
class OpcionParametro:
    """
    Una opción elegible de un parámetro del reglamento: la etiqueta que
    ve el usuario (texto libre del autor del YAML) y el valor numérico
    del factor que esa opción representa.
    """

    etiqueta: str
    valor: float


@dataclass
class ParametroReglamento:
    """
    Un parámetro del reglamento: una propiedad del proyecto (ej. destino
    del edificio) que el usuario define una sola vez y que resuelve el
    valor de los factores que lo referencian con { param: <id> }.
    """

    id_parametro: str
    nombre: str
    opciones: list[OpcionParametro]
    valor_default: float


@dataclass
class EleccionParametro:
    """
    La opción que el usuario eligió para un parámetro del reglamento.
    Viaja hasta la exportación para dejar registrada la elección en el
    encabezado del archivo generado (trazabilidad).
    """

    id_parametro: str
    nombre: str
    valor: float
    etiqueta: str


@dataclass
class Combinacion:
    """
    Una combinación de carga generada por el pipeline. Los campos de
    marcado (duplicada, superada, descartada, nombre) parten en su valor
    inicial y se van completando a lo largo del pipeline.
    """

    indice_generacion: int
    estado_limite: str
    combinacion_base_id: int
    componentes: list[Componente]
    es_duplicada: bool = False
    duplicada_por: int | None = None
    esta_superada: bool = False
    superada_por: int | None = None
    descartada_por_usuario: bool = False
    nombre: str | None = None


@dataclass
class FilaEnvolvente:
    """
    Una fila de la tabla de envolventes que se exporta al final del
    pipeline: qué envolvente contiene qué combinación y con qué factor.
    """

    nombre_envolvente: str
    nombre_combinacion: str
    factor: int = 1
