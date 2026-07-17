from __future__ import annotations

from pathlib import Path

import pytest

from combos.dominio.lector_yaml import leer_reglamento

YAML_VALIDO = """
metadata:
  code_name: "TEST"
  code_version: "1"
  country: "Testland"
  description: "Reglamento de prueba"

permanent_load_types:
  - D

limit_states:
  ELU:
    name: "Estado límite último"
    prefix: "U"

load_types:
  D:
    name: "Permanente"
    description: "Carga permanente"
  L:
    name: "Viva"
    description: "Sobrecarga de uso"

combinations:
  ELU:
    - id: 1
      factors:
        D: 1.4
    - id: 2
      factors:
        D: 1.2
        L: 1.6
"""


def _escribir_yaml(tmp_path: Path, contenido: str) -> str:
    ruta = tmp_path / "reglamento.yaml"
    ruta.write_text(contenido, encoding="utf-8")
    return str(ruta)


YAML_CON_PARAMETROS = YAML_VALIDO + """
    - id: 3
      factors:
        D: 1.2
        L: { param: L_factor }

parameters:
  L_factor:
    name: "Factor de sobrecarga L"
    options:
      - label: "Destinos con sobrecarga alta"
        value: 1.0
      - label: "Resto de los destinos"
        value: 0.5
    default: 1.0
"""


def test_leer_reglamento_valido_devuelve_estructura_esperada(tmp_path):
    ruta = _escribir_yaml(tmp_path, YAML_VALIDO)

    reglamento = leer_reglamento(ruta)

    assert reglamento["metadata"]["code_name"] == "TEST"
    assert reglamento["permanent_load_types"] == ["D"]
    assert reglamento["limit_states"]["ELU"]["prefix"] == "U"
    assert len(reglamento["combinations"]["ELU"]) == 2
    factores_combo_2 = reglamento["combinations"]["ELU"][1]["factors"]
    assert factores_combo_2 == {"D": 1.2, "L": 1.6}


YAML_CON_NOMBRES = """
metadata:
  code_name: "TEST"
  code_version: "1"
  country: "Testland"
  description: "Reglamento de prueba"

permanent_load_types:
  - D

limit_states:
  ELU:
    name: "Estado límite último"
    prefix: "U"
  ELS:
    name: "Estado límite de servicio"
    prefix: "S"

load_types:
  D:
    name: "Permanente"
    description: "Carga permanente"
  L:
    name: "Viva"
    description: "Sobrecarga de uso"

combinations:
  ELU:
    - id: 1
      name: "U1.1"
      factors:
        D: 1.4
    - id: 2
      name: "U2.1"
      factors:
        D: 1.2
        L: 1.6
  ELS:
    - id: 1
      name: "S1.1"
      factors:
        D: 1.0
"""


def test_leer_reglamento_sin_parameters_devuelve_parametros_vacios(tmp_path):
    ruta = _escribir_yaml(tmp_path, YAML_VALIDO)

    reglamento = leer_reglamento(ruta)

    assert reglamento["parameters"] == {}


# ── Campo name e ids de combinaciones ─────────────────────────────────────────

def test_leer_reglamento_construye_nombres_y_admite_ids_repetidos_entre_estados(
    tmp_path,
):
    ruta = _escribir_yaml(tmp_path, YAML_CON_NOMBRES)

    reglamento = leer_reglamento(ruta)

    assert reglamento["combinations"]["ELU"][0]["name"] == "U1.1"
    assert reglamento["combinations"]["ELU"][1]["name"] == "U2.1"
    assert reglamento["combinations"]["ELS"][0]["name"] == "S1.1"
    assert reglamento["combinations"]["ELU"][0]["id"] == 1
    assert reglamento["combinations"]["ELS"][0]["id"] == 1


def test_leer_reglamento_sin_name_devuelve_none(tmp_path):
    ruta = _escribir_yaml(tmp_path, YAML_VALIDO)

    reglamento = leer_reglamento(ruta)

    assert reglamento["combinations"]["ELU"][0]["name"] is None


def test_leer_reglamento_name_numerico_se_convierte_a_texto(tmp_path):
    yaml_name_numerico = YAML_CON_NOMBRES.replace('name: "U1.1"', "name: 9.5")
    ruta = _escribir_yaml(tmp_path, yaml_name_numerico)

    reglamento = leer_reglamento(ruta)

    assert reglamento["combinations"]["ELU"][0]["name"] == "9.5"


def test_leer_reglamento_name_vacio_falla(tmp_path):
    yaml_name_vacio = YAML_CON_NOMBRES.replace('name: "U1.1"', 'name: "  "')
    ruta = _escribir_yaml(tmp_path, yaml_name_vacio)

    with pytest.raises(ValueError, match="vacía"):
        leer_reglamento(ruta)


def test_leer_reglamento_name_repetido_entre_estados_falla(tmp_path):
    yaml_name_repetido = YAML_CON_NOMBRES.replace(
        'name: "S1.1"', 'name: "U1.1"'
    )
    ruta = _escribir_yaml(tmp_path, yaml_name_repetido)

    with pytest.raises(ValueError, match="repetido"):
        leer_reglamento(ruta)


def test_leer_reglamento_id_duplicado_en_mismo_estado_falla(tmp_path):
    yaml_id_duplicado = YAML_VALIDO.replace("- id: 2", "- id: 1")
    ruta = _escribir_yaml(tmp_path, yaml_id_duplicado)

    with pytest.raises(ValueError, match="único dentro"):
        leer_reglamento(ruta)


def test_leer_reglamento_id_duplicado_con_tipos_mixtos_falla(tmp_path):
    yaml_id_mixto = YAML_VALIDO.replace('- id: 2', '- id: "1"')
    ruta = _escribir_yaml(tmp_path, yaml_id_mixto)

    with pytest.raises(ValueError, match="único dentro"):
        leer_reglamento(ruta)


def test_leer_reglamento_id_no_entero_falla_con_mensaje_claro(tmp_path):
    yaml_id_invalido = YAML_VALIDO.replace("- id: 2", "- id: abc")
    ruta = _escribir_yaml(tmp_path, yaml_id_invalido)

    with pytest.raises(ValueError, match="número entero"):
        leer_reglamento(ruta)


def test_leer_reglamento_name_no_escalar_falla(tmp_path):
    yaml_name_lista = YAML_CON_NOMBRES.replace(
        'name: "U1.1"', 'name: ["U1", "1"]'
    )
    ruta = _escribir_yaml(tmp_path, yaml_name_lista)

    with pytest.raises(ValueError, match="debe ser un texto"):
        leer_reglamento(ruta)


def test_leer_reglamento_archivo_inexistente_lanza_file_not_found(tmp_path):
    ruta_inexistente = str(tmp_path / "no_existe.yaml")

    with pytest.raises(FileNotFoundError):
        leer_reglamento(ruta_inexistente)


def test_leer_reglamento_yaml_con_sintaxis_invalida_lanza_value_error(tmp_path):
    ruta = _escribir_yaml(tmp_path, "metadata: [esto no es un mapeo válido: :")

    with pytest.raises(ValueError):
        leer_reglamento(ruta)


def test_leer_reglamento_con_raiz_que_no_es_mapeo_lanza_value_error(tmp_path):
    ruta = _escribir_yaml(tmp_path, "- una\n- lista\n- suelta\n")

    with pytest.raises(ValueError, match="estructura"):
        leer_reglamento(ruta)


def test_leer_reglamento_con_archivo_vacio_lanza_value_error(tmp_path):
    ruta = _escribir_yaml(tmp_path, "")

    with pytest.raises(ValueError, match="estructura"):
        leer_reglamento(ruta)


def test_leer_reglamento_sin_secciones_obligatorias_lanza_value_error(tmp_path):
    ruta = _escribir_yaml(tmp_path, "metadata:\n  code_name: TEST\n")

    with pytest.raises(ValueError, match="incompleto"):
        leer_reglamento(ruta)


def test_leer_reglamento_sin_permanent_load_types_lanza_value_error(tmp_path):
    yaml_sin_permanentes = YAML_VALIDO.replace(
        "permanent_load_types:\n  - D\n", "permanent_load_types: []\n"
    )
    ruta = _escribir_yaml(tmp_path, yaml_sin_permanentes)

    with pytest.raises(ValueError, match="permanent_load_types"):
        leer_reglamento(ruta)


def test_leer_reglamento_combinacion_sin_carga_permanente_lanza_value_error(
    tmp_path,
):
    yaml_sin_carga_permanente = YAML_VALIDO.replace(
        "        D: 1.4\n", "        L: 1.4\n"
    )
    ruta = _escribir_yaml(tmp_path, yaml_sin_carga_permanente)

    with pytest.raises(ValueError, match="carga permanente"):
        leer_reglamento(ruta)


def test_leer_reglamento_factor_no_positivo_lanza_value_error(tmp_path):
    yaml_factor_invalido = YAML_VALIDO.replace("D: 1.4", "D: 0")
    ruta = _escribir_yaml(tmp_path, yaml_factor_invalido)

    with pytest.raises(ValueError, match="mayores que cero"):
        leer_reglamento(ruta)


def test_leer_reglamento_tipo_de_carga_no_definido_lanza_value_error(tmp_path):
    yaml_tipo_desconocido = YAML_VALIDO.replace(
        "D: 1.2\n        L: 1.6", "X: 1.2"
    )
    ruta = _escribir_yaml(tmp_path, yaml_tipo_desconocido)

    with pytest.raises(ValueError, match="load_types"):
        leer_reglamento(ruta)


def test_leer_reglamento_factor_no_numerico_lanza_value_error(tmp_path):
    yaml_factor_texto = YAML_VALIDO.replace('D: 1.4', 'D: "alto"')
    ruta = _escribir_yaml(tmp_path, yaml_factor_texto)

    with pytest.raises(ValueError, match="número mayor que cero"):
        leer_reglamento(ruta)


def test_leer_reglamento_acumula_varios_errores_de_factores(tmp_path):
    yaml_dos_errores = YAML_VALIDO.replace("D: 1.4", "D: 0").replace(
        "L: 1.6", 'L: "alto"'
    )
    ruta = _escribir_yaml(tmp_path, yaml_dos_errores)

    with pytest.raises(ValueError, match="2 error"):
        leer_reglamento(ruta)


# ── Sección parameters ────────────────────────────────────────────────────────

def test_leer_reglamento_con_parametros_construye_la_seccion(tmp_path):
    ruta = _escribir_yaml(tmp_path, YAML_CON_PARAMETROS)

    reglamento = leer_reglamento(ruta)

    parametro = reglamento["parameters"]["L_factor"]
    assert parametro.id_parametro == "L_factor"
    assert parametro.nombre == "Factor de sobrecarga L"
    assert parametro.valor_default == 1.0
    assert [o.valor for o in parametro.opciones] == [1.0, 0.5]
    assert parametro.opciones[1].etiqueta == "Resto de los destinos"
    factores_combo_3 = reglamento["combinations"]["ELU"][2]["factors"]
    assert factores_combo_3["L"] == {"param": "L_factor"}


def test_leer_reglamento_referencia_a_parametro_inexistente_falla(tmp_path):
    yaml_referencia_rota = YAML_CON_PARAMETROS.replace(
        "L: { param: L_factor }", "L: { param: otro }"
    )
    ruta = _escribir_yaml(tmp_path, yaml_referencia_rota)

    with pytest.raises(ValueError, match="no está definido"):
        leer_reglamento(ruta)


def test_leer_reglamento_parametro_sin_referencias_falla(tmp_path):
    yaml_parametro_sin_uso = YAML_CON_PARAMETROS.replace(
        "L: { param: L_factor }", "L: 1.0"
    )
    ruta = _escribir_yaml(tmp_path, yaml_parametro_sin_uso)

    with pytest.raises(ValueError, match="ninguna combinación"):
        leer_reglamento(ruta)


def test_leer_reglamento_referencia_con_clave_desconocida_falla(tmp_path):
    yaml_clave_rota = YAML_CON_PARAMETROS.replace(
        "L: { param: L_factor }", "L: { parm: L_factor }"
    )
    ruta = _escribir_yaml(tmp_path, yaml_clave_rota)

    with pytest.raises(ValueError, match="forma esperada"):
        leer_reglamento(ruta)


def test_leer_reglamento_default_que_no_es_una_opcion_falla(tmp_path):
    yaml_default_invalido = YAML_CON_PARAMETROS.replace(
        "default: 1.0", "default: 0.7"
    )
    ruta = _escribir_yaml(tmp_path, yaml_default_invalido)

    with pytest.raises(ValueError, match="default"):
        leer_reglamento(ruta)


def test_leer_reglamento_opcion_con_valor_no_positivo_falla(tmp_path):
    yaml_valor_invalido = YAML_CON_PARAMETROS.replace(
        "value: 0.5", "value: 0"
    )
    ruta = _escribir_yaml(tmp_path, yaml_valor_invalido)

    with pytest.raises(ValueError, match="mayor que cero"):
        leer_reglamento(ruta)


def test_leer_reglamento_parametro_con_una_sola_opcion_falla(tmp_path):
    yaml_una_opcion = YAML_CON_PARAMETROS.replace(
        '      - label: "Resto de los destinos"\n        value: 0.5\n', ""
    )
    ruta = _escribir_yaml(tmp_path, yaml_una_opcion)

    with pytest.raises(ValueError, match="al menos dos opciones"):
        leer_reglamento(ruta)


def test_leer_reglamento_parametro_sin_nombre_falla(tmp_path):
    yaml_sin_nombre = YAML_CON_PARAMETROS.replace(
        '    name: "Factor de sobrecarga L"\n', ""
    )
    ruta = _escribir_yaml(tmp_path, yaml_sin_nombre)

    with pytest.raises(ValueError, match="name"):
        leer_reglamento(ruta)


def test_leer_reglamento_seccion_parameters_vacia_falla(tmp_path):
    indice_seccion = YAML_CON_PARAMETROS.index("parameters:")
    yaml_seccion_vacia = (
        YAML_CON_PARAMETROS[: indice_seccion + len("parameters:")]
        + " {}\n"
    )
    yaml_seccion_vacia = yaml_seccion_vacia.replace(
        "L: { param: L_factor }", "L: 1.0"
    )
    ruta = _escribir_yaml(tmp_path, yaml_seccion_vacia)

    with pytest.raises(ValueError, match="parameters"):
        leer_reglamento(ruta)


# ── Estructura de secciones internas ──────────────────────────────────────────

def test_leer_reglamento_metadata_como_lista_falla(tmp_path):
    yaml_metadata_lista = YAML_VALIDO.replace(
        'metadata:\n  code_name: "TEST"\n  code_version: "1"\n  '
        'country: "Testland"\n  description: "Reglamento de prueba"\n',
        "metadata:\n  - una\n  - lista\n",
    )
    ruta = _escribir_yaml(tmp_path, yaml_metadata_lista)

    with pytest.raises(ValueError, match="'metadata'"):
        leer_reglamento(ruta)


def test_leer_reglamento_combinations_como_lista_falla(tmp_path):
    yaml_combinations_lista = YAML_VALIDO.replace(
        "combinations:\n  ELU:", "combinations:\n  - ELU:"
    )
    ruta = _escribir_yaml(tmp_path, yaml_combinations_lista)

    with pytest.raises(ValueError, match="'combinations'"):
        leer_reglamento(ruta)


def test_leer_reglamento_load_types_como_lista_falla(tmp_path):
    yaml_load_types_lista = YAML_VALIDO.replace(
        'load_types:\n  D:\n    name: "Permanente"\n    '
        'description: "Carga permanente"\n  L:\n    name: "Viva"\n    '
        'description: "Sobrecarga de uso"\n',
        "load_types:\n  - D\n  - L\n",
    )
    ruta = _escribir_yaml(tmp_path, yaml_load_types_lista)

    with pytest.raises(ValueError, match="'load_types'"):
        leer_reglamento(ruta)


def test_leer_reglamento_permanent_load_types_como_mapeo_falla(tmp_path):
    yaml_permanentes_mapeo = YAML_VALIDO.replace(
        "permanent_load_types:\n  - D\n",
        "permanent_load_types:\n  D: sí\n",
    )
    ruta = _escribir_yaml(tmp_path, yaml_permanentes_mapeo)

    with pytest.raises(ValueError, match="'permanent_load_types'"):
        leer_reglamento(ruta)


def test_leer_reglamento_limit_state_sin_name_falla(tmp_path):
    yaml_estado_sin_name = YAML_VALIDO.replace(
        '  ELU:\n    name: "Estado límite último"\n    prefix: "U"\n',
        '  ELU:\n    prefix: "U"\n',
    )
    ruta = _escribir_yaml(tmp_path, yaml_estado_sin_name)

    with pytest.raises(ValueError, match="'name'"):
        leer_reglamento(ruta)


def test_leer_reglamento_load_type_sin_description_falla(tmp_path):
    yaml_tipo_sin_desc = YAML_VALIDO.replace(
        '  D:\n    name: "Permanente"\n    description: "Carga permanente"\n',
        '  D:\n    name: "Permanente"\n',
    )
    ruta = _escribir_yaml(tmp_path, yaml_tipo_sin_desc)

    with pytest.raises(ValueError, match="'description'"):
        leer_reglamento(ruta)


def test_leer_reglamento_estado_de_combinations_con_valor_no_lista_falla(
    tmp_path,
):
    yaml_estado_mapeo = YAML_VALIDO.replace(
        "combinations:\n"
        "  ELU:\n"
        "    - id: 1\n"
        "      factors:\n"
        "        D: 1.4\n"
        "    - id: 2\n"
        "      factors:\n"
        "        D: 1.2\n"
        "        L: 1.6\n",
        "combinations:\n"
        "  ELU:\n"
        "    id: 1\n"
        "    factors:\n"
        "      D: 1.4\n",
    )
    ruta = _escribir_yaml(tmp_path, yaml_estado_mapeo)

    with pytest.raises(ValueError, match="lista"):
        leer_reglamento(ruta)


def test_leer_reglamento_combinacion_sin_factors_falla(tmp_path):
    yaml_sin_factors = YAML_VALIDO.replace(
        "    - id: 1\n      factors:\n        D: 1.4\n",
        "    - id: 1\n",
    )
    ruta = _escribir_yaml(tmp_path, yaml_sin_factors)

    with pytest.raises(ValueError, match="'factors'"):
        leer_reglamento(ruta)


def test_leer_reglamento_combinacion_con_factors_como_lista_falla(tmp_path):
    yaml_factors_lista = YAML_VALIDO.replace(
        "      factors:\n        D: 1.4\n",
        "      factors:\n        - D\n",
    )
    ruta = _escribir_yaml(tmp_path, yaml_factors_lista)

    with pytest.raises(ValueError, match="'factors'"):
        leer_reglamento(ruta)


# ── Metadata ──────────────────────────────────────────────────────────────────

def test_leer_reglamento_metadata_sin_clave_obligatoria_falla(tmp_path):
    yaml_sin_country = YAML_VALIDO.replace('  country: "Testland"\n', "")
    ruta = _escribir_yaml(tmp_path, yaml_sin_country)

    with pytest.raises(ValueError, match="metadata"):
        leer_reglamento(ruta)


def test_leer_reglamento_metadata_con_valor_no_escalar_falla(tmp_path):
    yaml_con_lista = YAML_VALIDO.replace(
        '  code_name: "TEST"', "  code_name: [2005, 2024]"
    )
    ruta = _escribir_yaml(tmp_path, yaml_con_lista)

    with pytest.raises(ValueError, match="code_name"):
        leer_reglamento(ruta)


def test_leer_reglamento_metadata_numerica_se_convierte_a_texto(tmp_path):
    """
    Un code_name numérico (ej. 2005 sin comillas) es YAML legítimo:
    aguas abajo (pantalla, Excel, sesiones .combos) siempre debe llegar
    como texto para que ningún consumidor falle por el tipo.
    """
    yaml_numerico = YAML_VALIDO.replace(
        '  code_name: "TEST"', "  code_name: 2005"
    )
    ruta = _escribir_yaml(tmp_path, yaml_numerico)

    reglamento = leer_reglamento(ruta)

    assert reglamento["metadata"]["code_name"] == "2005"


# ── Ids que no son texto ──────────────────────────────────────────────────────
# YAML admite claves de cualquier tipo (`1:` sin comillas es un entero);
# los ids del reglamento deben ser texto para que las comparaciones y
# los mensajes aguas abajo nunca fallen con un error técnico.

def test_leer_reglamento_factors_con_clave_numerica_falla(tmp_path):
    yaml_clave_numerica = YAML_VALIDO.replace(
        "      factors:\n        D: 1.4\n",
        "      factors:\n        D: 1.4\n        1: 9.9\n",
    )
    ruta = _escribir_yaml(tmp_path, yaml_clave_numerica)

    with pytest.raises(ValueError, match="comillas"):
        leer_reglamento(ruta)


def test_leer_reglamento_load_types_con_clave_numerica_falla(tmp_path):
    yaml_clave_numerica = YAML_VALIDO.replace(
        "load_types:\n  D:\n",
        "load_types:\n  2:\n    name: \"Rara\"\n"
        "    description: \"Clave numérica\"\n  D:\n",
    )
    ruta = _escribir_yaml(tmp_path, yaml_clave_numerica)

    with pytest.raises(ValueError, match="comillas"):
        leer_reglamento(ruta)


def test_leer_reglamento_permanentes_con_elemento_no_textual_falla(
    tmp_path,
):
    yaml_elemento_raro = YAML_VALIDO.replace(
        "permanent_load_types:\n  - D\n",
        "permanent_load_types:\n  - D\n  - {x: 1}\n",
    )
    ruta = _escribir_yaml(tmp_path, yaml_elemento_raro)

    with pytest.raises(ValueError, match="permanent_load_types"):
        leer_reglamento(ruta)


def test_leer_reglamento_referencia_con_claves_mixtas_da_error_claro(
    tmp_path,
):
    yaml_referencia_rara = YAML_CON_PARAMETROS.replace(
        "        L: { param: L_factor }",
        "        L: { param: L_factor, 1: 2 }",
    )
    ruta = _escribir_yaml(tmp_path, yaml_referencia_rara)

    with pytest.raises(ValueError, match="forma esperada"):
        leer_reglamento(ruta)


def test_leer_reglamento_parameters_con_clave_numerica_falla(tmp_path):
    yaml_parametro_numerico = YAML_CON_PARAMETROS.replace(
        "parameters:\n  L_factor:", "parameters:\n  7:"
    ).replace("{ param: L_factor }", "{ param: 7 }")
    ruta = _escribir_yaml(tmp_path, yaml_parametro_numerico)

    with pytest.raises(ValueError, match="comillas"):
        leer_reglamento(ruta)


# ── Protecciones contra archivos desmedidos u hostiles ────────────────────────

def test_leer_reglamento_con_alias_yaml_falla(tmp_path):
    ruta = _escribir_yaml(
        tmp_path, "ancla: &a [1]\notra: *a\n" + YAML_VALIDO
    )

    with pytest.raises(ValueError, match="alias"):
        leer_reglamento(ruta)


def test_leer_reglamento_archivo_gigante_falla(tmp_path, monkeypatch):
    import combos.dominio.lector_yaml as modulo_lector
    monkeypatch.setattr(modulo_lector, "MAX_BYTES_YAML", 10)
    ruta = _escribir_yaml(tmp_path, YAML_VALIDO)

    with pytest.raises(ValueError, match="tamaño"):
        leer_reglamento(ruta)


def test_leer_reglamento_id_con_doble_guion_da_error_claro(tmp_path):
    yaml_id_raro = YAML_VALIDO.replace("- id: 2", '- id: "--3"')
    ruta = _escribir_yaml(tmp_path, yaml_id_raro)

    with pytest.raises(ValueError, match="entero"):
        leer_reglamento(ruta)


def test_leer_reglamento_id_de_tipo_con_caracteres_raros_falla(tmp_path):
    yaml_tipo_raro = YAML_VALIDO.replace(
        "load_types:\n  D:\n", 'load_types:\n  "D,X":\n'
    )
    ruta = _escribir_yaml(tmp_path, yaml_tipo_raro)

    with pytest.raises(ValueError, match="caracteres no admitidos"):
        leer_reglamento(ruta)
