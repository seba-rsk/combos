from __future__ import annotations

from pathlib import Path

import pytest

from dominio.lector_yaml import leer_reglamento


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


def test_leer_reglamento_valido_devuelve_estructura_esperada(tmp_path):
    ruta = _escribir_yaml(tmp_path, YAML_VALIDO)

    reglamento = leer_reglamento(ruta)

    assert reglamento["metadata"]["code_name"] == "TEST"
    assert reglamento["permanent_load_types"] == ["D"]
    assert reglamento["limit_states"]["ELU"]["prefix"] == "U"
    assert len(reglamento["combinations"]["ELU"]) == 2
    factores_combo_2 = reglamento["combinations"]["ELU"][1]["factors"]
    assert factores_combo_2 == {"D": 1.2, "L": 1.6}


def test_leer_reglamento_archivo_inexistente_lanza_file_not_found(tmp_path):
    ruta_inexistente = str(tmp_path / "no_existe.yaml")

    with pytest.raises(FileNotFoundError):
        leer_reglamento(ruta_inexistente)


def test_leer_reglamento_yaml_con_sintaxis_invalida_lanza_value_error(tmp_path):
    ruta = _escribir_yaml(tmp_path, "metadata: [esto no es un mapeo válido: :")

    with pytest.raises(ValueError):
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
