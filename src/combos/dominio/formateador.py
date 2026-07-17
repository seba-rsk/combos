from __future__ import annotations

from combos.dominio.modelos import Componente


def formatear_componentes(componentes: list[Componente]) -> str:
    """
    Arma la representación textual de una combinación para mostrarla en
    pantalla o en el Excel de salida, con el formato
    "1.4 × DEAD  +  1.2 × CP".

    Args:
        componentes: Componentes de una combinación, cada uno con
            "nombre_estado", "factor" y "signo".

    Returns:
        Cadena con los componentes unidos por "+" o "-" según su signo,
        o cadena vacía si la combinación no tiene componentes.
    """
    if not componentes:
        return ""
    resultado = []
    for indice, componente in enumerate(componentes):
        factor = componente.factor
        nombre = componente.nombre_estado
        signo = componente.signo
        factor_str = f"{factor:.1f}" if factor == int(factor) else f"{factor:g}"
        if indice == 0:
            prefijo = "-" if signo < 0 else ""
            resultado.append(f"{prefijo}{factor_str} × {nombre}")
        else:
            separador = "  -  " if signo < 0 else "  +  "
            resultado.append(f"{separador}{factor_str} × {nombre}")
    return "".join(resultado)
