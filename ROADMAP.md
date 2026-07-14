# Roadmap

Mejoras identificadas y pospuestas a propósito. Cada una indica la condición
que la activa. Al implementar un ítem, se registra en `CHANGELOG.md` y se
quita de aquí.

---

## Registrar decisión sobre la política de destino del archivo Excel

**Identificado por:** auditoría `/auditoria` (2026-07-13, punto 4).

**Descripción:** hoy la CLI acepta cualquier ruta absoluta como destino de
exportación (incluidas rutas de sistema), sin whitelist. En una CLI local
operada por su único dueño esto es esperable. Cuando aparezcan la GUI y la
distribución a terceros, la premisa "único dueño" deja de ser válida y hay
que decidir la política (default a Documents/Desktop, validar que no sea
ruta de sistema, etc.) y registrarla en `docs/DECISIONS.md`.

**Condición de activación:** cuando se empiece a implementar la interfaz
gráfica o se planifique distribución a usuarios que no sean el autor.

---

## Split de `infraestructura/exportador.py` en submódulos

**Identificado por:** auditoría `/auditoria` (2026-07-13, punto 5).

**Descripción:** el archivo tiene 771 líneas y concentra el resumen, los
dos layouts de exportación (`por_componente`, `por_combinacion`) y las
envolventes. La estructura funciona bien mientras haya solo dos layouts,
pero agregar un tercer layout o un nuevo formato de salida (PDF, CSV, otro
software estructural como ETABS/RAM) va a inflar más un archivo ya
grande. Candidato natural a partirse en `exportador_resumen.py`,
`exportador_layouts.py`, `exportador_envolventes.py`.

**Condición de activación:** cuando se agregue un tercer layout de
exportación o un nuevo formato de salida distinto de Excel.

---

## Editor visual de reglamentos YAML

**Identificado por:** sesión `/evaluar` de mejoras mayores (2026-07-13).

**Descripción:** ventana para crear y editar reglamentos desde la aplicación
(formularios para combinaciones, validación en vivo, gestión de archivos).
Se evaluó y se descartó para esta etapa: crear un reglamento es un evento
raro (una vez por norma, no por proyecto) y el costo equivale a un segundo
producto. La necesidad se cubre con "duplicar reglamento como base" + edición
en el editor de texto del sistema + la validación existente de
`dominio/lector_yaml.py` al cargar (ver `docs/DECISIONS.md`).

**Condición de activación:** cuando un usuario tercero que no pueda editar
YAML a mano lo pida, o cuando crear/adaptar reglamentos se vuelva una tarea
recurrente (más de unas pocas veces al año).

---

## Exportación de resultados a PDF

**Identificado por:** sesión `/evaluar` de mejoras mayores (2026-07-13).

**Descripción:** exportar el resumen de combinaciones a PDF desde la pestaña
Resultados de la GUI. Requiere una dependencia pesada nueva y diseño de
reporte propio; Excel, CSV y HTML cubren el caso de uso inicial a costo
casi nulo.

**Condición de activación:** cuando la GUI esté publicada y estable, y algún
usuario pida el reporte en PDF.
