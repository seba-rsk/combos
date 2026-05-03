# Changelog

Todos los cambios notables de COMBOS se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).
El versionado sigue [Semantic Versioning](https://semver.org/lang/es/).

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
