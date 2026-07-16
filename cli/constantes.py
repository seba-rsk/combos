from __future__ import annotations

# Carpeta por defecto para guardar y buscar archivos del usuario.
NOMBRE_CARPETA_ESCRITORIO = "Desktop"

# Prefijos de los nombres de archivo que propone COMBOS por defecto.
PREFIJO_PLANTILLA = "Input_COMBOS_"
PREFIJO_EXPORTACION = "Output_COMBOS_"

# Extensiones de archivo que maneja la interfaz.
EXTENSION_EXCEL = ".xlsx"
EXTENSION_YAML = ".yaml"

# Formato de fecha usado en los nombres de archivo por defecto, para que
# corridas sucesivas no propongan siempre el mismo nombre.
FORMATO_FECHA_ARCHIVO = "%Y-%m-%d"

# Cantidad de filas que se muestran por página en las tablas largas de la
# consola (Resumen, Combinaciones superadas), antes de pedir Enter para
# seguir viendo el resto.
FILAS_POR_PAGINA = 20

# Largo máximo (en caracteres) de la lista de designaciones normativas de
# la línea "Afecta a" del menú de parámetros, antes de continuar en la
# línea siguiente con sangría colgante.
ANCHO_DESIGNACIONES_AFECTADAS = 50

# Pausa breve antes de imprimir cada separador de sección, para que el
# avance del flujo se perciba como pasos y no como un volcado instantáneo.
PAUSA_SEPARADOR_SEGUNDOS = 0.3

# Largo de la línea que acompaña al encabezado de cada estado límite en
# las tablas de consola (Resumen, Combinaciones superadas).
ANCHO_SEPARADOR_ESTADO = 60

# Formato de fecha y hora de las entradas del log de errores.
FORMATO_TIMESTAMP_LOG = "%Y-%m-%d %H:%M:%S"
