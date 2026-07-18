"""
Conversión de una Sesion a datos serializables (formato `.combos`) y
reconstrucción inversa.

El formato guarda inputs y decisiones del usuario —texto del reglamento
usado, estados de carga, elecciones de parámetros y descartes—, nunca
resultados calculados: al abrir, las combinaciones se regeneran con el
pipeline de dominio a partir de lo guardado. El esquema 1 solo persiste
sesiones completas (con reglamento y estados); el guardado de sesiones
a medias que habilite la GUI será un cambio de esquema versionado.

La lectura y escritura del archivo físico vive en
infraestructura.archivo_combos; acá no hay ningún acceso a disco.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from combos.dominio.lector_plantilla import (
    ErrorValidacionPlantilla,
    leer_plantilla,
)
from combos.dominio.lector_yaml import (
    MAX_BYTES_YAML,
    es_numero,
    leer_reglamento_desde_texto,
)
from combos.dominio.modelos import EleccionParametro, Estado, EstadoCrudo
from combos.dominio.parametros import (
    crear_eleccion,
    numero_opcion_default,
    resolver_parametros,
)
from combos.dominio.sesion import (
    ErrorLimiteCombinaciones,
    Sesion,
    aplicar_descartes,
    combinaciones_superadas,
    procesar,
)

VERSION_ESQUEMA = 1

_CLAVES_OBLIGATORIAS = {
    "schema_version",
    "combos_version",
    "guardado_el",
    "nombre_perfil",
    "reglamento_yaml",
    "estados",
    "elecciones",
    "descartes",
}

_TIPOS_DE_CLAVES = {
    "combos_version": str,
    "guardado_el": str,
    "nombre_perfil": str,
    "reglamento_yaml": str,
    "estados": list,
    "elecciones": list,
    "descartes": list,
}

# Público: infraestructura.archivo_combos lo usa para dar el mismo
# mensaje cuando el archivo ni siquiera se puede parsear como JSON.
MENSAJE_ARCHIVO_DANADO = (
    "el archivo está dañado o no es una sesión de COMBOS. Generalo de "
    "nuevo desde el programa o pedí una copia a quien te lo compartió."
)


class ErrorSesionInvalida(Exception):
    """
    El contenido de un archivo `.combos` no corresponde a una sesión
    utilizable. El mensaje empieza en minúscula: la interfaz lo muestra
    detrás de un prefijo con el nombre del archivo.
    """


def sesion_a_datos(sesion: Sesion, version_combos: str) -> dict:
    """
    Convierte la sesión en el diccionario serializable del formato
    `.combos` (esquema 1): inputs y decisiones del usuario, nunca las
    combinaciones calculadas, que se regeneran al abrir.

    Args:
        sesion: Sesión completa (con reglamento cargado y estados leídos).
        version_combos: Versión del programa que guarda, para registrar
            el origen del archivo.

    Raises:
        ValueError: Si la sesión está incompleta (sin reglamento cargado
            o sin estados de carga leídos): el esquema 1 solo persiste
            sesiones completas.
    """
    if (
        sesion.reglamento_texto is None
        or sesion.nombre_perfil is None
        or not sesion.estados_crudos
    ):
        raise ValueError(
            "La sesión está incompleta (falta el reglamento o los "
            "estados de carga); no se puede guardar."
        )
    return {
        "schema_version": VERSION_ESQUEMA,
        "combos_version": version_combos,
        "guardado_el": datetime.now().isoformat(timespec="seconds"),
        "nombre_perfil": sesion.nombre_perfil,
        "reglamento_yaml": sesion.reglamento_texto,
        "estados": [asdict(estado) for estado in sesion.estados_crudos],
        "elecciones": [
            {"id_parametro": e.id_parametro, "valor": e.valor}
            for e in sesion.elecciones
        ],
        "descartes": sorted(
            c.indice_generacion
            for c in sesion.combinaciones
            if c.descartada_por_usuario
        ),
    }


def sesion_desde_datos(datos) -> tuple[Sesion, list[str]]:
    """
    Reconstruye una sesión completa desde los datos de un archivo
    `.combos`: re-valida el reglamento embebido y los estados, vuelve a
    resolver los parámetros desde el reglamento crudo, regenera las
    combinaciones con el pipeline y reaplica los descartes guardados.

    Returns:
        Tupla (sesión reconstruida, avisos no bloqueantes). Hoy el único
        aviso posible es que algunos descartes guardados ya no
        correspondan a ninguna combinación superada.

    Raises:
        ErrorSesionInvalida: Si los datos no tienen la estructura del
            esquema, la versión es más nueva que la soportada, el
            reglamento embebido o los estados no pasan la validación,
            alguna elección no corresponde a los parámetros del
            reglamento, o la regeneración excedería el límite de
            combinaciones que COMBOS procesa.
    """
    _validar_estructura(datos)
    reglamento_crudo = _validar_reglamento_embebido(
        datos["reglamento_yaml"], datos["nombre_perfil"]
    )
    estados_crudos = _reconstruir_estados(datos["estados"])
    estados = _validar_estados(estados_crudos, reglamento_crudo)
    elecciones = _reconstruir_elecciones(
        reglamento_crudo, datos["elecciones"]
    )
    sesion = Sesion(
        reglamento_texto=datos["reglamento_yaml"],
        reglamento_crudo=reglamento_crudo,
        reglamento=_resolver_con_defaults(reglamento_crudo, elecciones),
        nombre_perfil=datos["nombre_perfil"],
        elecciones=elecciones,
        estados_crudos=estados_crudos,
        estados=estados,
    )
    try:
        procesar(sesion)
    except ErrorLimiteCombinaciones as error:
        raise ErrorSesionInvalida(
            "la sesión genera más combinaciones de las que COMBOS puede "
            f"procesar. {error} El archivo puede estar mal armado o "
            "haberse creado con datos desmedidos."
        ) from error
    avisos = _reaplicar_descartes(sesion, datos["descartes"])
    return sesion, avisos


# ── Validación de estructura ──────────────────────────────────────────────────

def _validar_estructura(datos) -> None:
    if not isinstance(datos, dict):
        raise ErrorSesionInvalida(MENSAJE_ARCHIVO_DANADO)
    _validar_version_de_esquema(datos.get("schema_version"))
    if _CLAVES_OBLIGATORIAS - set(datos):
        raise ErrorSesionInvalida(MENSAJE_ARCHIVO_DANADO)
    for clave, tipo in _TIPOS_DE_CLAVES.items():
        if not isinstance(datos[clave], tipo):
            raise ErrorSesionInvalida(MENSAJE_ARCHIVO_DANADO)


def _validar_version_de_esquema(version) -> None:
    if not isinstance(version, int) or isinstance(version, bool):
        raise ErrorSesionInvalida(MENSAJE_ARCHIVO_DANADO)
    if version > VERSION_ESQUEMA:
        raise ErrorSesionInvalida(
            "la sesión se guardó con una versión más nueva de COMBOS y "
            "este programa no puede leerla. Actualizá COMBOS para "
            "abrirla."
        )


# ── Reconstrucción del reglamento y los estados ───────────────────────────────

def _validar_reglamento_embebido(texto: str, nombre_perfil: str) -> dict:
    if not texto.strip():
        raise ErrorSesionInvalida(MENSAJE_ARCHIVO_DANADO)
    if len(texto.encode("utf-8")) > MAX_BYTES_YAML:
        # El mismo tope que rige para un YAML leído de disco: sin él,
        # el reglamento embebido solo estaba acotado por el tamaño
        # total del archivo .combos, mucho mayor.
        raise ErrorSesionInvalida(
            f"el reglamento guardado dentro de la sesión supera el "
            f"tamaño máximo admitido "
            f"({MAX_BYTES_YAML // (1024 * 1024)} MB). "
            f"{MENSAJE_ARCHIVO_DANADO}"
        )
    try:
        return leer_reglamento_desde_texto(texto, nombre_perfil)
    except ValueError as error:
        raise ErrorSesionInvalida(
            f"el reglamento guardado dentro de la sesión tiene un "
            f"problema: {error}"
        ) from error


def _reconstruir_estados(estados_datos: list) -> list[EstadoCrudo]:
    if not estados_datos:
        raise ErrorSesionInvalida(
            "la sesión no tiene estados de carga guardados, así que no "
            "hay nada para regenerar. Empezá una sesión nueva."
        )
    return [
        _reconstruir_estado(datos_estado) for datos_estado in estados_datos
    ]


def _reconstruir_estado(datos_estado) -> EstadoCrudo:
    if not isinstance(datos_estado, dict):
        raise ErrorSesionInvalida(MENSAJE_ARCHIVO_DANADO)
    if not _es_estado_bien_tipado(datos_estado):
        raise ErrorSesionInvalida(MENSAJE_ARCHIVO_DANADO)
    return EstadoCrudo(
        nombre_estado=datos_estado["nombre_estado"],
        tipo_carga=datos_estado["tipo_carga"],
        tipo_estado=datos_estado["tipo_estado"],
        grupo=datos_estado["grupo"],
        incluir_opuesto=datos_estado["incluir_opuesto"],
    )


def _es_estado_bien_tipado(datos_estado: dict) -> bool:
    """
    Aplica las mismas reglas que la lectura de la planilla Excel
    (infraestructura.lector_excel): tipo de estado exactamente "simple"
    (sin grupo ni opuesto) o "direccional" (grupo entero positivo y
    opuesto sí/no). Un estado con tipo desconocido no puede aceptarse:
    el generador lo excluiría de todas las combinaciones en silencio.
    """
    if not (
        isinstance(datos_estado.get("nombre_estado"), str)
        and isinstance(datos_estado.get("tipo_carga"), str)
    ):
        return False
    tipo_estado = datos_estado.get("tipo_estado")
    if tipo_estado == "simple":
        return (
            datos_estado.get("grupo") is None
            and datos_estado.get("incluir_opuesto") is False
        )
    if tipo_estado == "direccional":
        return _es_grupo_direccional_valido(
            datos_estado.get("grupo")
        ) and isinstance(datos_estado.get("incluir_opuesto"), bool)
    return False


def _es_grupo_direccional_valido(grupo) -> bool:
    return (
        isinstance(grupo, int)
        and not isinstance(grupo, bool)
        and grupo > 0
    )


def _validar_estados(
    estados_crudos: list[EstadoCrudo], reglamento: dict
) -> list[Estado]:
    try:
        return leer_plantilla(estados_crudos, reglamento)
    except ErrorValidacionPlantilla as error:
        raise ErrorSesionInvalida(
            "los estados de carga guardados no son válidos para el "
            f"reglamento de la sesión: {'; '.join(error.errores)}"
        ) from error


# ── Reconstrucción de elecciones y descartes ──────────────────────────────────

def _reconstruir_elecciones(
    reglamento: dict, elecciones_datos: list
) -> list[EleccionParametro]:
    elecciones: list[EleccionParametro] = []
    vistos: set[str] = set()
    for datos_eleccion in elecciones_datos:
        eleccion = _reconstruir_eleccion(
            reglamento["parameters"], datos_eleccion
        )
        if eleccion.id_parametro in vistos:
            raise ErrorSesionInvalida(
                f"la sesión guarda más de una elección del parámetro "
                f"'{eleccion.id_parametro}'."
            )
        vistos.add(eleccion.id_parametro)
        elecciones.append(eleccion)
    return elecciones


def _reconstruir_eleccion(
    parametros: dict, datos_eleccion
) -> EleccionParametro:
    if not isinstance(datos_eleccion, dict):
        raise ErrorSesionInvalida(MENSAJE_ARCHIVO_DANADO)
    id_parametro = datos_eleccion.get("id_parametro")
    valor = datos_eleccion.get("valor")
    if not isinstance(id_parametro, str) or not es_numero(valor):
        raise ErrorSesionInvalida(MENSAJE_ARCHIVO_DANADO)
    parametro = parametros.get(id_parametro)
    if parametro is None:
        raise ErrorSesionInvalida(
            f"la sesión guarda una elección del parámetro "
            f"'{id_parametro}', que no existe en el reglamento de la "
            f"sesión."
        )
    for numero, opcion in enumerate(parametro.opciones, start=1):
        if opcion.valor == valor:
            return crear_eleccion(parametro, numero)
    raise ErrorSesionInvalida(
        f"la elección guardada del parámetro '{id_parametro}' (valor "
        f"{valor}) no coincide con ninguna de sus opciones."
    )


def _resolver_con_defaults(
    reglamento_crudo: dict, elecciones: list[EleccionParametro]
) -> dict:
    """
    Resuelve los parámetros desde el crudo con las elecciones guardadas;
    los parámetros sin elección (no aplicaban al guardar) se resuelven
    con su default, igual que en el flujo original.
    """
    cubiertos = {e.id_parametro for e in elecciones}
    internas = [
        crear_eleccion(parametro, numero_opcion_default(parametro))
        for id_parametro, parametro in reglamento_crudo[
            "parameters"
        ].items()
        if id_parametro not in cubiertos
    ]
    return resolver_parametros(reglamento_crudo, elecciones + internas)


def _reaplicar_descartes(sesion: Sesion, descartes_datos: list) -> list[str]:
    indices = set()
    for valor in descartes_datos:
        if not isinstance(valor, int) or isinstance(valor, bool):
            raise ErrorSesionInvalida(MENSAJE_ARCHIVO_DANADO)
        indices.add(valor)
    validos = {
        c.indice_generacion for c in combinaciones_superadas(sesion)
    }
    aplicar_descartes(sesion, indices & validos)
    huerfanos = indices - validos
    if huerfanos:
        return [_aviso_descartes_huerfanos(len(huerfanos))]
    return []


def _aviso_descartes_huerfanos(cantidad: int) -> str:
    if cantidad == 1:
        return (
            "1 descarte guardado no corresponde a ninguna combinación "
            "superada y se ignoró. Revisá las combinaciones superadas "
            "en el resumen."
        )
    return (
        f"{cantidad} descartes guardados no corresponden a ninguna "
        "combinación superada y se ignoraron. Revisá las combinaciones "
        "superadas en el resumen."
    )
