# Roadmap

Mejoras identificadas y pospuestas a propósito. Cada una indica la condición
que la activa. Al implementar un ítem, se registra en `CHANGELOG.md` y se
quita de aquí.

---

## Split de `cli/flujo.py` en submódulos

**Identificado por:** auditoría `/auditoria` (2026-07-17).

**Descripción:** el archivo tiene ~950 líneas y concentra el menú de
inicio, los pasos del flujo, los helpers de diálogo/ruta y dos loggers
técnicos. Después de los refactors de los ítems 2 y 3 los pasos
quedaron cortos y la lógica se movió a `dominio/sesion.py`, así que el
archivo no duele hoy — pero cada feature nueva de la CLI lo hace
crecer. Candidato natural a partirse en `flujo_inicio.py`,
`flujo_procesamiento.py` y `flujo_exportacion.py`.

**Condición de activación:** al comenzar el ítem 5 (GUI). Decisión del
usuario (2026-07-18, tras la auditoría): el argumento `.combos` del
ítem 4B rozó la condición original ("una feature nueva de la CLI"),
pero partirlo recién cuando la GUI defina qué partes de la CLI
sobreviven evita hacerlo dos veces.

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

---

## Firma digital del ejecutable y del instalador

**Identificado por:** auditoría `/auditoria` — revisor de seguridad
(2026-07-18, severidad baja).

**Descripción:** ni `COMBOS.exe` ni el instalador van firmados
digitalmente: SmartScreen muestra "aplicación no reconocida" y quien
descarga no puede verificar la autenticidad por firma. Un certificado
de firma de código tiene costo anual real. Mitigación vigente y
gratuita: el SHA-256 del instalador se publica junto a cada release
(documentado en el README, sección "Construir el ejecutable y el
instalador").

**Condición de activación:** cuando la distribución supere el círculo
de confianza del autor (usuarios que no lo conocen personalmente), o
cuando la advertencia de SmartScreen se vuelva un problema real
reportado por usuarios.

---

## Anonimización de rutas del log de errores para soporte

**Identificado por:** auditoría `/auditoria` — revisor de seguridad
(2026-07-16, severidad baja). Parcialmente resuelto en el ítem 4B
(2026-07-17): los caracteres de control se sanean antes de escribir al
log (cierra la inyección de líneas falsas) y el archivo tiene tope de
tamaño. Queda pendiente solo la anonimización.

**Descripción:** el log de errores registra tracebacks completos, que
incluyen rutas absolutas con el nombre de usuario y la estructura de
carpetas de quien lo ejecuta. El README pide enviar ese archivo a
soporte: distribuido a terceros, expone datos del usuario final.

**Condición de activación:** cuando exista un canal de soporte real que
reciba logs de terceros, o al publicar un mecanismo automático de envío
de logs.
