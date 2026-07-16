# Problemas conocidos

Este archivo documenta limitaciones conocidas del software en su versión actual y el comportamiento esperado en cada caso. Las correcciones planificadas se indican donde corresponde.

---

## Sistema de log limitado al flujo principal

**Versión afectada:** 1.0.0
**Planificado para:** v2

### Descripción

El sistema de log actual registra únicamente errores inesperados que interrumpen la ejecución (excepciones no controladas). No registra las acciones del usuario durante una sesión normal: qué reglamento eligió, qué archivo cargó, cuántas combinaciones se generaron, qué combinaciones
superadas decidió descartar ni a qué ruta exportó.

Esto limita la capacidad de reconstruir lo ocurrido en una sesión cuando el usuario reporta un problema que no produjo un error explícito.

### Planificado para v2

Un log de sesión completo, uno por ejecución, guardado en la carpeta `logs/` junto al ejecutable. Cada entrada registrará timestamp, nivel y descripción de cada acción relevante del flujo.

---

## Combinaciones incompletas no detectadas como superadas

**Versión afectada:** 1.0.0
**Planificado para:** v2

### Descripción

Cuando el usuario no define estados para un tipo de carga que forma parte de una combinación multi-término, ese tipo se omite y la combinación se genera con menos términos de los previstos por el reglamento. A esta situación se la llama "combinación incompleta".
En muchos casos, el término ausente es precisamente el que justifica la existencia de esa combinación: el tipo de carga que genera el efecto desestabilizador o de vuelco. Sin ese término, la combinación resultante pierde su intención de diseño original y queda conformada únicamente por cargas permanentes u otras cargas que no representan el escenario para el que fue concebida.

**Ejemplo:**

El reglamento define `U = 0.9D + 1.6H`. El usuario no define estados de tipo `H`. COMBOS genera la combinación como `0.9D`. Esta combinación debería quedar descartada porque sin el empuje lateral `H` pierde sentido, pero el análisis de preponderancia no puede detectarlo: la Regla 3 clasifica `0.9D` y `1.4D` como no comparables (uno tiene factor `<1` y el otro `≥1`), por lo que la comparación no llega a evaluarse.

### Caso cubierto

- El análisis de preponderancia detecta correctamente la dominancia cuando **ambas** combinaciones tienen factores del mismo rango. Por ejemplo, `1.4D + 1.4F` supera a `1.2D + 1.2F` porque todos los factores son `≥1` y la Regla 3 no bloquea la comparación.
- Para combinaciones que están compuestas por un solo tipo de carga, por ejemplo `1.4D` y `0.9D`, se aplica una condición que limita la Regla 3 y permite comparar combinaciones con factores `<1` y `≥1`. En este caso, la combinación `0.9D` será detectada como superada por `1.4D`. 

### Caso no cubierto

Cuando la combinación incompleta queda con factores `<1` y la combinación dominante tiene factores `≥1`, la Regla 3 las clasifica como no comparables y la dominancia no se detecta. Esto ocurre típicamente con combinaciones de estabilidad (`0.9D + ...`) cuando el término variable está ausente.

### Recomendación para el usuario

Revisá manualmente las combinaciones resultantes cuando algún tipo de carga del reglamento no tiene estados definidos en la planilla. En esos casos, las combinaciones que lo incluían pueden haber quedado con menos términos de los esperados y sin su intención de diseño original.

---

## Nombres de combinaciones no disponibles en el resumen de pantalla

**Versión afectada:** 1.0.0 
**Planificado para:** v2

### Descripción

En la pantalla de resumen (sección "Resumen" de la CLI), las combinaciones se identifican por su índice de generación (`#1`, `#2`, etc.) en lugar de su nombre final (`U1`, `U2`, etc.). El nombre se asigna recién durante la exportación.

### Impacto

El índice de generación no coincide con el nombre que aparece en el Excel exportado. El usuario puede necesitar cruzar ambas referencias manualmente si necesita identificar una combinación específica antes de exportar.

---

## Combinaciones sin carga permanente requieren un tipo virtual

**Versión afectada:** 1.0.0
**Planificado para:** v2

### Descripción

El reglamento exige que todas las combinaciones incluyan al menos un tipo de carga permanente declarado en `permanent_load_types`. Si un reglamento tiene combinaciones que genuinamente no incluyen carga permanente (por ejemplo, combinaciones de sismo puro), el archivo YAML no pasará la validación.

### Solución provisoria

Definí un tipo de carga permanente virtual (por ejemplo, `D0`) en `load_types` y en `permanent_load_types`. Incluilo en esas combinaciones con factor `1.0`. No definas ningún estado de ese tipo en la planilla Excel: COMBOS ignorará automáticamente esas combinaciones al no encontrar estados del tipo correspondiente.

---

## Estilos del Excel de salida no configurables en v1.0.0

**Versión afectada:** 1.0.0
**Planificado para:** v2

### Descripción

El formato visual del archivo de salida (colores de fondo, bordes, anchos de columna y fuentes) está definido internamente en `infraestructura/estilos_excel.py` y no es configurable por el usuario en esta versión.

### Recomendación para el usuario

No hay ningún archivo de configuración para personalizar los estilos en esta versión. Esa posibilidad está reservada para v2.