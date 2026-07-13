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
