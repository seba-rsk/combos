# Changelog

Todos los cambios notables de COMBOS se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).
El versionado sigue [Semantic Versioning](https://semver.org/lang/es/).

---

## [Unreleased]

### Agregado

- **Parámetros del reglamento** (sección opcional `parameters` del YAML): un reglamento puede declarar factores alternativos que dependen de una propiedad del proyecto (ej. el factor de la sobrecarga L según el destino del edificio) como parámetros con opciones etiquetadas y un valor por defecto. COMBOS pregunta cada parámetro una sola vez por corrida con un menú numerado (Enter acepta el default) — después de leer y validar los estados de carga del usuario, y solo los parámetros cuyos tipos de carga referenciados tienen al menos un estado ingresado; los que no aplican se resuelven con su default sin preguntar ni registrarse, porque no participan de ninguna combinación generada. Cada referencia `{ param: <id> }` se reemplaza por el valor elegido antes de generar las combinaciones, y la elección del usuario queda registrada en el encabezado del Excel exportado para trazabilidad. La extensión es retrocompatible: los reglamentos existentes con factores numéricos siguen funcionando sin cambios. Nuevo módulo `dominio/parametros.py` (resolución pura), dataclasses `ParametroReglamento`/`OpcionParametro`/`EleccionParametro` en `dominio/modelos.py`, y validación completa de la sección en `dominio/lector_yaml.py` (opciones mínimas, valores positivos, default válido, referencias rotas y parámetros sin uso producen error claro).
- Perfil `profiles/cirsoc2005_actualizado.yaml`: copia del CIRSOC 2005 que aplica la excepción del reglamento que permite reducir el factor de L de 1.0 a 0.5 en las combinaciones U3 a U5 del ELU según el destino del edificio, usando el parámetro `L_factor`. El `cirsoc2005.yaml` original queda intacto. Dos tests de integración verifican que con la opción default el perfil produce exactamente los mismos resultados que el original, y que la opción reducida solo afecta las combinaciones habilitadas por la excepción.
- La validación de factores del reglamento ahora rechaza con mensaje claro los valores no numéricos (ej. `D: "alto"`); antes producían un error técnico sin explicación.
- **Designación normativa de las combinaciones** (campo opcional `name` en el YAML): cada combinación puede llevar el nombre con el que la norma la identifica (ej. `"U3.1"`), en texto libre. El menú de parámetros lo usa en la línea nueva "Afecta a", que muestra qué combinaciones del reglamento toca cada parámetro agrupadas por estado límite y en la nomenclatura de la norma (las combinaciones sin `name` se muestran como `id N`). Validación: `name` no vacío y único en todo el reglamento, incluso entre estados límite. El perfil `cirsoc2005_actualizado.yaml` incorpora las 26 designaciones reales (U1.1–U7.1, S1.1–S3.1), que hasta ahora vivían solo como comentarios. Surgido de `/evaluar` sobre la idea de un campo de agrupamiento "variante": la designación textual resuelve lo mismo sin tocar la lógica interna.
- Validación nueva: el `id` de cada combinación debe ser único dentro de su estado límite (entre estados límite distintos puede repetirse, como ya hacen los perfiles CIRSOC). Antes un id duplicado no se detectaba y corrompía silenciosamente el agrupamiento del nombrado en la exportación (dos combinaciones distintas se fusionaban como variantes de una sola).
- Revisión automática en GitHub Actions (`.github/workflows/ci.yml`): en cada push y pull request contra `main`, el CI corre lint (`ruff`), tests (`pytest`), seguridad estática (`bandit`) y auditoría de dependencias vulnerables (`pip-audit`) sobre una matriz de Python 3.12, 3.13 y 3.14 — las tres versiones que el `pyproject.toml` declara soportar. Se agregaron `ruff`, `bandit` y `pip-audit` a las dependencias opcionales de desarrollo, y una sección `[tool.ruff]` al `pyproject.toml` (línea de 80, reglas `E`/`F`/`W`/`I`).
- Actualizaciones mensuales agrupadas de dependencias y de las propias acciones del workflow vía Dependabot (`.github/dependabot.yml`). Las alertas de seguridad de dependencias siguen llegando al instante como canal aparte de GitHub, sin esperar el ciclo mensual.
- Badge de estado de CI en la cabecera del `README.md`.

### Interfaz

- Al elegir la ruta de destino para la plantilla Excel, si el archivo ya existe se pide confirmación antes de sobreescribir (mismo comportamiento que la ruta de exportación). Antes, la generación de plantilla sobreescribía silenciosamente cualquier archivo previo con el mismo nombre.

### Seguridad

- Se cierran los últimos huecos de cobertura de la neutralización anti-fórmulas en el Excel exportado, detectados por la auditoría del 2026-07-15: los ids de estado límite, el "Nombre asignado" (cuyo prefijo viene del campo `prefix` del YAML), la columna "Componentes" y los títulos definidos en el YAML del exportador (columnas de layouts, tabla de nombres y tabla de envolventes) ahora pasan por `neutralizar_texto_libre`. Verificado con un reglamento y un exportador hostiles (todos los textos libres empezando con `=`): el archivo generado no contiene ninguna celda interpretable como fórmula.
- Se uniforma el escape de markup de rich en la consola: los mensajes que interpolan texto libre (errores de validación del YAML y de la planilla, listas de archivos, mensajes de éxito/procesando, encabezados de estado límite en las tablas) se escapan en el punto de impresión. La política queda documentada en `cli/consola.py`.
- Un YAML de reglamento cuya raíz no es un conjunto de secciones (una lista suelta, un archivo vacío) y un perfil de exportación vacío o mal estructurado ahora producen el mensaje claro de "formato inválido" en vez de caer al error genérico de soporte. Se agregaron validaciones de estructura al perfil de exportación (`metadata`, `hoja`, `tabla_combinaciones`, `columnas`).
- Se completa la neutralización de textos libres antes de escribirlos en las celdas de Excel: el nombre de cada combinación y el nombre de cada envolvente también pasan por `neutralizar_texto_libre`. Antes solo se neutralizaban los nombres de estados de carga; un YAML de reglamento hostil (con un `prefix` que empezara con `=`, `+`, `-` o `@`) podía inyectar una fórmula al archivo generado al abrirlo desde Excel. El uso local individual actual no está expuesto, pero el proyecto habilita compartir YAML de reglamento entre colegas, así que el fix cierra el hallazgo antes de que crezca. Detectado por revisión de seguridad del 2026-07-14.
- Validación de estructura de las secciones internas del YAML de reglamento: `metadata`, `limit_states`, `load_types` y `combinations` ahora se rechazan con mensaje claro si no son mapeos, si un estado límite o un tipo de carga no es un mapeo con `name`/`prefix` (o `name`/`description`), si el valor de un estado en `combinations` no es una lista, o si una combinación no tiene `id` o `factors` con la estructura esperada. Antes, un YAML mal armado producía un error técnico interno que el usuario recibía como "Ocurrió un error inesperado en COMBOS — enviá el log a soporte". Detectado por la auditoría del 2026-07-16 (hallazgo 1 del revisor de seguridad). Nueve tests nuevos en `test_lector_yaml.py` (105 en total).

### Refactor

- **Objeto de sesión** (ítem 2 del plan post-v1.1.0): el estado de una corrida — reglamento crudo y resuelto, perfil, elecciones de parámetros, estados crudos y enriquecidos, combinaciones — ahora vive en la dataclass `Sesion` del nuevo módulo `dominio/sesion.py`, junto con las operaciones del pipeline (`procesar`, `aplicar_descartes`, `combinaciones_resultantes`, `combinaciones_superadas`). `cli/flujo.py` dejó de encadenar hasta seis parámetros entre pasos y quedó reducido a entrada/salida: cada paso completa la sesión y la lógica vive en dominio. `exportar` pasó de diez parámetros a cinco (recibe la sesión). El filtro "ni duplicada ni descartada", repetido en cinco lugares, quedó en una única función de dominio. La sesión conserva por separado el reglamento crudo (con las referencias `{param: X}` originales) y el resuelto (con los factores ya numéricos), y la resolución de parámetros siempre parte del crudo — prerequisito del formato `.combos` (ítem 3), que necesita el crudo para regenerar combinaciones al reabrir. Sin ningún cambio de comportamiento visible: verificado con la suite completa y comparando el Excel exportado antes y después del refactor celda por celda (idéntico, salvo la fecha). Es el prerequisito común del formato `.combos` (ítem 3) y de la GUI (ítem 5): ambos consumirán estas mismas funciones sin conocer el orden interno del pipeline. 10 tests nuevos (96 en total).

### Diseño y calidad

- Auditoría completa del 2026-07-15 aplicada: se agregaron docstrings a las 31 funciones públicas de presentación que no los tenían (`cli/consola.py`, `infraestructura/estilos_excel.py`, `main.py`, `cli/flujo.py:ejecutar_flujo`); `escribir_encabezado_programa` (112 líneas) se partió en helpers por bloque (título, fila de metadata, bloque de reglamento) quedando en 38; y los valores mágicos sueltos pasaron a constantes con nombre (`PAUSA_SEPARADOR_SEGUNDOS`, `ANCHO_SEPARADOR_ESTADO`, `FORMATO_TIMESTAMP_LOG` en `cli/constantes.py`, `MAX_CARACTERES_NOMBRE_HOJA` en el exportador).
- Auditoría completa del 2026-07-16 aplicada: se partieron las cinco funciones que excedían las 30 líneas del estándar sin aportar lógica adicional. `mostrar_tabla_resumen` (55) quedó en 12 líneas apoyada en `_agrupar_por_estado_limite` + `_mostrar_grupo_de_estado_limite` + `_construir_tabla_pagina`. Los dos `_pedir_ruta_destino_*` (55 y 56) quedaron reducidos a un armado de ruta por defecto + delegación en un helper compartido `_pedir_ruta_destino_excel` que reutiliza `_leer_ruta_excel_por_consola` y `_confirmar_destino_excel`. `_validar_config_exportador` (63) se dividió en tres validaciones jerárquicas (`_validar_config_exportador` + `_validar_layout_tabla_combinaciones` + `_validar_columnas_por_componente`). `_validar_nombres_de_combinaciones` (38) delega ahora en `_validar_nombre_de_combinacion` por combinación. Sin cambio de comportamiento (105 tests siguen pasando).
- Se elimina de `KNOWN_ISSUES.md` la limitación "Combinaciones con factores alternativos no soportadas": la resuelve la sección `parameters` del YAML (ver Agregado).

### Cambiado

- Se elimina `requirements.txt` para dejar `pyproject.toml` como única fuente de verdad de dependencias. Para instalar desde el código fuente, `pip install .` (o `pip install -e ".[dev]"` para desarrollo) reemplaza el uso anterior de `pip install -r requirements.txt`.

### Corregido

- Se corrige la referencia "Lo que COMBOS no hace en v1.0" en el `README.md` — el proyecto está en v1.1.0. El texto pasa a "Lo que COMBOS no hace en esta versión" para que la nota no vuelva a envejecer con cada release.
- Se elimina un bloque de código comentado en `cli/consola.py` (5 líneas dentro de la función del easter egg) que había quedado como versión alternativa descartada del panel.

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
