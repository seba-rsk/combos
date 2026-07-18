from __future__ import annotations

from combos.dominio.modelos import Estado, EstadoCrudo

# Tope de estados de carga por corrida. El uso real está en el orden de
# las decenas; el límite corta una entrada desmedida (una planilla
# propia o un archivo .combos de terceros) antes de enriquecerla y
# combinarla. Hallazgo de la auditoría 2026-07-18.
LIMITE_ESTADOS = 500


class ErrorValidacionPlantilla(Exception):
    def __init__(self, errores: list[str]) -> None:
        self.errores = errores
        super().__init__("\n".join(errores))


def leer_plantilla(
    estados: list[EstadoCrudo], reglamento: dict
) -> list[Estado]:
    """
    Valida los estados de carga leídos de la planilla del usuario contra
    el reglamento activo y los enriquece con las variantes de signo que
    se derivan de los estados direccionales.

    Args:
        estados: Estados crudos leídos de la planilla (ver
            infraestructura.lector_excel.leer_excel).
        reglamento: Reglamento ya validado (ver
            dominio.lector_yaml.leer_reglamento).

    Raises:
        ErrorValidacionPlantilla: Si hay más estados que LIMITE_ESTADOS,
            tipos de carga no definidos en el reglamento, grupos
            direccionales con menos de dos estados, o nombres de estado
            duplicados.

    Returns:
        Lista de estados enriquecidos, con una fila por cada variante de
        signo (los estados direccionales con "incluir opuesto" generan
        dos filas).
    """
    if len(estados) > LIMITE_ESTADOS:
        raise ErrorValidacionPlantilla([
            f"La planilla tiene {len(estados)} estados de carga y el "
            f"máximo que COMBOS procesa es {LIMITE_ESTADOS}. Revisá que "
            f"el archivo sea el correcto."
        ])
    estados_enriquecidos = _construir_estados_enriquecidos(estados)
    errores = _recolectar_errores_de_validacion(
        estados, estados_enriquecidos, reglamento
    )
    if errores:
        raise ErrorValidacionPlantilla(errores)
    return estados_enriquecidos


# ── Validación ────────────────────────────────────────────────────────────────

def _recolectar_errores_de_validacion(
    estados_originales: list[EstadoCrudo],
    estados_enriquecidos: list[Estado],
    reglamento: dict,
) -> list[str]:
    errores: list[str] = []
    errores.extend(
        _errores_tipos_de_carga_desconocidos(estados_originales, reglamento)
    )
    errores.extend(
        _errores_grupos_con_menos_de_dos_estados(estados_enriquecidos)
    )
    errores.extend(_errores_nombres_de_estado_duplicados(estados_originales))
    return errores


def _errores_tipos_de_carga_desconocidos(
    estados: list[EstadoCrudo], reglamento: dict
) -> list[str]:
    tipos_definidos = set(reglamento["load_types"].keys())
    tipos_usados = {estado.tipo_carga for estado in estados}
    tipos_desconocidos = tipos_usados - tipos_definidos
    return [
        f"El tipo de carga '{tipo}' no está definido en el reglamento."
        for tipo in sorted(tipos_desconocidos)
    ]


def _errores_grupos_con_menos_de_dos_estados(
    estados_enriquecidos: list[Estado],
) -> list[str]:
    conteo_por_grupo = _contar_estados_enriquecidos_por_grupo(
        estados_enriquecidos
    )
    return [
        f"El grupo '{nombre_grupo}' tiene {cantidad} estado(s). "
        "Se requieren al menos dos."
        for nombre_grupo, cantidad in sorted(conteo_por_grupo.items())
        if cantidad < 2
    ]


def _contar_estados_enriquecidos_por_grupo(
    estados_enriquecidos: list[Estado],
) -> dict[str, int]:
    conteo: dict[str, int] = {}
    for estado in estados_enriquecidos:
        if estado.tipo_estado != "direccional":
            continue
        nombre_grupo = estado.nombre_grupo
        conteo[nombre_grupo] = conteo.get(nombre_grupo, 0) + 1
    return conteo


def _errores_nombres_de_estado_duplicados(
    estados: list[EstadoCrudo],
) -> list[str]:
    nombres_vistos: dict[str, str] = {}
    errores: list[str] = []
    for estado in estados:
        nombre = estado.nombre_estado
        clave_normalizada = nombre.lower()
        if clave_normalizada in nombres_vistos:
            errores.append(
                f"El nombre de estado '{nombre}' está duplicado "
                f"(ya existe como '{nombres_vistos[clave_normalizada]}')."
            )
        else:
            nombres_vistos[clave_normalizada] = nombre
    return errores


# ── Construcción ──────────────────────────────────────────────────────────────

def _construir_estados_enriquecidos(
    estados: list[EstadoCrudo],
) -> list[Estado]:
    resultado: list[Estado] = []
    for estado in estados:
        resultado.extend(_construir_variantes(estado))
    return resultado


def _construir_variantes(estado: EstadoCrudo) -> list[Estado]:
    if estado.tipo_estado == "simple":
        return [_construir_variante(estado, signo=1, nombre_grupo=None)]

    nombre_grupo = _construir_nombre_grupo(estado.tipo_carga, estado.grupo)
    variantes = [
        _construir_variante(estado, signo=1, nombre_grupo=nombre_grupo)
    ]

    if estado.incluir_opuesto:
        variantes.append(
            _construir_variante(estado, signo=-1, nombre_grupo=nombre_grupo)
        )

    return variantes


def _construir_variante(
    estado: EstadoCrudo, signo: int, nombre_grupo: str | None
) -> Estado:
    return Estado(
        nombre_estado=estado.nombre_estado,
        tipo_carga=estado.tipo_carga,
        tipo_estado=estado.tipo_estado,
        nombre_grupo=nombre_grupo,
        signo=signo,
    )


def _construir_nombre_grupo(tipo_carga: str, numero_grupo: int) -> str:
    return f"{tipo_carga}-{numero_grupo}"
