# COMBOS

**Generador de combinaciones de carga estructural para ingeniería civil.**

![Versión](https://img.shields.io/badge/versión-1.1.0-blue)
![Licencia](https://img.shields.io/badge/licencia-MIT-green)
![Python](https://img.shields.io/badge/Python-3.12+-yellow)
![Plataforma](https://img.shields.io/badge/plataforma-Windows-lightgrey)
![CI](https://github.com/seba-rsk/combos/actions/workflows/ci.yml/badge.svg)

COMBOS lee un reglamento de cargas desde un archivo YAML, procesa una planilla Excel completada por el usuario con sus estados de carga, y exporta las combinaciones válidas en el formato que SAP2000 — u otro software de cálculo — puede importar directamente.

---

## Capturas de pantalla

### Flujo de trabajo
![Diagrama de flujo](https://raw.githubusercontent.com/seba-rsk/combos/main/docs/diagrama_flujo.svg)

### Planilla de entrada
![Planilla de entrada](https://raw.githubusercontent.com/seba-rsk/combos/main/docs/planilla_input.png)

### Archivo de resultados - Resumen General
![Planilla de salida - Resumen](https://raw.githubusercontent.com/seba-rsk/combos/main/docs/planilla_output_resumen.png)

![Planilla de salida - Resumen completo](https://raw.githubusercontent.com/seba-rsk/combos/main/docs/planilla_output_resumen_completo.png)

### Archivo de exportación a SAP2000

![Planilla de salida - SAP2000](https://raw.githubusercontent.com/seba-rsk/combos/main/docs/planilla_output_sap2000.png)

![Planilla de salida - SAP2000 completo](https://raw.githubusercontent.com/seba-rsk/combos/main/docs/planilla_output_sap2000_completo.png)

---

## Características

- Generación automática de combinaciones a partir de un reglamento YAML configurable.
- Soporte para estados de carga simples y direccionales (con variantes por dirección).
- Detección y eliminación automática de combinaciones duplicadas.
- Análisis de preponderancia entre combinaciones comparables del mismo estado límite.
- Resolución interactiva: el usuario decide qué combinaciones superadas conservar.
- Resumen en pantalla de las combinaciones resultantes antes de exportar.
- Exportación a Excel con hoja de resumen completo y hoja de datos lista para importar.
- Generación de envolventes por estado límite incluida en la exportación.
- Compatible con SAP2000. Extensible a otros softwares mediante archivos YAML de exportación.
- Reglamentos intercambiables: incluye CIRSOC 2005 y soporte para agregar los propios.
- Interfaz de línea de comandos guiada paso a paso. Funciona en Windows sin instalación adicional.

---

## Requisitos

- Windows 10 o superior (64 bits).
- La carpeta de instalación debe mantenerse completa e intacta. No muevas ni elimines ningún archivo o subcarpeta interna.
- No requiere Python instalado (la versión portable incluye todo lo necesario).

Para correr desde el código fuente:

- Python 3.12 o superior.
- Dependencias listadas en `pyproject.toml`.

---

## Instalación

### Versión portable (recomendada)

1. Descargá la última versión desde [Releases](https://github.com/seba-rsk/combos/releases).
2. Descomprimí el archivo `.zip` en la ubicación que prefieras (por ejemplo `C:\COMBOS\`).
3. **No muevas ni elimines ningún archivo o subcarpeta** dentro de la carpeta descomprimida. El programa necesita todos los archivos para funcionar.
4. Para ejecutar COMBOS, abrí una terminal (CMD o PowerShell), navegá hasta la carpeta y ejecutá:

```cmd
.\COMBOS.exe
```

> **Nota:** Si hacés doble clic en `COMBOS.exe` directamente, la ventana se cerrará al presionar Enter al finalizar la sesión. Para una experiencia más cómoda, ejecutá desde una terminal abierta (CMD o PowerShell).

No requiere instalación. Para desinstalar, borrá la carpeta.

### Desde el código fuente

```bash
git clone https://github.com/seba-rsk/combos.git
cd combos
pip install -e .
python main.py
```

---

## Uso

COMBOS guía al usuario paso a paso a través de la interfaz de línea de comandos. En cualquier momento podés presionar **Ctrl+C** para cancelar y salir del programa limpiamente.

### Flujo de trabajo

**Paso 1 — Selección del reglamento**

COMBOS lista los perfiles YAML disponibles en la carpeta `profiles/`. Elegís el reglamento que corresponde a tu proyecto.

**Paso 2 — Generación de la planilla (opcional)**

COMBOS puede generar una planilla Excel en blanco lista para completar, con las columnas y validaciones ya configuradas según el reglamento elegido. Si ya tenés una planilla completada, podés saltear este paso.

**Paso 3 — Carga de la planilla**

Seleccionás la planilla Excel completada con tus estados de carga.

**Paso 4 — Parámetros del reglamento (solo si aplican a tus estados)**

Si el reglamento define parámetros (por ejemplo, el factor de sobrecarga L según el destino del edificio), COMBOS pregunta una sola vez los que afectan a tus estados de carga, con un menú de opciones. El menú indica qué combinaciones del reglamento afecta cada parámetro, usando la designación de la norma (ej. "Afecta a: ELU · U3.1, U3.3..."). Enter acepta la opción por defecto. La elección queda registrada en el encabezado del Excel exportado. Los parámetros cuyos tipos de carga no tienen estados ingresados no se preguntan — no participan de ninguna combinación generada. Si ningún parámetro aplica, este paso no aparece.

**Paso 5 — Procesamiento**

COMBOS genera todas las combinaciones posibles según el reglamento, detecta duplicadas y analiza preponderancia automáticamente.

**Paso 6 — Resolución de combinaciones superadas**

Para cada grupo de combinaciones superadas, COMBOS te presenta las opciones y vos decidís cuáles descartar y cuáles conservar en el resultado final.

**Paso 7 — Resumen en pantalla**

COMBOS muestra en pantalla las combinaciones resultantes con sus componentes, estado límite y nombre asignado.

**Paso 8 — Exportación**

Seleccionás el perfil de exportación y la ruta de destino. COMBOS genera el archivo Excel de salida.

---

### Ejemplo paso a paso

Este ejemplo usa el reglamento **CIRSOC 2005** con tres estados de carga simples:

| Nombre del estado | Tipo de carga | Tipo de estado  |
|-------------------|---------------|-----------------|
| DEAD              | D             | Simple          |
| SC                | L             | Simple          |       
| CP                | D             | Simple          |

COMBOS genera 26 combinaciones brutas a partir del reglamento. Luego del procesamiento:

- **17 combinaciones** se eliminan por ser duplicadas exactas entre sí.
- **5 combinaciones** quedan marcadas como superadas por otras. En el paso 5, el usuario elige descartarlas todas.
- **4 combinaciones** conforman el resultado final:

| Nombre | Componentes                      | Estado límite |
|--------|----------------------------------|---------------|
| U1     | 1.4 × DEAD + 1.4 × CP            | ELU           |
| U2     | 1.2 × DEAD + 1.2 × CP + 1.6 × SC | ELU           |
| S1     | 1.0 × DEAD + 1.0 × CP            | ELS           |
| S2     | 1.0 × DEAD + 1.0 × CP + 1.0 × SC | ELS           |

El archivo Excel de salida incluye el resumen completo del proceso y las tablas listas para importar en SAP2000.

---

## Planilla de entrada

La planilla Excel de entrada se genera desde COMBOS (paso 2) y se completa manualmente con los estados de carga del proyecto. Tiene una sola hoja llamada **"Estados de carga"** con hasta **20 filas**. Las filas que el usuario deja vacías se ignoran automáticamente.

### Encabezado

La planilla incluye un bloque de encabezado con metadatos generados automáticamente: versión de COMBOS, perfil usado, nombre y descripción del reglamento, país y fecha de generación.

### Columnas

| Columna               | Obligatoria                   | Descripción                     |
|-----------------------|-------------------------------|---------------------------------|
| **N°**                | —                             | Numeración automática del 1 al 20. Generada por COMBOS; el usuario no la completa. |
| **Nombre del estado** | Siempre                       | Nombre exacto del estado de carga tal como está definido en el software de cálculo (ej: `DEAD`, `LIVE`, `WIND-X`). |
| **Tipo de carga**     | Siempre                       | Código del tipo de carga según el reglamento activo (ej: `D`, `L`, `W`). Lista desplegable con validación: Excel rechaza valores no definidos en el reglamento. |
| **Tipo de estado**    | Siempre                       | `Simple` o `Direccional`. Lista desplegable con validación. |
| **Número de grupo**   | Solo en estados direccionales | Entero positivo que agrupa los estados de una misma acción direccional. COMBOS construye el nombre del grupo como `tipo_carga-número` (ej: `W-1`). Se ignora si el tipo de estado es Simple. |
| **Incluir opuesto**   | Solo en estados direccionales | `Sí` o `No`. Indica si COMBOS debe generar automáticamente la variante con signo opuesto para ese estado. Se ignora si el tipo de estado es Simple. |

> Las columnas **Número de grupo** e **Incluir opuesto** tienen fondo gris en todas las filas para indicar visualmente que solo aplican a estados direccionales.

---

## Archivo de salida

El archivo Excel de salida tiene dos hojas.

### Hoja 1 — Resumen COMBOS

Contiene cinco tablas apiladas verticalmente que documentan el proceso completo:

| Tabla                                      | Contenido                                    |
|--------------------------------------------|----------------------------------------------|
| **Datos ingresados por el usuario**        | Los estados de carga tal como fueron leídos de la planilla de entrada. |
| **Combinaciones resultantes**              | Las combinaciones que pasan el proceso completo y se incluyen en la exportación. |
| **Combinaciones eliminadas por duplicado** | Combinaciones idénticas a otra ya incluida, con referencia a cuál las duplica. |
| **Combinaciones superadas por otras**      | Combinaciones que el usuario eligió descartar por ser dominadas, con referencia a cuál las supera. |
| **Resumen general**                        | Todas las combinaciones generadas con su estado final: si resultaron duplicadas, superadas, descartadas o incluidas. Es la trazabilidad completa del proceso.    |

### Hoja 2 — Output {nombre\_exportador}

Contiene tres tablas dispuestas horizontalmente:

**Tabla 1 — Combinaciones**
Las combinaciones resultantes en el formato configurado en el YAML del exportador. Soporta dos layouts:

- `por_componente`: una fila por cada componente de cada combinación. Formato requerido por SAP2000.

  | Combination | Load\_case | Factor |
  |-------------|------------|--------|
  | U1          | DEAD       | 1.4    |
  | U1          | CP         | 1.4    |
  | U2          | DEAD       | 1.2    |
  | U2          | CP         | 1.2    |
  | S1          | DEAD       | 1.0    |
  | S1          | CP         | 1.0    |
  | S2          | DEAD       | 1.0    |
  | S2          | CP         | 1.0    |
  | S2          | SC         | 1.0    |

- `por_combinacion`: una fila por combinación, con una columna por cada estado de carga presente.

  | Case | DEAD | CP   | SC   |
  |------|------|------|------|
  | U1   | 1.4  | 1.4  |      |
  | U2   | 1.2  | 1.2  | 1.6  |
  | S1   | 1.0  | 1.0  |      |
  | S2   | 1.0  | 1.0  | 1.0  |

**Tabla 2 — Nombres de combinaciones**
Lista compacta de los nombres finales de todas las combinaciones resultantes, una por fila.

  | Combination |
  |-------------|
  | U1          |
  | U2          |
  | S1          |
  | S2          |

**Tabla 3 — Envolventes**
Una envolvente por estado límite, compuesta por todas las combinaciones de ese estado con factor 1. El nombre de cada envolvente se forma con el prefijo `ENV` (configurable desde el perfil de exportador) seguido del prefijo del estado límite (ej: `ENVU`, `ENVS`).

| Envelope | Combination | Factor |
|----------|-------------|--------|
| ENVU     | U1          | 1.0    |
| ENVU     | U2          | 1.0    |
| ENVS     | S1          | 1.0    |
| ENVS     | S2          | 1.0    |

---

## Conceptos clave

### Estados de carga

Un estado de carga es una acción que actúa sobre la estructura: peso propio, sobrecarga de uso viento, sismo, etc. El usuario los define en la planilla Excel y les asigna un nombre, un tipo de carga y un tipo de estado.

**Estado simple** — actúa con un único signo y no tiene relación de exclusividad con otros estados. Participa en todas las combinaciones donde su tipo de carga sea requerido.

**Estado direccional** — pertenece a un grupo que representa distintas direcciones de actuación de una misma acción (por ejemplo, viento en X y viento en Y). Los estados del mismo grupo son **mutuamente excluyentes**: nunca aparecen juntos en la misma combinación. COMBOS los expande
automáticamente mediante producto cartesiano.

El nombre del grupo se construye como `tipo_carga-número` (ej: `W-1`). Si el usuario activa "Incluir opuesto" para un estado direccional, COMBOS genera automáticamente una variante adicional con signo negativo dentro del mismo grupo. El usuario no define esa variante: COMBOS la infiere.

**Ejemplo:** `Wx` y `Wy` son ambos de tipo `W`, grupo `1`, con opuesto activado. COMBOS construye el grupo `W-1` con cuatro variantes: `Wx`, `-Wx`, `Wy`, `-Wy`. Para una combinación base que incluya el tipo `W`, se generan cuatro combinaciones, una por variante. Si existiera además un grupo `E-1` con `Ex` y `Ey` en la misma combinación base, el resultado sería el producto cartesiano de ambos grupos: `Wx+Ex`, `Wx+Ey`, `Wy+Ex`, `Wy+Ey`.

> **Nota:** COMBOS no conoce la lógica física de cómo se aplican las cargas dentro del software de cálculo. Solo genera combinaciones siguiendo el reglamento seleccionado al iniciar. La decisión de qué tipo corresponde a cada estado, cómo se agrupan los direccionales y si tienen opuestos es responsabilidad del ingeniero.

### Combinaciones de carga

Un reglamento de cargas establece fórmulas del tipo `1.2D + 1.6L + 0.5S`, donde cada letra representa un tipo de carga y el número que la acompaña es su factor de ponderación. COMBOS toma esas fórmulas y las expande automáticamente con los estados de carga reales del proyecto, generando todas las combinaciones posibles. Cuando **ninguno** de los tipos de carga que requiere una combinación tiene estados definidos en la planilla, esa combinación no se genera. Cuando **algunos sí y otros no**, la combinación se genera igual, pero con menos términos de los previstos por el reglamento — ver [KNOWN_ISSUES.md](KNOWN_ISSUES.md) para el detalle y sus implicancias.

### Preponderancia

Cuando dos combinaciones son comparables entre sí (mismo estado límite, mismo conjunto de tipos de carga, mismos signos), una puede dominar a la otra: si todos sus factores son mayores o iguales y al menos uno es estrictamente mayor, la combinación dominante hace redundante a la dominada. COMBOS detecta estas relaciones automáticamente y las marca como "superadas", permitiendo al usuario decidir cuáles conservar en el resultado final.

Dos combinaciones no son comparables cuando tienen distinta intención de diseño. Por ejemplo, una combinación con `0.9D` (donde D es un tipo de carga permanente) representa una verificación de estabilidad donde la carga permanente actúa en sentido favorable, y no debe compararse directamente con combinaciones de amplificación como `1.2D` o `1.4D`.

### Nomenclatura de combinaciones

El nombre de cada combinación se construye a partir del prefijo del estado
límite definido en el reglamento YAML:

- **Sin variantes direccionales:** `prefijo` + número secuencial. Ejemplo: `U1`, `U2`, `S1`.
- **Con variantes direccionales:** `prefijo` + número secuencial + `-` + número de variante.   Ejemplo: `U3-1`, `U3-2`, `U3-3`, `U3-4`.

Los nombres se asignan **al final del proceso**, una vez que el usuario decidió qué combinaciones superadas descartar. Esto garantiza que la numeración del archivo de salida no tenga huecos.

### Estados límite

Los reglamentos organizan las combinaciones en estados límite. El más común es **ELU** (Estado Límite Último), usado para dimensionar secciones, y **ELS** (Estado Límite de Servicio), usado para verificar deformaciones y fisuración. COMBOS solo compara combinaciones del mismo estado límite.

---

## Estructura del proyecto

```
combos/
├── main.py                       # Punto de entrada del programa
├── version.py                    # Fuente única de la versión del programa
├── combos.spec                   # Configuración de build PyInstaller
├── pyproject.toml                # Configuración del proyecto y dependencias
├── combos.ico                    # Icono para versión portable.
├── cli/
│   ├── consola.py                # Funciones de presentación en pantalla
│   ├── flujo.py                  # Orquestador del flujo completo
│   └── constantes.py             # Constantes de la interfaz (rutas, extensiones, prefijos)
├── dominio/
│   ├── modelos.py                # Objetos de dominio (dataclasses) que circulan por el pipeline
│   ├── generador.py              # Generación de combinaciones de carga
│   ├── duplicados.py             # Detección y marcado de combinaciones duplicadas
│   ├── envolventes.py            # Generación de envolventes
│   ├── preponderancia.py         # Análisis de preponderancia y marcado de combinaciones superadas
│   ├── formateador.py            # Formateo de combinaciones para su presentación en pantalla
│   ├── lector_yaml.py            # Lectura y validación de reglamentos YAML
│   ├── parametros.py             # Resolución de parámetros del reglamento a factores numéricos
│   └── lector_plantilla.py       # Validación de los estados de carga ingresados por el usuario
├── infraestructura/
│   ├── config_interna.py         # Configuración interna embebida de plantilla y resumen
│   ├── estilos_excel.py          # Estilos visuales aplicados a los archivos Excel generados
│   ├── sanitizacion_excel.py     # Neutralización de texto libre antes de escribirlo en Excel
│   ├── encabezado_excel.py       # Bloque de encabezado compartido por resumen y plantilla
│   ├── guardado_excel.py         # Guardado atómico de los archivos Excel generados
│   ├── exportador.py             # Generación del archivo Excel de salida
│   ├── generador_plantilla.py    # Generación de la planilla Excel en blanco para el usuario
│   ├── lector_excel.py           # Lectura de la planilla Excel completada por el usuario
│   └── rutas.py                  # Resolución de rutas del sistema de archivos (desarrollo y portable)
├── tests/                        # Tests unitarios (pytest) de la lógica de dominio
│   └── dominio/
├── docs/                         # Documentación general para readme.txt
│   ├── diagrama_flujo.svg
│   ├── planilla_input.png
│   ├── planilla_output_resumen.png
│   ├── planilla_output_resumen_completo.png
│   ├── planilla_output_sap2000.png
│   └── planilla_output_sap2000_completo.png
├── profiles/
│   ├── ejemplo_reglamento.yaml          # Plantilla comentada para crear un reglamento nuevo
│   ├── cirsoc2005.yaml                  # Reglamento CIRSOC-2005 (Argentina)
│   ├── cirsoc2005_actualizado.yaml      # CIRSOC-2005 con factor de sobrecarga L parametrizado según destino
│   └── cirsoc2005_reducido.yaml         # Reglamento CIRSOC-2005 (Argentina) con tipos de cargas más usados
├── exportadores/
│   ├── por_combinacion.yaml      # Ejemplo de exportador con layout "una fila por combinación"
│   ├── por_componente.yaml       # Ejemplo de exportador con layout "una fila por componente"
│   └── sap2000.yaml              # Exportador para SAP2000
│
└── (documentación)
    ├── README.md                 # Documentación principal del proyecto
    ├── CHANGELOG.md              # Historial de cambios por versión
    ├── CONTRIBUTING.md           # Guía para reportar bugs y enviar contribuciones
    ├── KNOWN_ISSUES.md           # Limitaciones conocidas y comportamiento esperado en casos borde
    ├── AUTHORS.md                # Autores y colaboradores del proyecto
    ├── LICENSE                   # Licencia de uso del software
    └── .gitignore
```

---

## Agregar un reglamento propio

Creá un archivo `.yaml` en la carpeta `profiles/`. COMBOS lo detecta automáticamente al iniciar. Tomá como referencia `profiles/ejemplo_reglamento.yaml`, que incluye todos los campos comentados. La estructura mínima es:

```yaml
metadata:
  code_name: "NOMBRE_CORTO"
  code_version: "AÑO_O_VERSION"
  country: "País"
  description: "Descripción completa del reglamento"

# Tipos de carga que representan cargas permanentes gravitatorias.
# Obligatorio. Todas las combinaciones deben incluir al menos uno de estos tipos.
permanent_load_types:
  - D

limit_states:
  ELU:
    name: "Estado límite último"
    prefix: "U"
  ELS:
    name: "Estado límite de servicio"
    prefix: "S"

load_types:
  D:
    name: "Cargas permanentes"
    description: "Descripción del tipo de carga."
  L:
    name: "Cargas vivas"
    description: "Descripción del tipo de carga."

combinations:
  ELU:
    - id: 1
      name: "U1.1"    # Designación de la norma (opcional)
      factors:
        D: 1.4
    - id: 2
      name: "U2.1"
      factors:
        D: 1.2
        L: 1.6
  ELS:
    - id: 1
      name: "S1.1"
      factors:
        D: 1.0
    - id: 2
      name: "S1.2"
      factors:
        D: 1.0
        L: 1.0
```

### Reglas del reglamento

- `permanent_load_types` es obligatorio. Si falta o está vacío, COMBOS no puede cargar el reglamento. COMBOS lo usa para verificar que toda combinación tenga al menos una carga permanente, lo que garantiza que el análisis de preponderancia pueda comparar combinaciones con coherencia física: una combinación sin carga permanente no puede compararse correctamente con una que sí la tiene.

- Si tu reglamento incluye combinaciones que genuinamente no contienen carga permanente (por ejemplo, combinaciones de sismo puro), podés usar un **tipo de carga permanente virtual**. Definí un tipo (por ejemplo `D0`) en `load_types` y en `permanent_load_types`, e incluilo en esas combinaciones con factor `1.0`. No definas ningún estado de ese tipo en la planilla: COMBOS ignorará automáticamente las combinaciones donde todos los tipos requeridos carecen de estados definidos.

```yaml
  permanent_load_types:
    - D
    - D0   # Tipo virtual para combinaciones sin carga permanente real

  load_types:
    D0:
      name: "Permanente virtual"
      description: "Tipo auxiliar para combinaciones sin carga permanente."

  combinations:
    ELU:
      - id: 5
        factors:
          D0: 1.0
          E: 1.0   # Combinación de sismo puro
```
- Todos los tipos en `permanent_load_types` deben estar declarados en `load_types`.
- Todos los tipos usados en `combinations` deben estar declarados en `load_types`.
- Toda combinación debe contener al menos un tipo de carga permanente.
- Los factores deben ser mayores que cero, o una referencia a un parámetro (ver la sección siguiente).
- El `id` de cada combinación debe ser un número entero, único dentro de su estado límite (puede repetirse entre estados límite distintos).
- El campo `name` de cada combinación es opcional: es la designación con la que la norma la identifica (ej. `"U3.1"`), en texto libre. Si existe, no puede estar vacío y debe ser único en todo el reglamento, incluso entre estados límite. COMBOS lo usa para referirse a las combinaciones en la nomenclatura de la norma; sin `name`, las identifica por su id.

### Parámetros del reglamento (opcional)

Cuando un reglamento admite factores alternativos que dependen de una propiedad del proyecto — por ejemplo, el factor de la sobrecarga L según el destino del edificio —, podés declararlos como **parámetros** en vez de duplicar el archivo YAML por cada variante. COMBOS pregunta cada parámetro una sola vez por corrida — después de leer tus estados de carga, y solo si algún estado usa los tipos que el parámetro afecta —, aplica el valor elegido a todos los factores que lo referencian y registra la elección en el encabezado del Excel exportado. Un parámetro que no aplica a tus estados se resuelve con su valor por defecto sin preguntar.

```yaml
parameters:
  L_factor:                            # Id del parámetro
    name: "Factor de sobrecarga L"     # Título que se muestra en pantalla
    options:                           # Al menos dos opciones
      - label: "Cocheras, lugares de reunión pública o L > 5 kN/m²"
        value: 1.0
      - label: "Resto de los destinos (L ≤ 5 kN/m²)"
        value: 0.5
    default: 1.0                       # Debe coincidir con el value de una opción

combinations:
  ELU:
    - id: 5
      factors:
        D: 1.2
        Lr: 1.6
        L: { param: L_factor }         # Referencia: se resuelve con el valor elegido
```

Reglas de la sección `parameters`:

- Es opcional. Si no existe, el reglamento se comporta como siempre; si existe, no puede estar vacía.
- Cada parámetro necesita `name`, al menos dos `options` (cada una con `label` y `value` mayor que cero) y un `default` igual al `value` de alguna opción.
- Toda referencia `{ param: X }` debe apuntar a un parámetro definido, y todo parámetro definido debe ser usado por al menos una combinación.

El perfil `profiles/cirsoc2005_actualizado.yaml` es un caso real: aplica la excepción del CIRSOC 2005 que permite reducir el factor de L de 1.0 a 0.5 en las combinaciones U3 a U5 del ELU según el destino del edificio.

---

## Agregar un exportador propio

Creá un archivo `.yaml` en la carpeta `exportadores/`. COMBOS lo detecta automáticamente al exportar. El exportador define el formato del archivo Excel de salida y soporta dos layouts:

- **`por_componente`** — una fila por cada componente de cada combinación. Formato requerido por SAP2000 y la mayoría de los softwares de cálculo estructural.
- **`por_combinacion`** — una fila por combinación, con una columna por cada estado de carga. Útil para revisión manual o para softwares con ese formato de importación.

Tomá como referencia `exportadores/por_combinacion.yaml` o `exportadores/por_componente.yaml`, que incluyen todos los campos disponibles con sus comentarios explicativos.

---

## Errores frecuentes

**"El reglamento no define `permanent_load_types`"**
Agregá la clave al archivo YAML del reglamento. Es obligatoria. Ver la sección _Agregar un reglamento propio_.

**"Combinación X no contiene ningún tipo de carga permanente"**
Todas las combinaciones del reglamento deben incluir al menos un tipo de carga permanente. Revisá los `factors` de la combinación indicada.

**"Tipos de carga no definidos en load_types"**
Alguna combinación usa un tipo de carga (por ejemplo `W`) que no está declarado en la sección `load_types` del YAML.

**El software falla con un error inesperado**
COMBOS genera automáticamente un archivo de log en la carpeta de instalación. Enviá ese archivo al reportar el problema.

**La ventana se cierra al terminar**
Es el comportamiento normal al ejecutar desde doble clic. Ejecutá COMBOS desde una terminal (CMD o PowerShell) para que la ventana permanezca abierta.

**"Failed to load Python DLL"**
La carpeta de instalación está incompleta. Asegurate de haber descomprimido el `.zip` completo sin mover ni eliminar ningún archivo interno.

---

## Alcance de esta versión

COMBOS automatiza la generación y filtrado de combinaciones, pero hay decisiones que pertenecen al criterio del ingeniero y tareas que están planificadas para versiones futuras.

**Lo que COMBOS no hace en esta versión:**

- No decide qué tipo de carga corresponde a cada estado. Esa asignación la realiza el ingeniero en la planilla Excel.
- No valida si los factores definidos en el YAML son correctos según el reglamento impreso. COMBOS aplica los factores tal como están escritos, sin cotejarlos con ninguna fuente externa.
- No tiene editor visual de archivos YAML. Los reglamentos y exportadores se crean y editan manualmente con cualquier editor de texto.
- No soporta estados con dependencias entre sí (por ejemplo, estados que solo pueden coexistir con otros estados específicos).
- No tiene interfaz gráfica. Opera exclusivamente desde la línea de comandos.
- Solo genera el ejecutable portable para Windows. Linux y macOS requieren correr el software desde el código fuente.

---

## Limitaciones conocidas

Ver [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

---

## Contribuciones

Ver [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Licencia

MIT — ver [LICENSE](LICENSE).

---

## Autor

Desarrollado por **Sebastián A. Roskopf** — [GitHub](https://github.com/seba-rsk)
