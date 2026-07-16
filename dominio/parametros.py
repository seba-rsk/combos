"""
Resolución de los parámetros del reglamento.

Un reglamento puede definir parámetros (sección `parameters` del YAML):
propiedades del proyecto que el usuario elige una sola vez y que
determinan el valor de los factores que las referencian con
`{ param: <id> }`. Este módulo convierte esas referencias en números
concretos antes de que el resto del pipeline (generación, duplicados,
preponderancia, exportación) vea el reglamento: para todos ellos los
factores son siempre numéricos.
"""

from __future__ import annotations

from dominio.lector_yaml import CLAVE_REFERENCIA_PARAMETRO
from dominio.modelos import EleccionParametro, ParametroReglamento


def resolver_parametros(
    reglamento: dict, elecciones: list[EleccionParametro]
) -> dict:
    """
    Devuelve una copia del reglamento con cada referencia `{ param: X }`
    reemplazada por el valor elegido para ese parámetro. No modifica el
    reglamento recibido.

    Args:
        reglamento: Reglamento ya validado (ver
            dominio.lector_yaml.leer_reglamento).
        elecciones: Una elección por cada parámetro definido en el
            reglamento (ver crear_eleccion).

    Raises:
        ValueError: Si falta la elección de algún parámetro definido.
    """
    valores = {e.id_parametro: e.valor for e in elecciones}
    faltantes = set(reglamento.get("parameters", {})) - set(valores)
    if faltantes:
        raise ValueError(
            f"Faltan las elecciones de los parámetros: {sorted(faltantes)}."
        )
    resuelto = dict(reglamento)
    resuelto["combinations"] = {
        id_estado: [
            {
                "id": combinacion["id"],
                "name": combinacion.get("name"),
                "factors": _resolver_factores(
                    combinacion["factors"], valores
                ),
            }
            for combinacion in lista_combinaciones
        ]
        for id_estado, lista_combinaciones in reglamento[
            "combinations"
        ].items()
    }
    return resuelto


def crear_eleccion(
    parametro: ParametroReglamento, numero_opcion: int
) -> EleccionParametro:
    """
    Construye la elección del usuario a partir del número de opción tal
    como se muestra en pantalla (empezando en 1).

    Raises:
        ValueError: Si el número está fuera del rango de opciones.
    """
    if not 1 <= numero_opcion <= len(parametro.opciones):
        raise ValueError(
            f"El parámetro '{parametro.id_parametro}' no tiene una "
            f"opción {numero_opcion} (tiene {len(parametro.opciones)})."
        )
    opcion = parametro.opciones[numero_opcion - 1]
    return EleccionParametro(
        id_parametro=parametro.id_parametro,
        nombre=parametro.nombre,
        valor=opcion.valor,
        etiqueta=opcion.etiqueta,
    )


def numero_opcion_default(parametro: ParametroReglamento) -> int:
    """
    Devuelve el número (empezando en 1) de la primera opción cuyo valor
    coincide con el default del parámetro, para ofrecerla con Enter.
    """
    for numero, opcion in enumerate(parametro.opciones, start=1):
        if opcion.valor == parametro.valor_default:
            return numero
    raise ValueError(
        f"El parámetro '{parametro.id_parametro}' no tiene ninguna "
        f"opción con su valor default ({parametro.valor_default})."
    )


def tipos_de_carga_que_referencian(
    reglamento: dict, id_parametro: str
) -> list[str]:
    """
    Lista, sin repetir y en orden de aparición, los tipos de carga cuyos
    factores referencian el parámetro indicado. Se usa para mostrar en
    el menú qué factor está eligiendo el usuario (ej. "L × 0.5").
    """
    tipos: list[str] = []
    for lista_combinaciones in reglamento["combinations"].values():
        for combinacion in lista_combinaciones:
            for tipo_carga, factor in combinacion["factors"].items():
                if (
                    isinstance(factor, dict)
                    and factor.get(CLAVE_REFERENCIA_PARAMETRO)
                    == id_parametro
                    and tipo_carga not in tipos
                ):
                    tipos.append(tipo_carga)
    return tipos


def parametros_que_aplican(
    reglamento: dict, tipos_presentes: set[str]
) -> tuple[list[ParametroReglamento], list[ParametroReglamento]]:
    """
    Separa los parámetros del reglamento entre los que aplican al
    proyecto (algún tipo de carga que los referencia tiene estados
    ingresados) y los que no. El valor de un parámetro que no aplica
    no participa de ninguna combinación generada, así que puede
    resolverse con su default sin preguntar al usuario.

    Args:
        reglamento: Reglamento ya validado.
        tipos_presentes: Tipos de carga de los estados ingresados por
            el usuario.

    Returns:
        Tupla (aplican, no_aplican), cada una en el orden de
        declaración de la sección parameters.
    """
    aplican: list[ParametroReglamento] = []
    no_aplican: list[ParametroReglamento] = []
    for parametro in reglamento.get("parameters", {}).values():
        tipos_referenciados = tipos_de_carga_que_referencian(
            reglamento, parametro.id_parametro
        )
        if tipos_presentes & set(tipos_referenciados):
            aplican.append(parametro)
        else:
            no_aplican.append(parametro)
    return aplican, no_aplican


def combinaciones_que_referencian(
    reglamento: dict, id_parametro: str
) -> dict[str, list[str | int]]:
    """
    Devuelve, por estado límite y en orden de aparición, la designación
    de cada combinación base cuyos factores referencian el parámetro:
    su `name` normativo si lo tiene (ej. "U3.1"), o su id numérico como
    respaldo. Se usa para mostrar "Afecta a: ..." en el menú del
    parámetro. Los estados límite sin combinaciones afectadas no
    aparecen en el resultado.
    """
    afectadas: dict[str, list[str | int]] = {}
    for id_estado, lista_combinaciones in reglamento["combinations"].items():
        designaciones = [
            combinacion.get("name") or combinacion["id"]
            for combinacion in lista_combinaciones
            if _referencia_al_parametro(combinacion, id_parametro)
        ]
        if designaciones:
            afectadas[id_estado] = designaciones
    return afectadas


def _referencia_al_parametro(combinacion: dict, id_parametro: str) -> bool:
    return any(
        isinstance(factor, dict)
        and factor.get(CLAVE_REFERENCIA_PARAMETRO) == id_parametro
        for factor in combinacion["factors"].values()
    )


def _resolver_factores(factores: dict, valores: dict[str, float]) -> dict:
    return {
        tipo_carga: (
            valores[factor[CLAVE_REFERENCIA_PARAMETRO]]
            if isinstance(factor, dict)
            else factor
        )
        for tipo_carga, factor in factores.items()
    }
