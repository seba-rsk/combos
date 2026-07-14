# Changelog

Todos los cambios notables de COMBOS se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).
El versionado sigue [Semantic Versioning](https://semver.org/lang/es/).

---

## [Unreleased]

(cambios en desarrollo que todavía no tienen versión asignada)

---

## [1.1.0] — 2026-07-13

### Cambiado

- `pyproject.toml`: se bajó `requires-python` de `>=3.13` a `>=3.12` para ampliar la compatibilidad con usuarios que todavía están en Python 3.12 (soportada hasta octubre 2028). El proyecto no usa ninguna feature exclusiva de 3.13 y las dependencias (`openpyxl`, `pyyaml`, `rich`) corren en 3.12. Verificado con la suite completa (44 tests) en un venv 3.12.

### Agregado

- Tests unitarios con `pytest` para los cinco módulos de `dominio/` (`lector_yaml`, `lector_plantilla`, `generador`, `duplicados`, `preponderancia`) y `formateador`/`envolventes`, cubriendo casos esperados, casos borde y condiciones de error (44 tests). Se agregó un test de integración (`tests/test_integracion_cirsoc2005.py`, marcado `integration`) que reproduce el ejemplo paso a paso del README contra el reglamento real CIRSOC 2005. `pytest` se agregó como dependencia opcional de desarrollo en `pyproject.toml`. Resuelve la limitación documentada en `KNOWN_ISSUES.md` (removida).

### Interfaz

- Los mensajes de error mostrados al usuario cuando falla la apertura de la planilla Excel o la lectura del perfil de exportación YAML ya no incluyen la jerga técnica de la librería subyacente (`openpyxl`, `pyyaml`). En su lugar, el usuario ve una explicación clara con qué revisar (que el archivo sea `.xlsx` válido y no esté abierto en otra ventana, o que el YAML tenga formato correcto). El detalle técnico original queda registrado en `combos_error.log` para que un pedido de soporte no pierda información. Se agregó `cli.flujo._loguear_error_tecnico` para reutilizar el patrón en futuros casos.
- Los nombres de archivo por defecto (`Input_COMBOS_*.xlsx`, `Output_COMBOS_*.xlsx`) ahora incluyen la fecha, para que corridas sucesivas no propongan siempre el mismo nombre y disparen confirmaciones de sobreescritura innecesarias.
- El Excel de salida ahora tiene una sección "RESUMEN EJECUTIVO" al principio de la hoja "Resumen COMBOS", con los totales por estado límite (generadas, duplicadas, superadas descartadas, resultantes) y un total general — antes había que recorrer las 5 tablas de detalle para reconstruir esos números.
- Todas las tablas de datos del Excel de salida (hoja de resumen y hoja de exportación, ambos layouts) ahora tienen filas alternas con un gris muy claro para facilitar la lectura horizontal.
- Las tablas largas de la consola ("Combinaciones resultantes" y "Combinaciones superadas") ahora se paginan cada `FILAS_POR_PAGINA` (20) filas, pidiendo Enter para seguir viendo el resto en vez de imprimir todo de una vez y perder el contexto hacia arriba en la terminal.
- Si no queda ninguna combinación resultante para exportar, COMBOS ahora avisa explícitamente y pregunta si el usuario quiere elegir un exportador igualmente, en vez de llevarlo directo a esa pantalla sin avisarle.
- Al descartar combinaciones superadas, COMBOS ahora muestra qué se va a descartar y pide confirmación antes de aplicarlo; si el usuario se arrepiente, puede volver a elegir sin reiniciar el programa. No agrega fricción cuando no se descarta nada (Enter = ninguna).

### Corregido

- `pyproject.toml`: `build-backend` apuntaba a un módulo inexistente (`setuptools.backends.legacy:build`), lo que rompía `pip install -e .`. Corregido a `setuptools.build_meta`.
- `infraestructura/exportador.py`: los valores de "Nombre del estado" (texto libre ingresado por el usuario) se escribían sin sanitizar en las celdas del Excel exportado. Un nombre que empezara con `=`, `+`, `-` o `@` podía interpretarse como fórmula al abrir el archivo. Se neutralizan esos valores antes de escribirlos.
- La sanitización anterior no cubría los campos de metadata del reglamento YAML (`code_name`, `code_version`, `country`, `description`, tipos de carga y `nombre_perfil`), que también pueden venir de un archivo compartido por terceros. Se extendió a `infraestructura/exportador.py` (incluidas las columnas "Tipo de carga" y "Nombre de grupo") e `infraestructura/generador_plantilla.py` (incluido el panel de referencia de la plantilla), y se centralizó la función `neutralizar_texto_libre` en el nuevo módulo `infraestructura/sanitizacion_excel.py` para que ambos archivos compartan una única fuente de verdad.
- `infraestructura/exportador.py` e `infraestructura/generador_plantilla.py` guardaban el Excel directamente sobre la ruta final (`libro.save(ruta)`). Una interrupción a mitad de escritura podía corromper el archivo o perder la versión anterior al sobreescribir. Se agregó `infraestructura/guardado_excel.py` con un guardado atómico (archivo temporal + `os.replace`).
- `cli/flujo.py`: si el diálogo gráfico de selección de archivo fallaba por cualquier motivo, el error se descartaba en silencio (`except Exception: return None`) y el programa caía al input manual sin dejar rastro. Ahora el fallo queda registrado en el log de errores antes de continuar con el input manual.

### Diseño y eficiencia

- `_escribir_encabezado_programa` estaba duplicada casi entera en `infraestructura/exportador.py` (91 líneas) e `infraestructura/generador_plantilla.py` (86 líneas). Unificada en `infraestructura/encabezado_excel.py:escribir_encabezado_programa`, parametrizada por la etiqueta de hoja ("SALIDA DE DATOS" / "ENTRADA DE DATOS").
- Las cinco funciones de sección de `infraestructura/exportador.py` (`_escribir_seccion_datos_ingresados`, `_escribir_seccion_combinaciones_generadas`, `_escribir_seccion_combinaciones_resultantes`, `_escribir_seccion_duplicados_eliminados`, `_escribir_seccion_superadas`) repetían la misma estructura de ~40-46 líneas cada una. Unificadas en un único helper `_escribir_tabla_seccion`, con cada sección reducida a una función chica que solo define cómo armar el dict de valores de su fila.
- `cli/consola.py:pedir_input` tenía un parámetro (`al_activar`) cuyo comportamiento real (activar un mensaje oculto vía hash) no era evidente por su nombre. Se separó en `pedir_seleccion_de_archivo`, dejando `pedir_input` con una única responsabilidad (pedir texto y devolverlo).
- `infraestructura/config_interna.py`: se quitaron los campos de `CONFIG_PLANTILLA`/`CONFIG_RESUMEN` que nunca se leían (`version`, `imagen_empresa`, colores/fuentes/anchos placeholder, `estilos` completo) — prometían una configurabilidad que el código no implementa. Reservado para cuando se implemente de verdad.
- Evaluadas las recomendaciones de eficiencia (la complejidad O(n²) de `preponderancia.marcar_superadas`, y el estilizado celda-por-celda de Excel): no se tocaron, no son un problema real a la escala de este dominio (decenas a cientos de combinaciones).
- Registrada en `ROADMAP.md` la migración de los objetos de dominio (dict → `dataclass`) para una sesión aparte — cambio más grande, requiere tocar `dominio/`, `infraestructura/exportador.py` y los tests.

### Documentación

- Se agregaron docstrings faltantes en funciones públicas de `dominio/` e `infraestructura/`: `generar_combinaciones`, `marcar_duplicadas`, `marcar_superadas`, `formatear_componentes`, `leer_plantilla`, `leer_excel` y `exportar`.
- Se corrigió un typo ("psra" → "para") en `exportadores/sap2000.yaml`.
- Se corrigió el nombre de archivo documentado en `README.md` (`cirsoc2005_reduido.yaml` → `cirsoc2005_reducido.yaml`, coincidiendo con el archivo real).
- Se corrigió una afirmación incorrecta en `README.md` (sección "Combinaciones de carga"): decía que una combinación no se genera si le falta algún tipo de carga, pero el comportamiento real (confirmado con tests) es que se genera igual con menos términos, salvo que falten *todos* los tipos requeridos. Ahora coincide con `KNOWN_ISSUES.md`, que ya lo describía correctamente.
- Se actualizó la versión de Python declarada en `README.md` (badge y sección "Requisitos") y `CONTRIBUTING.md` (sección "Estilo de código") de 3.13+ a 3.12+, para alinearlas con el cambio de `requires-python` ya aplicado en `pyproject.toml`.

### Refactor

- Se creó `cli/constantes.py` y se reemplazaron los valores hardcodeados `"Desktop"`, `"Input_COMBOS_"` y `"Output_COMBOS_"` en `cli/flujo.py` por constantes compartidas.
- Se extrajeron las extensiones `.xlsx`/`.yaml` (repetidas ~9 veces en `cli/flujo.py`) a `EXTENSION_EXCEL`/`EXTENSION_YAML` en `cli/constantes.py`.
- Se eliminó un import sin usar (`formatear_componentes`) en `cli/flujo.py`.
- Se unificó la fórmula duplicada de ancho de columna del título (`round(len(...) * 1.4) + 2`), presente idéntica en `infraestructura/exportador.py` e `infraestructura/generador_plantilla.py`, en un único helper `ajustar_ancho_columna_titulo` en `infraestructura/estilos_excel.py`.
- Se limpió una rama muerta en `dominio/preponderancia.py:_obtener_clave_grupo` que leía `grupo_direccional`, un campo que `dominio/generador.py` nunca asigna (confirmado como comportamiento intencional: variantes direccionales distintas del mismo grupo no deben tratarse como comparables).
- Se migraron los cinco objetos de dominio que circulaban como `dict` (`EstadoCrudo`, `Estado`, `Componente`, `Combinacion`, `FilaEnvolvente`) a `@dataclass` en el nuevo módulo `dominio/modelos.py`. Un campo mal tipeado ahora falla en la construcción en vez de propagarse como una clave silenciosa (lo mismo que produjo el bug de `grupo_direccional` resuelto arriba). Se actualizaron todos los consumidores: `dominio/{generador,duplicados,preponderancia,lector_plantilla,envolventes,formateador}.py`, `infraestructura/{lector_excel,exportador}.py`, `cli/{flujo,consola}.py` y las fábricas de `tests/conftest.py`. Los tests de dominio y el test de integración CIRSOC 2005 se actualizaron para construir dataclasses y acceder por atributo; 44/44 tests pasan.
- Se reformateó todo el código fuente (`cli/`, `dominio/`, `infraestructura/`, `main.py`) para respetar el límite de 80 caracteres por línea, sin cambios de comportamiento. Verificado con pruebas de compilación y una corrida end-to-end completa del pipeline (plantilla → lectura → generación → exportación).

### Eliminado

- `config/plantilla.json` y `config/resumen.json`: archivos huérfanos que nunca se leían desde el código (la configuración real vive en `infraestructura/config_interna.py`) y duplicaban su contenido. Se actualizó la estructura documentada en `README.md` y la referencia en `KNOWN_ISSUES.md` en consecuencia.

---

## [1.0.0] — 2026-05-02

Lanzamiento inicial del MVP.

### Agregado

- Lectura de reglamentos de carga desde archivos YAML configurables.
- Generación automática de combinaciones de carga a partir del reglamento y los estados de carga del usuario.
- Soporte para estados de carga simples y direccionales (con variantes por dirección).
- Detección y marcado de combinaciones duplicadas.
- Análisis de preponderancia con seis reglas de comparación:
  - Regla 0: mismo estado límite.
  - Regla 1: mismo conjunto de tipos de carga.
  - Regla 2: mismo signo por estado.
  - Regla 3: coherencia de magnitud sobre cargas permanentes (con excepción para combinaciones de un único tipo de carga).
  - Regla 4: estados direccionales idénticos dentro de cada grupo.
  - Regla 5: dominancia estricta.
- Clave obligatoria `permanent_load_types` en el YAML del reglamento para identificar tipos de carga permanente gravitatoria.
- Validación exhaustiva del YAML del reglamento: secciones obligatorias, tipos de carga, factores, tipos permanentes y presencia de carga permanente en todas las combinaciones.
- Resolución interactiva de combinaciones superadas: el usuario decide cuáles descartar.
- Resumen en pantalla de las combinaciones resultantes antes de exportar.
- Exportación a Excel con hoja de resumen y hoja de datos para importar en SAP2000.
- Soporte para dos layouts de exportación: `por_componente` y `por_combinacion`.
- Generación de envolventes por estado límite incluida en la exportación.
- Generación de planilla Excel en blanco lista para completar.
- Interfaz de línea de comandos con soporte para diálogo de selección de archivos.
- Salida limpia con Ctrl+C en cualquier momento.
- Log automático de errores inesperados.
- Versión portable para Windows (sin necesidad de instalar Python).
