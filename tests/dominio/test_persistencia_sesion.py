from __future__ import annotations

import json

import pytest

from dominio.lector_plantilla import leer_plantilla
from dominio.lector_yaml import leer_reglamento_desde_texto
from dominio.modelos import EstadoCrudo
from dominio.parametros import crear_eleccion, resolver_parametros
from dominio.persistencia_sesion import (
    VERSION_ESQUEMA,
    ErrorSesionInvalida,
    sesion_a_datos,
    sesion_desde_datos,
)
from dominio.sesion import (
    Sesion,
    aplicar_descartes,
    combinaciones_superadas,
    procesar,
)

REGLAMENTO_YAML = """
metadata:
  code_name: TEST
  code_version: "1"
  country: Testland
  description: Reglamento de prueba

limit_states:
  ELU:
    name: Estado límite último
    prefix: U

load_types:
  D:
    name: Permanente
    description: Carga permanente
  L:
    name: Viva
    description: Sobrecarga de uso

permanent_load_types: [D]

parameters:
  K:
    name: Factor de sobrecarga
    options:
      - label: Normal
        value: 1.0
      - label: Reducido
        value: 0.5
    default: 1.0

combinations:
  ELU:
    - id: 1
      factors: {D: 1.4}
    - id: 2
      factors:
        D: 1.2
        L: {param: K}
    - id: 3
      factors: {D: 1.2}
"""


def _estado_crudo(nombre: str, tipo: str) -> EstadoCrudo:
    return EstadoCrudo(
        nombre_estado=nombre,
        tipo_carga=tipo,
        tipo_estado="simple",
        grupo=None,
        incluir_opuesto=False,
    )


@pytest.fixture
def sesion_completa() -> Sesion:
    """
    Sesión como la deja el flujo al llegar al cierre: reglamento con el
    parámetro K elegido en 0.5, estados D y L, tres combinaciones
    generadas (1.2D superada por 1.4D) y la superada descartada.
    """
    crudo = leer_reglamento_desde_texto(REGLAMENTO_YAML, "test.yaml")
    estados_crudos = [_estado_crudo("DEAD", "D"), _estado_crudo("SC", "L")]
    eleccion = crear_eleccion(crudo["parameters"]["K"], 2)
    sesion = Sesion(
        reglamento_texto=REGLAMENTO_YAML,
        reglamento_crudo=crudo,
        reglamento=resolver_parametros(crudo, [eleccion]),
        nombre_perfil="test.yaml",
        elecciones=[eleccion],
        estados_crudos=estados_crudos,
        estados=leer_plantilla(estados_crudos, crudo),
    )
    procesar(sesion)
    indice_superada = combinaciones_superadas(sesion)[0].indice_generacion
    aplicar_descartes(sesion, {indice_superada})
    return sesion


@pytest.fixture
def datos_validos(sesion_completa) -> dict:
    return sesion_a_datos(sesion_completa, "1.2.0")


# ── sesion_a_datos ────────────────────────────────────────────────────────────

def test_datos_guardan_inputs_y_decisiones_no_resultados(
    sesion_completa, datos_validos
):
    assert set(datos_validos) == {
        "schema_version", "combos_version", "guardado_el",
        "nombre_perfil", "reglamento_yaml", "estados", "elecciones",
        "descartes",
    }
    assert datos_validos["schema_version"] == VERSION_ESQUEMA
    assert datos_validos["reglamento_yaml"] == REGLAMENTO_YAML
    assert datos_validos["elecciones"] == [
        {"id_parametro": "K", "valor": 0.5}
    ]
    indice_superada = (
        combinaciones_superadas(sesion_completa)[0].indice_generacion
    )
    assert datos_validos["descartes"] == [indice_superada]


def test_sesion_incompleta_no_se_puede_guardar():
    with pytest.raises(ValueError, match="incompleta"):
        sesion_a_datos(Sesion(), "1.2.0")


# ── ida y vuelta ──────────────────────────────────────────────────────────────

def test_ida_y_vuelta_reconstruye_la_misma_sesion(
    sesion_completa, datos_validos
):
    sesion2, avisos = sesion_desde_datos(datos_validos)

    assert avisos == []
    assert sesion2.combinaciones == sesion_completa.combinaciones
    assert sesion2.elecciones == sesion_completa.elecciones
    assert sesion2.estados_crudos == sesion_completa.estados_crudos
    assert sesion2.estados == sesion_completa.estados
    assert sesion2.nombre_perfil == sesion_completa.nombre_perfil
    assert sesion2.reglamento_texto == REGLAMENTO_YAML


def test_ida_y_vuelta_sobrevive_al_json(sesion_completa, datos_validos):
    """
    El diccionario debe ser JSON puro: serializarlo y parsearlo no puede
    cambiar la sesión reconstruida.
    """
    datos_desde_json = json.loads(
        json.dumps(datos_validos, ensure_ascii=False)
    )

    sesion2, _ = sesion_desde_datos(datos_desde_json)

    assert sesion2.combinaciones == sesion_completa.combinaciones


def test_reconstruccion_es_determinista(datos_validos):
    """
    Los descartes se guardan por índice de generación: abrir dos veces
    el mismo archivo debe regenerar exactamente las mismas
    combinaciones, en el mismo orden.
    """
    sesion_a, _ = sesion_desde_datos(datos_validos)
    sesion_b, _ = sesion_desde_datos(datos_validos)

    assert sesion_a.combinaciones == sesion_b.combinaciones


def test_parametro_sin_eleccion_se_resuelve_con_default(datos_validos):
    datos_validos["elecciones"] = []

    sesion2, avisos = sesion_desde_datos(datos_validos)

    factores = sesion2.reglamento["combinations"]["ELU"][1]["factors"]
    assert factores["L"] == 1.0
    assert sesion2.elecciones == []
    assert avisos == []


# ── estructura inválida ───────────────────────────────────────────────────────

def test_datos_que_no_son_un_mapeo_lanzan_error():
    with pytest.raises(ErrorSesionInvalida, match="dañado"):
        sesion_desde_datos(["no soy una sesión"])


def test_clave_faltante_lanza_error(datos_validos):
    del datos_validos["estados"]
    with pytest.raises(ErrorSesionInvalida, match="dañado"):
        sesion_desde_datos(datos_validos)


def test_version_de_esquema_mas_nueva_pide_actualizar(datos_validos):
    datos_validos["schema_version"] = VERSION_ESQUEMA + 1
    with pytest.raises(ErrorSesionInvalida, match="más nueva"):
        sesion_desde_datos(datos_validos)


def test_estado_mal_tipado_lanza_error(datos_validos):
    datos_validos["estados"][0]["grupo"] = "uno"
    with pytest.raises(ErrorSesionInvalida, match="dañado"):
        sesion_desde_datos(datos_validos)


def test_tipo_de_estado_desconocido_lanza_error(datos_validos):
    """
    Un tipo de estado que no sea exactamente "simple" o "direccional"
    (ej. "Simple" editado a mano) debe rechazarse: el generador lo
    excluiría de todas las combinaciones sin ningún aviso.
    """
    datos_validos["estados"][0]["tipo_estado"] = "Simple"
    with pytest.raises(ErrorSesionInvalida, match="dañado"):
        sesion_desde_datos(datos_validos)


def test_estado_simple_con_grupo_lanza_error(datos_validos):
    datos_validos["estados"][0]["grupo"] = 1
    with pytest.raises(ErrorSesionInvalida, match="dañado"):
        sesion_desde_datos(datos_validos)


def test_estado_simple_con_opuesto_lanza_error(datos_validos):
    datos_validos["estados"][0]["incluir_opuesto"] = True
    with pytest.raises(ErrorSesionInvalida, match="dañado"):
        sesion_desde_datos(datos_validos)


def test_estado_direccional_sin_grupo_lanza_error(datos_validos):
    datos_validos["estados"][1] = {
        "nombre_estado": "SC", "tipo_carga": "L",
        "tipo_estado": "direccional", "grupo": None,
        "incluir_opuesto": True,
    }
    with pytest.raises(ErrorSesionInvalida, match="dañado"):
        sesion_desde_datos(datos_validos)


def test_estado_direccional_con_grupo_no_positivo_lanza_error(
    datos_validos,
):
    datos_validos["estados"][1] = {
        "nombre_estado": "SC", "tipo_carga": "L",
        "tipo_estado": "direccional", "grupo": 0,
        "incluir_opuesto": True,
    }
    with pytest.raises(ErrorSesionInvalida, match="dañado"):
        sesion_desde_datos(datos_validos)


def test_estado_direccional_valido_se_reconstruye(datos_validos):
    datos_validos["estados"][1] = {
        "nombre_estado": "SC", "tipo_carga": "L",
        "tipo_estado": "direccional", "grupo": 1,
        "incluir_opuesto": True,
    }
    datos_validos["descartes"] = []

    sesion2, _ = sesion_desde_datos(datos_validos)

    direccionales = [
        e for e in sesion2.estados_crudos
        if e.tipo_estado == "direccional"
    ]
    assert len(direccionales) == 1
    assert direccionales[0].grupo == 1


def test_sin_estados_guardados_lanza_error(datos_validos):
    datos_validos["estados"] = []
    with pytest.raises(ErrorSesionInvalida, match="estados de carga"):
        sesion_desde_datos(datos_validos)


def test_reglamento_embebido_invalido_lanza_error(datos_validos):
    datos_validos["reglamento_yaml"] = "metadata: [1, 2]"
    with pytest.raises(ErrorSesionInvalida, match="reglamento guardado"):
        sesion_desde_datos(datos_validos)


def test_reglamento_embebido_con_metadata_incompleta_lanza_error(
    datos_validos,
):
    """
    Un reglamento embebido cuya metadata no tiene las claves
    obligatorias debe producir el error claro de sesión inválida,
    nunca un error técnico que termine el programa.
    """
    datos_validos["reglamento_yaml"] = REGLAMENTO_YAML.replace(
        "  code_name: TEST\n", ""
    )
    with pytest.raises(ErrorSesionInvalida, match="reglamento guardado"):
        sesion_desde_datos(datos_validos)


def test_estados_invalidos_para_el_reglamento_lanzan_error(datos_validos):
    datos_validos["estados"][0]["tipo_carga"] = "X"
    with pytest.raises(ErrorSesionInvalida, match="no son válidos"):
        sesion_desde_datos(datos_validos)


# ── elecciones y descartes inválidos ──────────────────────────────────────────

def test_eleccion_de_parametro_inexistente_lanza_error(datos_validos):
    datos_validos["elecciones"] = [
        {"id_parametro": "Z", "valor": 1.0}
    ]
    with pytest.raises(ErrorSesionInvalida, match="no existe"):
        sesion_desde_datos(datos_validos)


def test_eleccion_con_valor_sin_opcion_lanza_error(datos_validos):
    datos_validos["elecciones"] = [
        {"id_parametro": "K", "valor": 0.7}
    ]
    with pytest.raises(ErrorSesionInvalida, match="no coincide"):
        sesion_desde_datos(datos_validos)


def test_eleccion_con_entero_gigante_no_tumba_el_programa(datos_validos):
    """
    JSON admite enteros de cualquier tamaño; compararlos contra las
    opciones no debe desbordar, sino caer en el error claro de opción
    inexistente.
    """
    datos_validos["elecciones"] = [
        {"id_parametro": "K", "valor": 10**400}
    ]
    with pytest.raises(ErrorSesionInvalida, match="no coincide"):
        sesion_desde_datos(datos_validos)


def test_elecciones_duplicadas_del_mismo_parametro_lanzan_error(
    datos_validos,
):
    datos_validos["elecciones"] = [
        {"id_parametro": "K", "valor": 0.5},
        {"id_parametro": "K", "valor": 1.0},
    ]
    with pytest.raises(ErrorSesionInvalida, match="más de una elección"):
        sesion_desde_datos(datos_validos)


def test_descarte_mal_tipado_lanza_error(datos_validos):
    datos_validos["descartes"] = ["3"]
    with pytest.raises(ErrorSesionInvalida, match="dañado"):
        sesion_desde_datos(datos_validos)


def test_descartes_huerfanos_avisan_y_se_ignoran(datos_validos):
    datos_validos["descartes"] = [998, 999]

    sesion2, avisos = sesion_desde_datos(datos_validos)

    assert len(avisos) == 1
    assert "2 descartes" in avisos[0]
    assert "ignoraron" in avisos[0]
    assert not any(
        c.descartada_por_usuario for c in sesion2.combinaciones
    )


def test_un_solo_descarte_huerfano_avisa_en_singular(datos_validos):
    datos_validos["descartes"] = [999]

    _, avisos = sesion_desde_datos(datos_validos)

    assert "1 descarte guardado no corresponde" in avisos[0]
    assert "ignoró" in avisos[0]


# ── Protecciones contra archivos desmedidos ───────────────────────────────────

def test_sesion_que_excede_el_limite_de_combinaciones_lanza_error(
    datos_validos, monkeypatch
):
    import dominio.sesion as modulo_sesion
    monkeypatch.setattr(modulo_sesion, "LIMITE_COMBINACIONES", 1)

    with pytest.raises(
        ErrorSesionInvalida, match="más combinaciones"
    ):
        sesion_desde_datos(datos_validos)


def test_reglamento_embebido_con_alias_yaml_lanza_error(datos_validos):
    datos_validos["reglamento_yaml"] = (
        "ancla: &a [1]\notra: *a\n" + REGLAMENTO_YAML
    )
    with pytest.raises(ErrorSesionInvalida, match="alias"):
        sesion_desde_datos(datos_validos)
