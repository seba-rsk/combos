import yaml
from pathlib import Path


SECCIONES_OBLIGATORIAS = {"metadata", "limit_states", "load_types", "combinations", "permanent_load_types"}


def leer_reglamento(ruta_yaml: str) -> dict:
    """
    Lee el archivo YAML del reglamento y devuelve su contenido validado.

    Raises:
        FileNotFoundError: Si el archivo no existe en la ruta indicada.
        ValueError: Si el YAML tiene sintaxis inválida, secciones faltantes,
                    tipos de carga desconocidos o factores inválidos.
    """
    contenido_crudo = _leer_archivo(ruta_yaml)
    datos = _parsear_yaml(contenido_crudo, ruta_yaml)
    _validar_secciones_obligatorias(datos)
    tipos_de_carga_definidos = set(datos["load_types"].keys())
    _validar_combinaciones(datos["combinations"], tipos_de_carga_definidos)
    _validar_tipos_permanentes(datos["permanent_load_types"], tipos_de_carga_definidos)
    _validar_tipos_permanentes_en_combinaciones(datos["combinations"], datos["permanent_load_types"])
    return _construir_reglamento(datos)


def _leer_archivo(ruta_yaml: str) -> str:
    ruta = Path(ruta_yaml)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo de reglamento: '{ruta_yaml}'")
    return ruta.read_text(encoding="utf-8")


def _parsear_yaml(contenido: str, ruta_yaml: str) -> dict:
    try:
        return yaml.safe_load(contenido)
    except yaml.YAMLError as error:
        raise ValueError(f"El archivo '{ruta_yaml}' contiene YAML con sintaxis inválida: {error}")


def _validar_secciones_obligatorias(datos: dict) -> None:
    secciones_presentes = set(datos.keys())
    secciones_faltantes = SECCIONES_OBLIGATORIAS - secciones_presentes
    if secciones_faltantes:
        raise ValueError(
            f"El reglamento está incompleto. Secciones faltantes: {sorted(secciones_faltantes)}"
        )


def _validar_combinaciones(combinations: dict, tipos_definidos: set) -> None:
    errores: list[str] = []
    for id_estado_limite, lista_combinaciones in combinations.items():
        for combinacion in lista_combinaciones:
            tipos_en_combinacion = set(combinacion["factors"].keys())
            tipos_desconocidos = tipos_en_combinacion - tipos_definidos
            if tipos_desconocidos:
                errores.append(
                    f"Combinación {combinacion['id']} del estado '{id_estado_limite}' "
                    f"referencia tipos de carga no definidos en load_types: {sorted(tipos_desconocidos)}"
                )
            _validar_factores_en_combinacion(combinacion, id_estado_limite)
    if errores:
        raise ValueError(
            f"Se encontraron {len(errores)} error(es) en las combinaciones:\n" +
            "\n".join(f"  • {e}" for e in errores)
        )


def _validar_factores_en_combinacion(combinacion: dict, id_estado_limite: str) -> None:
    for tipo_carga, factor in combinacion["factors"].items():
        if factor <= 0:
            raise ValueError(
                f"Combinación {combinacion['id']} del estado '{id_estado_limite}': "
                f"el factor del tipo de carga '{tipo_carga}' es {factor}. "
                f"Los factores de ponderación deben ser mayores que cero."
            )


def _validar_tipos_permanentes(
    tipos_permanentes: list, tipos_definidos: set
) -> None:
    if not tipos_permanentes:
        raise ValueError(
            "La clave 'permanent_load_types' está vacía. "
            "Debe definir al menos un tipo de carga permanente."
        )
    tipos_duplicados = [t for t in tipos_permanentes if tipos_permanentes.count(t) > 1]
    if tipos_duplicados:
        raise ValueError(
            f"La clave 'permanent_load_types' contiene tipos duplicados: {sorted(set(tipos_duplicados))}"
        )
    tipos_invalidos = [t for t in tipos_permanentes if t not in tipos_definidos]
    if tipos_invalidos:
        raise ValueError(
            f"'permanent_load_types' referencia tipos no definidos en load_types: {sorted(tipos_invalidos)}"
        )


def _validar_tipos_permanentes_en_combinaciones(
    combinations: dict, tipos_permanentes: list
) -> None:
    tipos_permanentes_set = set(tipos_permanentes)
    errores: list[str] = []
    for id_estado_limite, lista_combinaciones in combinations.items():
        for combinacion in lista_combinaciones:
            tipos_en_combinacion = set(combinacion["factors"].keys())
            if not tipos_en_combinacion & tipos_permanentes_set:
                errores.append(
                    f"Combinación {combinacion['id']} del estado '{id_estado_limite}' "
                    f"no contiene ningún tipo de carga permanente "
                    f"(se requiere al menos uno de: {sorted(tipos_permanentes_set)})"
                )
    if errores:
        raise ValueError(
            f"Se encontraron {len(errores)} error(es) de carga permanente:\n" +
            "\n".join(f"  • {e}" for e in errores)
        )


def _construir_reglamento(datos: dict) -> dict:
    return {
        "metadata": _construir_metadata(datos["metadata"]),
        "limit_states": _construir_estados_limite(datos["limit_states"]),
        "load_types": _construir_tipos_de_carga(datos["load_types"]),
        "combinations": _construir_combinaciones(datos["combinations"]),
        "permanent_load_types": list(datos["permanent_load_types"]),
    }


def _construir_metadata(metadata: dict) -> dict:
    return {
        "code_name": metadata["code_name"],
        "code_version": metadata["code_version"],
        "country": metadata["country"],
        "description": metadata["description"],
    }


def _construir_estados_limite(limit_states: dict) -> dict:
    return {
        id_estado: {
            "name": datos_estado["name"],
            "prefix": datos_estado["prefix"],
        }
        for id_estado, datos_estado in limit_states.items()
    }


def _construir_tipos_de_carga(load_types: dict) -> dict:
    return {
        id_tipo: {
            "name": datos_tipo["name"],
            "description": datos_tipo["description"],
        }
        for id_tipo, datos_tipo in load_types.items()
    }


def _construir_combinaciones(combinations: dict) -> dict:
    return {
        id_estado: [
            {
                "id": int(combinacion["id"]),
                "factors": dict(combinacion["factors"]),
            }
            for combinacion in lista_combinaciones
        ]
        for id_estado, lista_combinaciones in combinations.items()
    }
