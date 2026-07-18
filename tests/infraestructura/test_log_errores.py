"""Tests de la escritura del log técnico de errores."""

from combos.infraestructura.log_errores import (
    MAX_BYTES_LOG,
    anexar_entrada_log,
    sanear_texto_log,
)


class TestSanearTextoLog:
    def test_texto_normal_queda_igual(self):
        texto = "ValueError: la carga no puede ser negativa (fila 12)"
        assert sanear_texto_log(texto) == texto

    def test_conserva_saltos_de_linea(self):
        texto = "línea 1\nlínea 2\n"
        assert sanear_texto_log(texto) == texto

    def test_reemplaza_caracteres_de_control(self):
        hostil = "archivo\r\x1b[2Jfalso\x00.yaml"
        saneado = sanear_texto_log(hostil)
        assert "\r" not in saneado
        assert "\x1b" not in saneado
        assert "\x00" not in saneado
        assert "archivo" in saneado
        assert "falso" in saneado


class TestAnexarEntradaLog:
    def test_crea_carpeta_y_escribe_la_entrada(self, tmp_path):
        ruta_log = tmp_path / "carpeta_nueva" / "combos_error.log"

        resultado = anexar_entrada_log(
            ruta_log, "error de prueba", "TypeError: detalle"
        )

        assert resultado is True
        contenido = ruta_log.read_text(encoding="utf-8")
        assert "COMBOS v" in contenido
        assert "error de prueba" in contenido
        assert "TypeError: detalle" in contenido

    def test_agrega_sin_borrar_las_entradas_anteriores(self, tmp_path):
        ruta_log = tmp_path / "combos_error.log"

        anexar_entrada_log(ruta_log, "primera", "cuerpo 1")
        anexar_entrada_log(ruta_log, "segunda", "cuerpo 2")

        contenido = ruta_log.read_text(encoding="utf-8")
        assert "primera" in contenido
        assert "segunda" in contenido

    def test_sanea_el_contexto_y_el_cuerpo(self, tmp_path):
        ruta_log = tmp_path / "combos_error.log"

        anexar_entrada_log(
            ruta_log, "contexto\rhostil", "cuerpo\x1bhostil"
        )

        contenido = ruta_log.read_text(encoding="utf-8")
        assert "\r" not in contenido
        assert "\x1b" not in contenido

    def test_el_contexto_no_admite_saltos_de_linea(self, tmp_path):
        # El encabezado de cada entrada es una única línea por diseño:
        # un contexto con "\n" no debe poder inyectar líneas en él,
        # aunque el cuerpo sí conserve sus saltos.
        ruta_log = tmp_path / "combos_error.log"

        anexar_entrada_log(
            ruta_log, "contexto\ninyectado", "línea 1\nlínea 2"
        )

        contenido = ruta_log.read_text(encoding="utf-8")
        assert "contexto\ninyectado" not in contenido
        assert "contexto�inyectado" in contenido
        assert "línea 1\nlínea 2" in contenido

    def test_recorta_el_log_conservando_lo_reciente(self, tmp_path):
        ruta_log = tmp_path / "combos_error.log"
        ruta_log.write_text(
            "viejo\n" + "x" * (MAX_BYTES_LOG + 1000), encoding="utf-8"
        )

        anexar_entrada_log(ruta_log, "entrada nueva", "cuerpo nuevo")

        assert ruta_log.stat().st_size < MAX_BYTES_LOG
        contenido = ruta_log.read_text(encoding="utf-8")
        assert "entrada nueva" in contenido
        assert "eliminadas por tamaño" in contenido
        assert not contenido.startswith("viejo")

    def test_devuelve_false_si_no_puede_escribir(self, tmp_path):
        # El "directorio" padre del log es en realidad un archivo:
        # crear la carpeta falla con OSError y la función debe
        # devolver False sin propagar la excepción.
        bloqueo = tmp_path / "ocupado"
        bloqueo.write_text("soy un archivo", encoding="utf-8")
        ruta_log = bloqueo / "combos_error.log"

        resultado = anexar_entrada_log(ruta_log, "contexto", "cuerpo")

        assert resultado is False
