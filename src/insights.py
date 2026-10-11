import re
from datetime import datetime
from decimal import Decimal

from config import OUTPUT_DIR
from db import SQL_DIR


def _consultas():
    texto = (SQL_DIR / "insights.sql").read_text(encoding="utf-8")
    partes = re.split(r"^-- nombre: (.+)$", texto, flags=re.MULTILINE)
    return [(nombre.strip(), sql.strip()) for nombre, sql in zip(partes[1::2], partes[2::2])]


def _formato(valor):
    if valor is None:
        return ""
    if isinstance(valor, (Decimal, float)):
        return f"{valor:,.2f}"
    if isinstance(valor, int):
        return f"{valor:,}"
    return str(valor)


def _tabla_md(columnas, filas):
    lineas = [
        "| " + " | ".join(columnas) + " |",
        "|" + " --- |" * len(columnas),
    ]
    lineas += ["| " + " | ".join(_formato(v) for v in fila) + " |" for fila in filas]
    return "\n".join(lineas)


def generar_reporte(conn):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    secciones = [f"# Reporte de calidad y evolución\n\nGenerado: {datetime.now():%Y-%m-%d %H:%M}"]

    for nombre, sql in _consultas():
        cursor = conn.execute(sql)
        columnas = [c.name for c in cursor.description]
        titulo = nombre.replace("_", " ").capitalize()
        secciones.append(f"## {titulo}\n\n{_tabla_md(columnas, cursor.fetchall())}")

    (OUTPUT_DIR / "reporte.md").write_text("\n\n".join(secciones) + "\n", encoding="utf-8")


def exportar_rechazados(conn):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    consulta = "COPY (SELECT * FROM movimientos_rechazados ORDER BY archivo, id) TO STDOUT (FORMAT csv, HEADER true)"

    with (OUTPUT_DIR / "rechazados.csv").open("wb") as archivo:
        # Excel necesita el BOM para mostrar bien las tildes de un CSV en UTF-8
        archivo.write(b"\xef\xbb\xbf")
        with conn.cursor().copy(consulta) as copy:
            for bloque in copy:
                archivo.write(bloque)