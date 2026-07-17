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

## Split de `cli/flujo.py` en submódulos

**Identificado por:** auditoría `/auditoria` (2026-07-17).

**Descripción:** el archivo tiene 892 líneas y concentra el menú de
inicio, los doce pasos del flujo, seis helpers de diálogo/ruta y dos
loggers técnicos. Después de los refactors de los ítems 2 y 3 los pasos
quedaron cortos y la lógica se movió a `dominio/sesion.py`, así que el
archivo no duele hoy — pero cada feature nueva de la CLI lo va a hacer
crecer linealmente. Candidato natural a partirse en `flujo_inicio.py`,
`flujo_procesamiento.py`, `flujo_exportacion.py` y `logging_tecnico.py`.

**Condición de activación:** cuando se agregue una feature nueva a la
CLI que sume otro paso (o cuando el archivo cruce las 1000 líneas).

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

---

## Asociación de archivos `.combos` con el software en Windows

**Identificado por:** sesión de pruebas manuales (2026-07-17).

**Descripción:** que un doble click sobre un `.combos` abra COMBOS con
esa sesión ya cargada, y que el explorador de Windows muestre
`combos.ico` como icono del archivo. Son dos piezas complementarias:

1. **Instalador:** registra la asociación `.combos` en el registro de
   Windows (`HKCR\.combos`, ProgID propio, `DefaultIcon` apuntando a
   `combos.ico`, `shell\open\command` con el ejecutable + `%1`). Hacerlo
   desde la app en cada arranque es mala práctica; corresponde al
   instalador (candidato natural: **Inno Setup** sobre un ejecutable
   armado con PyInstaller, estándar de facto en Windows).
2. **Entry point:** que `main.py` (o el ejecutable, o la GUI del ítem 5)
   acepte una ruta a `.combos` como argumento y salte al paso de
   apertura de sesión sin pasar por el menú de inicio.

Sin la pieza 2, el doble click abre COMBOS pero el usuario tiene que
navegar el menú manualmente para abrir el archivo — se pierde el
beneficio de la asociación.

**Condición de activación:** al implementar el instalador (ítem 4 del
plan post-v1.1.0). Cobra sentido pleno cuando exista la GUI (ítem 5); en
el CLI actual, doble click sobre archivos es un patrón de uso raro.
