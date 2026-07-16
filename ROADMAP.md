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

---

## Endurecer sanitización de `software_name` para nombre de hoja Excel

**Identificado por:** auditoría `/auditoria` — revisor de seguridad
(2026-07-16, severidad baja).

**Descripción:** el `software_name` del YAML del reglamento se usa como
nombre de hoja de Excel sin validar contra las reglas de openpyxl (largo
máximo 31 caracteres, caracteres inválidos `\ / * ? [ ] :`). Un reglamento
propio mal armado hace fallar el export. Hoy con "único dueño" es un error
autoinfligido; con reglamentos importados de terceros deja de serlo.

**Condición de activación:** cuando se acepten reglamentos importados desde
usuarios que no sean el autor.

---

## Escritura atómica con nombre de temporal no predecible

**Identificado por:** auditoría `/auditoria` — revisor de seguridad
(2026-07-16, severidad baja).

**Descripción:** el archivo temporal usado en `infraestructura/guardado_excel.py`
tiene nombre determinista (`.name.tmp`). En directorios compartidos habilita
race por symlink. En una CLI local operada por su único dueño no hay
superficie explotable, pero si aparece un instalador que corra con
privilegios elevados o si el destino puede ser un directorio compartido, sí.

**Condición de activación:** cuando el software se distribuya con instalador
o cuando el destino pueda ser un directorio compartido.

---

## Anonimización del log de errores para soporte

**Identificado por:** auditoría `/auditoria` — revisor de seguridad
(2026-07-16, severidad baja).

**Descripción:** `main.py` escribe el traceback completo en
`combos_error.log` — incluye rutas absolutas (`OneDrive`, `ANTRA`, nombre
de usuario). El propio README pide enviar ese archivo a soporte. En un CLI
para el autor es aceptable; distribuido a terceros, expone datos del
usuario final. Además, la interpolación del traceback en el log no escapa
caracteres de control: un nombre de archivo malicioso puede inyectar líneas.

**Condición de activación:** al distribuir el software a terceros o al
publicar un mecanismo automático de envío de logs.
