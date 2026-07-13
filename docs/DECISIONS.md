# Decisiones de arquitectura

Registro permanente de decisiones aprobadas. Solo se agregan filas, nunca
se eliminan.

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-07-13 | No implementar `freeze_panes` en la hoja "Resumen COMBOS" | La hoja tiene 5 tablas apiladas verticalmente con encabezados en filas distintas; congelar una fila fijaría el encabezado de una tabla mientras se scrollea otra, mostrando la columna equivocada fija en vez de ayudar. |
| 2026-07-13 | No optimizar la complejidad O(n²) de `dominio/preponderancia.marcar_superadas` ni el estilizado celda-por-celda de Excel | A la escala real del dominio (decenas a un par de cientos de combinaciones por corrida) el costo es imperceptible; optimizar agregaría complejidad sin beneficio medible. |
| 2026-07-13 | Mantener el easter egg de `cli/consola.py` (activado solo en la selección de reglamento) | Decisión del autor, no un descuido. Se reubicó la lógica de activación a una función propia (`pedir_seleccion_de_archivo`) para que `pedir_input` no tenga comportamiento oculto, sin eliminar la funcionalidad. |
| 2026-07-13 | Diferir la migración de objetos de dominio (dict → `dataclass`) a una sesión aparte | Cambio de mayor alcance (toca `dominio/`, `infraestructura/exportador.py` y tests). Condición de activación y detalle en `ROADMAP.md`. |
| 2026-07-13 | Bajar `requires-python` de `>=3.13` a `>=3.12` | Ampliar compatibilidad para usuarios que todavía están en 3.12 (soportada hasta octubre 2028). El proyecto no usa ninguna feature exclusiva de 3.13, y las dependencias (`openpyxl`, `pyyaml`, `rich`) corren en 3.12. |
| 2026-07-13 | Concentrar todos los objetos de dominio en un único módulo `dominio/modelos.py` en vez de un archivo por dataclass | Las cinco clases son chicas (≤10 campos) y se usan siempre en conjunto en el pipeline; un archivo único evita cinco imports por cada consumidor sin ocultar responsabilidades (el módulo tiene una única razón: definir la forma de los objetos que circulan por el dominio). |
| 2026-07-13 | Usar dataclasses mutables (no `frozen=True`) para los objetos de dominio | Los campos de marcado de `Combinacion` (`es_duplicada`, `esta_superada`, `descartada_por_usuario`, `nombre`) se completan a lo largo del pipeline; congelarlos obligaría a reemplazar el objeto en cada paso (con `replace`) y complicaría el flujo sin beneficio real a esta escala. |
