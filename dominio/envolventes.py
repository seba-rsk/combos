from __future__ import annotations

from collections import defaultdict


def construir_envolventes(
    combinaciones_validas: list[dict],
    reglamento: dict,
    prefijo_nombre: str,
) -> list[dict]:
    """
    Construye las filas de envolventes a partir de combinaciones ya nombradas.

    Precondición: cada combinación en combinaciones_validas debe tener el campo
    "nombre" ya asignado (lo hace exportador.py antes de llamar a esta función).
    """
    grupos = _agrupar_combinaciones_por_estado_limite(combinaciones_validas)

    filas: list[dict] = []
    for estado_limite, nombres_combinaciones in grupos.items():
        prefijo_estado = _obtener_prefijo_estado_limite(reglamento, estado_limite)
        nombre_envolvente = f"{prefijo_nombre}{prefijo_estado}"
        for nombre_combinacion in nombres_combinaciones:
            filas.append(_construir_fila_envolvente(nombre_envolvente, nombre_combinacion))
    return filas


# ── Agrupamiento ──────────────────────────────────────────────────────────────

def _agrupar_combinaciones_por_estado_limite(
    combinaciones_validas: list[dict],
) -> dict[str, list[str]]:
    grupos: dict[str, list[str]] = defaultdict(list)
    for combinacion in combinaciones_validas:
        grupos[combinacion["estado_limite"]].append(combinacion["nombre"])
    return grupos


# ── Construcción de objetos ───────────────────────────────────────────────────

def _construir_fila_envolvente(nombre_envolvente: str, nombre_combinacion: str) -> dict:
    return {
        "nombre_envolvente": nombre_envolvente,
        "nombre_combinacion": nombre_combinacion,
        "factor": 1,
    }


# ── Lectura del reglamento ────────────────────────────────────────────────────

def _obtener_prefijo_estado_limite(reglamento: dict, estado_limite: str) -> str:
    config_estado = reglamento.get("limit_states", {}).get(estado_limite, {})
    if isinstance(config_estado, dict):
        return config_estado.get("prefix", estado_limite)
    return estado_limite
