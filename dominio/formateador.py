from __future__ import annotations


def formatear_componentes(componentes: list[dict]) -> str:
    if not componentes:
        return ""
    resultado = []
    for indice, componente in enumerate(componentes):
        factor = componente["factor"]
        nombre = componente["nombre_estado"]
        signo = componente["signo"]
        factor_str = f"{factor:.1f}" if factor == int(factor) else f"{factor:g}"
        if indice == 0:
            prefijo = "-" if signo < 0 else ""
            resultado.append(f"{prefijo}{factor_str} × {nombre}")
        else:
            separador = "  -  " if signo < 0 else "  +  "
            resultado.append(f"{separador}{factor_str} × {nombre}")
    return "".join(resultado)