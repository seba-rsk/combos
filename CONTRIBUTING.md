# Guía de contribución

Gracias por tu interés en contribuir a COMBOS. Este documento explica cómo reportar problemas, proponer cambios y enviar código.

---

## Antes de empezar

COMBOS es un software de ingeniería civil. Cualquier cambio en la lógica de generación de combinaciones o en las reglas de preponderancia puede afectar resultados que se usan para dimensionar estructuras reales. Por eso, toda contribución que toque el dominio (`dominio/`) debe venir acompañada de casos de prueba que demuestren que el comportamiento es correcto.

---

## Reportar un bug

Usá el sistema de [Issues de GitHub](https://github.com/seba-rsk/combos/issues) y seguí esta estructura:

1. **Descripción** — qué ocurre y qué esperabas que ocurriera.
2. **Pasos para reproducirlo** — lo más detallado posible.
3. **Archivos involucrados** — si el bug ocurre con un YAML o una planilla específica, adjuntala (podés anonimizar los datos si es necesario).
4. **Log de error** — si COMBOS generó un archivo de log, adjuntalo.
5. **Versión de COMBOS** — la versión que estabas usando.

---

## Proponer una mejora

Abrí un Issue antes de escribir código. Describí el problema que querés resolver y la solución que tenés en mente. Esto evita trabajo innecesario si la propuesta no encaja con la dirección del proyecto.

---

## Enviar un pull request

### 1. Forkeá el repositorio y creá una rama

```bash
git checkout -b tipo/descripcion-corta
```

Tipos de rama:

| Tipo        | Cuándo usarlo                                  |
|-------------|------------------------------------------------|
| `fix/`      | Corrección de un bug                           |
| `feat/`     | Funcionalidad nueva                            |
| `docs/`     | Solo documentación                             |
| `refactor/` | Cambio interno sin efecto en el comportamiento |
| `test/`     | Solo tests                                     |

Ejemplos: `fix/regla3-els`, `feat/nuevo-exportador`, `docs/readme-reglamentos`.

### 2. Seguí las reglas de arquitectura

COMBOS tiene separación estricta en tres capas:

- **`cli/`** — interfaz de usuario. No contiene lógica de negocio.
- **`dominio/`** — lógica pura. No depende de archivos ni de la interfaz.
- **`infraestructura/`** — lectura y escritura de archivos. No contiene lógica de combinaciones.

Cada función hace una sola cosa. Los nombres son descriptivos y en español. Sin abreviaturas.

### 3. Convenciones de commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/):

```
tipo(scope): descripción corta en español
```

Tipos permitidos: `fix`, `feat`, `docs`, `refactor`, `test`, `chore`.

Ejemplos:

```
fix(preponderancia): corregir comparación de factores en ELS
feat(exportador): agregar layout por_estado_limite
docs(readme): documentar clave permanent_load_types
refactor(generador): extraer función _construir_componente_direccional
```

- Primera línea: máximo 72 caracteres.
- Usá el cuerpo del commit para explicar el *por qué*, no el *qué*.
- Un commit por cambio lógico. No acumules cambios no relacionados.

### 4. Actualizá la documentación

Si tu cambio afecta el comportamiento del software:

- Actualizá el `README.md` si cambia el uso o la configuración.
- Actualizá `KNOWN_ISSUES.md` si resolvés un problema documentado o descubrís uno nuevo.
- Agregá una entrada en `CHANGELOG.md` bajo `[Unreleased]`.

### 5. Abrí el pull request

- Título claro que describa el cambio.
- Descripción con el problema que resuelve y cómo lo resuelve.
- Si cierra un Issue, mencionalo: `Closes #42`.

---

## Estilo de código

- Python 3.13+.
- Sin comentarios obvios. Solo comentar lo que no es evidente.
- Nombres en español. Sin abreviaturas.
- Type hints en todas las funciones públicas.
- Sin dependencias nuevas sin discutirlo primero en un Issue.

---

## Preguntas

Si tenés dudas sobre si algo encaja en el proyecto o cómo encararlo, abrí un Issue con la etiqueta `question` antes de escribir código.
