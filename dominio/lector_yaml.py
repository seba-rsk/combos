import re
from pathlib import Path

import yaml

from dominio.modelos import OpcionParametro, ParametroReglamento

SECCIONES_OBLIGATORIAS = {
    "metadata",
    "limit_states",
    "load_types",
    "combinations",
    "permanent_load_types",
}

CLAVES_METADATA = ("code_name", "code_version", "country", "description")

# Tamaño máximo de un archivo YAML que COMBOS lee completo a memoria.
# Un reglamento real ocupa unos pocos KB; el límite corta archivos
# desmedidos antes de cargarlos.
MAX_BYTES_YAML = 2 * 1024 * 1024

CLAVE_REFERENCIA_PARAMETRO = "param"


def leer_reglamento(ruta_yaml: str) -> dict:
    """
    Lee el archivo YAML del reglamento y devuelve su contenido validado.

    Raises:
        FileNotFoundError: Si el archivo no existe en la ruta indicada.
        ValueError: Si el YAML tiene sintaxis inválida, secciones faltantes,
                    tipos de carga desconocidos, factores inválidos o una
                    sección `parameters` mal formada.
    """
    contenido_crudo = leer_texto_reglamento(ruta_yaml)
    return leer_reglamento_desde_texto(contenido_crudo, ruta_yaml)


def leer_texto_reglamento(ruta_yaml: str) -> str:
    """
    Devuelve el contenido de texto del archivo YAML del reglamento, sin
    parsear ni validar. Se expone aparte para que la sesión conserve el
    texto original tal como se leyó: el formato `.combos` lo embebe
    íntegro para poder reproducir el cálculo aunque el archivo externo
    cambie después.

    Raises:
        FileNotFoundError: Si el archivo no existe en la ruta indicada.
    """
    ruta = Path(ruta_yaml)
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de reglamento: '{ruta_yaml}'"
        )
    if ruta.stat().st_size > MAX_BYTES_YAML:
        raise ValueError(
            f"El archivo de reglamento '{ruta.name}' supera el tamaño "
            f"máximo admitido ({MAX_BYTES_YAML // (1024 * 1024)} MB). "
            f"Un reglamento real ocupa unos pocos KB; revisá que sea el "
            f"archivo correcto."
        )
    return ruta.read_text(encoding="utf-8")


def contiene_alias_yaml(contenido: str) -> bool:
    """
    Detecta si el documento YAML usa alias ('&ancla' / '*alias')
    recorriendo los eventos del parser, sin construir el documento: la
    expansión de alias anidados puede crear estructuras gigantes en
    memoria a partir de un archivo diminuto. Si la sintaxis es inválida
    devuelve False: ese error lo reporta el parseo normal.
    """
    try:
        return any(
            isinstance(evento, yaml.AliasEvent)
            for evento in yaml.parse(contenido)
        )
    except yaml.YAMLError:
        return False


def leer_reglamento_desde_texto(contenido: str, origen: str) -> dict:
    """
    Parsea y valida el texto YAML de un reglamento y devuelve su
    contenido validado. `origen` identifica de dónde salió el texto
    (nombre del archivo) para los mensajes de error.

    Raises:
        ValueError: Si el YAML tiene sintaxis inválida, secciones faltantes,
                    tipos de carga desconocidos, factores inválidos o una
                    sección `parameters` mal formada.
    """
    datos = _parsear_yaml(contenido, origen)
    _validar_secciones_obligatorias(datos)
    _validar_estructura_de_secciones(datos)
    _validar_metadata(datos["metadata"])
    parametros = _validar_y_construir_parametros(datos)
    tipos_de_carga_definidos = set(datos["load_types"].keys())
    _validar_combinaciones(
        datos["combinations"], tipos_de_carga_definidos, set(parametros)
    )
    _validar_ids_de_combinaciones(datos["combinations"])
    _validar_nombres_de_combinaciones(datos["combinations"])
    _validar_parametros_referenciados(datos["combinations"], set(parametros))
    _validar_tipos_permanentes(
        datos["permanent_load_types"], tipos_de_carga_definidos
    )
    _validar_tipos_permanentes_en_combinaciones(
        datos["combinations"], datos["permanent_load_types"]
    )
    return _construir_reglamento(datos, parametros)


def _parsear_yaml(contenido: str, ruta_yaml: str) -> dict:
    if contiene_alias_yaml(contenido):
        raise ValueError(
            f"El archivo '{ruta_yaml}' usa anclas y alias de YAML "
            f"('&' y '*'), que COMBOS no admite. Escribí cada valor de "
            f"forma explícita."
        )
    try:
        datos = yaml.safe_load(contenido)
    except yaml.YAMLError as error:
        raise ValueError(
            f"El archivo '{ruta_yaml}' contiene YAML con sintaxis "
            f"inválida: {error}"
        )
    if not isinstance(datos, dict) or not datos:
        raise ValueError(
            f"El archivo '{ruta_yaml}' no tiene la estructura de un "
            f"reglamento: el contenido debe ser un conjunto de secciones "
            f"(metadata, load_types, combinations...). Tomá como "
            f"referencia profiles/ejemplo_reglamento.yaml."
        )
    return datos


def _validar_secciones_obligatorias(datos: dict) -> None:
    secciones_presentes = set(datos.keys())
    secciones_faltantes = SECCIONES_OBLIGATORIAS - secciones_presentes
    if secciones_faltantes:
        raise ValueError(
            f"El reglamento está incompleto. "
            f"Secciones faltantes: {sorted(secciones_faltantes)}"
        )


def _validar_estructura_de_secciones(datos: dict) -> None:
    """
    Verifica que cada sección obligatoria tenga la estructura esperada
    (mapeo o lista, según corresponda) antes de que el pipeline itere
    sobre ellas. Sin esta validación, un reglamento mal armado provoca
    errores técnicos internos difíciles de interpretar para quien lo
    escribió.
    """
    _exigir_mapeo_no_vacio("metadata", datos["metadata"])
    _exigir_mapeo_no_vacio("limit_states", datos["limit_states"])
    _exigir_mapeo_no_vacio("load_types", datos["load_types"])
    _exigir_mapeo_no_vacio("combinations", datos["combinations"])
    _exigir_lista_no_vacia(
        "permanent_load_types", datos["permanent_load_types"]
    )
    _exigir_claves_de_texto("La sección 'limit_states'",
                            datos["limit_states"])
    _exigir_claves_de_texto("La sección 'load_types'", datos["load_types"])
    _validar_ids_de_tipos_de_carga(datos["load_types"])
    _exigir_claves_de_texto("La sección 'combinations'",
                            datos["combinations"])
    _exigir_elementos_de_texto(
        "permanent_load_types", datos["permanent_load_types"]
    )
    _validar_estructura_de_limit_states(datos["limit_states"])
    _validar_estructura_de_load_types(datos["load_types"])
    _validar_estructura_de_combinations(datos["combinations"])


def _exigir_mapeo_no_vacio(nombre_seccion: str, valor) -> None:
    if not isinstance(valor, dict) or not valor:
        raise ValueError(
            f"La sección '{nombre_seccion}' debe ser un mapeo de pares "
            f"clave/valor no vacío. Revisá el ejemplo en "
            f"profiles/ejemplo_reglamento.yaml."
        )


def _exigir_lista_no_vacia(nombre_seccion: str, valor) -> None:
    if not isinstance(valor, list) or not valor:
        raise ValueError(
            f"La sección '{nombre_seccion}' debe ser una lista no vacía "
            f"(por ejemplo '- D')."
        )


def _exigir_claves_de_texto(descripcion: str, mapeo: dict) -> None:
    """
    Los ids de un reglamento (estados límite, tipos de carga,
    parámetros, claves de factors) deben ser texto. Una clave YAML de
    otro tipo (ej. `1:` sin comillas) rompería las comparaciones y el
    ordenamiento de los mensajes aguas abajo con un error técnico.
    """
    for clave in mapeo:
        if not isinstance(clave, str) or not clave.strip():
            raise ValueError(
                f"{descripcion} tiene una clave que no es texto: "
                f"'{clave}'. Escribila entre comillas si es un número "
                f"(ej. \"{clave}\")."
            )


_PATRON_ID_TIPO_CARGA = re.compile(r"^[A-Za-z0-9_.\-]+$")


def _validar_ids_de_tipos_de_carga(load_types: dict) -> None:
    """
    Los ids de tipos de carga viajan a la lista desplegable de la
    plantilla Excel dentro de una fórmula de validación, donde una
    comilla o una coma romperían la fórmula. Se admiten letras, números,
    guion, guion bajo y punto — lo que un id real es en la práctica
    (D, L, Lr, W).
    """
    for id_tipo in load_types:
        if not _PATRON_ID_TIPO_CARGA.match(id_tipo):
            raise ValueError(
                f"El id de tipo de carga '{id_tipo}' contiene "
                f"caracteres no admitidos. Usá solo letras, números, "
                f"guion, guion bajo o punto (ej. D, Lr, W_x)."
            )


def _exigir_elementos_de_texto(nombre_seccion: str, lista: list) -> None:
    for elemento in lista:
        if not isinstance(elemento, str) or not elemento.strip():
            raise ValueError(
                f"La sección '{nombre_seccion}' tiene un elemento que "
                f"no es texto: '{elemento}'. Cada elemento debe ser el "
                f"id de un tipo de carga (por ejemplo '- D')."
            )


def _validar_estructura_de_limit_states(limit_states: dict) -> None:
    for id_estado, datos_estado in limit_states.items():
        contexto = (
            f"El estado límite '{id_estado}' de la sección limit_states"
        )
        if not isinstance(datos_estado, dict):
            raise ValueError(
                f"{contexto} debe ser un mapeo con las claves 'name' y "
                f"'prefix'."
            )
        for clave in ("name", "prefix"):
            valor = datos_estado.get(clave)
            if not isinstance(valor, str) or not valor.strip():
                raise ValueError(
                    f"{contexto}: falta la clave '{clave}' o está vacía."
                )


def _validar_estructura_de_load_types(load_types: dict) -> None:
    for id_tipo, datos_tipo in load_types.items():
        contexto = f"El tipo de carga '{id_tipo}' de la sección load_types"
        if not isinstance(datos_tipo, dict):
            raise ValueError(
                f"{contexto} debe ser un mapeo con las claves 'name' y "
                f"'description'."
            )
        for clave in ("name", "description"):
            valor = datos_tipo.get(clave)
            if not isinstance(valor, str) or not valor.strip():
                raise ValueError(
                    f"{contexto}: falta la clave '{clave}' o está vacía."
                )


def _validar_estructura_de_combinations(combinations: dict) -> None:
    for id_estado_limite, lista_combinaciones in combinations.items():
        contexto_estado = (
            f"El estado '{id_estado_limite}' de la sección combinations"
        )
        if (
            not isinstance(lista_combinaciones, list)
            or not lista_combinaciones
        ):
            raise ValueError(
                f"{contexto_estado} debe contener una lista no vacía de "
                f"combinaciones."
            )
        for posicion, combinacion in enumerate(
            lista_combinaciones, start=1
        ):
            _validar_estructura_de_combinacion(
                combinacion, id_estado_limite, posicion
            )


def _validar_estructura_de_combinacion(
    combinacion, id_estado_limite: str, posicion: int
) -> None:
    contexto = (
        f"La combinación número {posicion} del estado "
        f"'{id_estado_limite}'"
    )
    if not isinstance(combinacion, dict):
        raise ValueError(
            f"{contexto} debe ser un mapeo con las claves 'id' y "
            f"'factors'."
        )
    for clave in ("id", "factors"):
        if clave not in combinacion:
            raise ValueError(f"{contexto}: falta la clave '{clave}'.")
    factors = combinacion["factors"]
    if not isinstance(factors, dict) or not factors:
        raise ValueError(
            f"{contexto}: la clave 'factors' debe ser un mapeo no vacío "
            f"de tipos de carga a factores."
        )
    _exigir_claves_de_texto(f"{contexto}: la clave 'factors'", factors)


def _validar_combinaciones(
    combinations: dict, tipos_definidos: set, ids_parametros: set
) -> None:
    errores: list[str] = []
    for id_estado_limite, lista_combinaciones in combinations.items():
        for combinacion in lista_combinaciones:
            tipos_en_combinacion = set(combinacion["factors"].keys())
            tipos_desconocidos = tipos_en_combinacion - tipos_definidos
            if tipos_desconocidos:
                errores.append(
                    f"Combinación {combinacion['id']} del estado "
                    f"'{id_estado_limite}' referencia tipos de carga no "
                    f"definidos en load_types: {sorted(tipos_desconocidos)}"
                )
            errores.extend(
                _errores_de_factores(
                    combinacion, id_estado_limite, ids_parametros
                )
            )
    if errores:
        raise ValueError(
            f"Se encontraron {len(errores)} error(es) en las combinaciones:\n"
            + "\n".join(f"  • {e}" for e in errores)
        )


def _errores_de_factores(
    combinacion: dict, id_estado_limite: str, ids_parametros: set
) -> list[str]:
    contexto = (
        f"Combinación {combinacion['id']} del estado '{id_estado_limite}'"
    )
    errores: list[str] = []
    for tipo_carga, factor in combinacion["factors"].items():
        if isinstance(factor, dict):
            error = _error_de_referencia_a_parametro(
                factor, tipo_carga, contexto, ids_parametros
            )
            if error:
                errores.append(error)
        elif es_numero(factor):
            if factor <= 0:
                errores.append(
                    f"{contexto}: el factor del tipo de carga "
                    f"'{tipo_carga}' es {factor}. Los factores de "
                    f"ponderación deben ser mayores que cero."
                )
        else:
            errores.append(
                f"{contexto}: el factor del tipo de carga '{tipo_carga}' "
                f"es '{factor}'. Debe ser un número mayor que cero o una "
                f"referencia a un parámetro con la forma "
                f"{{ {CLAVE_REFERENCIA_PARAMETRO}: <id> }}."
            )
    return errores


def _error_de_referencia_a_parametro(
    referencia: dict,
    tipo_carga: str,
    contexto: str,
    ids_parametros: set,
) -> str | None:
    if set(referencia.keys()) != {CLAVE_REFERENCIA_PARAMETRO}:
        claves = sorted(str(clave) for clave in referencia.keys())
        return (
            f"{contexto}: la referencia a parámetro del tipo de carga "
            f"'{tipo_carga}' no tiene la forma esperada "
            f"{{ {CLAVE_REFERENCIA_PARAMETRO}: <id> }}. "
            f"Claves encontradas: {claves}."
        )
    id_parametro = referencia[CLAVE_REFERENCIA_PARAMETRO]
    if id_parametro not in ids_parametros:
        return (
            f"{contexto}: el tipo de carga '{tipo_carga}' referencia el "
            f"parámetro '{id_parametro}', que no está definido en la "
            f"sección parameters del reglamento."
        )
    return None


def _validar_parametros_referenciados(
    combinations: dict, ids_parametros: set
) -> None:
    referenciados = {
        factor[CLAVE_REFERENCIA_PARAMETRO]
        for lista_combinaciones in combinations.values()
        for combinacion in lista_combinaciones
        for factor in combinacion["factors"].values()
        if isinstance(factor, dict)
    }
    sin_uso = ids_parametros - referenciados
    if sin_uso:
        raise ValueError(
            f"La sección parameters define parámetros que ninguna "
            f"combinación referencia: {sorted(sin_uso)}. Agregá la "
            f"referencia {{ {CLAVE_REFERENCIA_PARAMETRO}: <id> }} en los "
            f"factores que correspondan, o eliminá el parámetro sin uso."
        )


def es_numero(valor) -> bool:
    """Devuelve True si el valor es un número real (excluye bool)."""
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _validar_ids_de_combinaciones(combinations: dict) -> None:
    errores: list[str] = []
    for id_estado_limite, lista_combinaciones in combinations.items():
        vistos: set[int] = set()
        for combinacion in lista_combinaciones:
            id_crudo = combinacion["id"]
            id_normalizado = _id_entero(id_crudo)
            if id_normalizado is None:
                errores.append(
                    f"El estado '{id_estado_limite}' tiene una "
                    f"combinación con id '{id_crudo}', que no es un "
                    f"número entero. Usá un entero (ej. id: 3)."
                )
                continue
            if id_normalizado in vistos:
                errores.append(
                    f"El estado '{id_estado_limite}' tiene más de una "
                    f"combinación con id {id_normalizado}. Cada id debe "
                    f"ser único dentro de su estado límite."
                )
            vistos.add(id_normalizado)
    if errores:
        raise ValueError(
            f"Se encontraron {len(errores)} error(es) en los ids de "
            f"combinaciones:\n" + "\n".join(f"  • {e}" for e in errores)
        )


def _id_entero(valor) -> int | None:
    """
    Normaliza el id de una combinación a entero, o devuelve None si no
    representa un entero. Acepta las variantes que YAML puede producir
    para el mismo id (3, 3.0, "3"), para que la detección de duplicados
    compare lo mismo que consume el resto del pipeline.
    """
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    if isinstance(valor, str):
        try:
            return int(valor.strip())
        except ValueError:
            return None
    return None


def _validar_nombres_de_combinaciones(combinations: dict) -> None:
    errores: list[str] = []
    vistos: dict[str, str] = {}
    for id_estado_limite, lista_combinaciones in combinations.items():
        for combinacion in lista_combinaciones:
            ubicacion = (
                f"la combinación {combinacion['id']} del estado "
                f"'{id_estado_limite}'"
            )
            error = _validar_nombre_de_combinacion(
                combinacion, ubicacion, vistos
            )
            if error:
                errores.append(error)
    if errores:
        raise ValueError(
            f"Se encontraron {len(errores)} error(es) en los nombres de "
            f"combinaciones:\n" + "\n".join(f"  • {e}" for e in errores)
        )


def _validar_nombre_de_combinacion(
    combinacion: dict, ubicacion: str, vistos: dict[str, str]
) -> str | None:
    """
    Devuelve el mensaje de error si la clave `name` es inválida, o None
    si es válida (o está ausente). Cuando es válida, registra el nombre
    en `vistos` para poder detectar repeticiones más adelante.
    """
    if "name" not in combinacion or combinacion["name"] is None:
        return None
    if not _es_escalar(combinacion["name"]):
        return (
            f"La clave 'name' de {ubicacion} debe ser un texto "
            f"(ej. \"U3.1\"); se encontró '{combinacion['name']}'."
        )
    nombre = _nombre_de_combinacion(combinacion)
    if nombre is None:
        return (
            f"La clave 'name' de {ubicacion} está vacía. Escribí la "
            f"designación (ej. \"U3.1\") o eliminá la clave."
        )
    if nombre in vistos:
        return (
            f"El nombre '{nombre}' está repetido: lo usan "
            f"{vistos[nombre]} y {ubicacion}. Los nombres deben ser "
            f"únicos en todo el reglamento."
        )
    vistos[nombre] = ubicacion
    return None


def _nombre_de_combinacion(combinacion: dict) -> str | None:
    """
    Devuelve la designación normativa de la combinación normalizada a
    texto, o None si no tiene (clave ausente, nula, en blanco o de un
    tipo no escalar — este último caso lo rechaza antes la validación).
    Acepta cualquier escalar: un `name: 9.5` sin comillas llega como
    número desde el YAML y se convierte a "9.5" en vez de fallar.
    """
    if "name" not in combinacion or combinacion["name"] is None:
        return None
    if not _es_escalar(combinacion["name"]):
        return None
    nombre = str(combinacion["name"]).strip()
    return nombre or None


def _es_escalar(valor) -> bool:
    return isinstance(valor, str) or es_numero(valor)


def _validar_tipos_permanentes(
    tipos_permanentes: list, tipos_definidos: set
) -> None:
    if not tipos_permanentes:
        raise ValueError(
            "La clave 'permanent_load_types' está vacía. "
            "Debe definir al menos un tipo de carga permanente."
        )
    tipos_duplicados = [
        t for t in tipos_permanentes if tipos_permanentes.count(t) > 1
    ]
    if tipos_duplicados:
        raise ValueError(
            f"La clave 'permanent_load_types' contiene tipos duplicados: "
            f"{sorted(set(tipos_duplicados))}"
        )
    tipos_invalidos = [t for t in tipos_permanentes if t not in tipos_definidos]
    if tipos_invalidos:
        raise ValueError(
            f"'permanent_load_types' referencia tipos no definidos en "
            f"load_types: {sorted(tipos_invalidos)}"
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
                    f"Combinación {combinacion['id']} del estado "
                    f"'{id_estado_limite}' no contiene ningún tipo de carga "
                    f"permanente (se requiere al menos uno de: "
                    f"{sorted(tipos_permanentes_set)})"
                )
    if errores:
        raise ValueError(
            f"Se encontraron {len(errores)} error(es) de carga permanente:\n"
            + "\n".join(f"  • {e}" for e in errores)
        )


def _validar_y_construir_parametros(
    datos: dict,
) -> dict[str, ParametroReglamento]:
    if "parameters" not in datos:
        return {}
    parameters = datos["parameters"]
    if not isinstance(parameters, dict) or not parameters:
        raise ValueError(
            "La sección parameters está vacía o mal formada. Debe definir "
            "al menos un parámetro, o eliminarse si el reglamento no "
            "usa parámetros."
        )
    _exigir_claves_de_texto("La sección 'parameters'", parameters)
    return {
        id_parametro: _construir_parametro(id_parametro, definicion)
        for id_parametro, definicion in parameters.items()
    }


def _construir_parametro(
    id_parametro: str, definicion
) -> ParametroReglamento:
    contexto = f"Parámetro '{id_parametro}' de la sección parameters"
    if not isinstance(definicion, dict):
        raise ValueError(
            f"{contexto}: la definición debe ser un mapeo con las claves "
            f"'name', 'options' y 'default'."
        )
    nombre = definicion.get("name")
    if not isinstance(nombre, str) or not nombre.strip():
        raise ValueError(
            f"{contexto}: falta la clave 'name' o está vacía. Es el "
            f"título que se muestra al elegir la opción."
        )
    opciones = _construir_opciones(definicion.get("options"), contexto)
    valor_default = _validar_default(
        definicion.get("default"), opciones, contexto
    )
    return ParametroReglamento(
        id_parametro=id_parametro,
        nombre=nombre.strip(),
        opciones=opciones,
        valor_default=valor_default,
    )


def _construir_opciones(options, contexto: str) -> list[OpcionParametro]:
    if not isinstance(options, list) or len(options) < 2:
        raise ValueError(
            f"{contexto}: la clave 'options' debe ser una lista con al "
            f"menos dos opciones (label + value). Con una sola opción no "
            f"hay nada que elegir: usá el número directamente como factor."
        )
    opciones: list[OpcionParametro] = []
    for numero, option in enumerate(options, start=1):
        etiqueta = option.get("label") if isinstance(option, dict) else None
        valor = option.get("value") if isinstance(option, dict) else None
        if not isinstance(etiqueta, str) or not etiqueta.strip():
            raise ValueError(
                f"{contexto}, opción {numero}: falta la clave 'label' o "
                f"está vacía. Es el texto que describe la opción."
            )
        if not es_numero(valor) or valor <= 0:
            raise ValueError(
                f"{contexto}, opción {numero}: la clave 'value' debe ser "
                f"un número mayor que cero (se encontró '{valor}')."
            )
        opciones.append(
            OpcionParametro(etiqueta=etiqueta.strip(), valor=float(valor))
        )
    return opciones


def _validar_default(
    default, opciones: list[OpcionParametro], contexto: str
) -> float:
    valores = [opcion.valor for opcion in opciones]
    if not es_numero(default) or float(default) not in valores:
        raise ValueError(
            f"{contexto}: la clave 'default' debe coincidir con el "
            f"'value' de una de las opciones ({valores}); se encontró "
            f"'{default}'."
        )
    return float(default)


def _validar_metadata(metadata: dict) -> None:
    """
    Verifica que la sección metadata tenga las cuatro claves que
    identifican el reglamento y que sus valores sean escalares no
    vacíos. Al construir el reglamento se convierten siempre a texto,
    así aguas abajo (pantalla, Excel, sesiones `.combos`) nunca aparece
    un valor de otro tipo.
    """
    faltantes = [clave for clave in CLAVES_METADATA if clave not in metadata]
    if faltantes:
        raise ValueError(
            f"La sección metadata está incompleta. Claves faltantes: "
            f"{faltantes}. Tomá como referencia "
            f"profiles/ejemplo_reglamento.yaml."
        )
    for clave in CLAVES_METADATA:
        valor = metadata[clave]
        if not _es_escalar(valor) or not str(valor).strip():
            raise ValueError(
                f"La clave '{clave}' de la sección metadata debe ser un "
                f"texto o número no vacío; se encontró '{valor}'."
            )


def _construir_reglamento(
    datos: dict, parametros: dict[str, ParametroReglamento]
) -> dict:
    return {
        "metadata": _construir_metadata(datos["metadata"]),
        "limit_states": _construir_estados_limite(datos["limit_states"]),
        "load_types": _construir_tipos_de_carga(datos["load_types"]),
        "combinations": _construir_combinaciones(datos["combinations"]),
        "permanent_load_types": list(datos["permanent_load_types"]),
        "parameters": parametros,
    }


def _construir_metadata(metadata: dict) -> dict:
    return {
        clave: str(metadata[clave]).strip() for clave in CLAVES_METADATA
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
                "name": _nombre_de_combinacion(combinacion),
                "factors": dict(combinacion["factors"]),
            }
            for combinacion in lista_combinaciones
        ]
        for id_estado, lista_combinaciones in combinations.items()
    }
