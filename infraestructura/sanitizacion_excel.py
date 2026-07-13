from __future__ import annotations

_CARACTERES_DE_FORMULA = ("=", "+", "-", "@")


def neutralizar_texto_libre(valor: str) -> str:
    """
    Neutraliza valores de texto que pueden provenir del usuario o de un
    archivo YAML de terceros (ej. nombre de un estado de carga, metadata
    de un reglamento) antes de escribirlos en una celda de Excel.

    Si el valor empieza con '=', '+', '-' o '@', Excel (u openpyxl, en el
    caso de '=') puede interpretarlo como una fórmula en lugar de texto.
    Anteponer un apóstrofe evita esa interpretación sin alterar el texto
    visible para el usuario.
    """
    if valor.startswith(_CARACTERES_DE_FORMULA):
        return f"'{valor}"
    return valor
