import re
from pathlib import Path

import polars as pl

from config import RAW_DIR

COLUMNAS = [
    "id_cliente", "date", "product", "type",
    "fund", "amount", "description", "commercial_name",
]

PATRON_CORTE = re.compile(r"movimientos_dia_T(\d*)\.parquet")


def listar_cortes(directorio: Path = RAW_DIR):
    cortes = []
    for archivo in directorio.glob("movimientos_dia_T*.parquet"):
        coincidencia = PATRON_CORTE.fullmatch(archivo.name)
        if coincidencia:
            orden = int(coincidencia.group(1) or 0)
            cortes.append((orden, archivo))
    return sorted(cortes)


def leer_corte(archivo: Path) -> pl.LazyFrame:
    lf = pl.scan_parquet(archivo)
    esquema = lf.collect_schema()

    faltantes = set(COLUMNAS) - set(esquema.names())
    if faltantes:
        raise ValueError(f"{archivo.name}: faltan columnas {sorted(faltantes)}")

    if not esquema["amount"].is_numeric():
        raise ValueError(f"{archivo.name}: amount llegó como {esquema['amount']}, se esperaba numérico")

    return lf.select(COLUMNAS)