import io
from pathlib import Path

import polars as pl
import psycopg

from config import DB_DSN

SQL_DIR = Path(__file__).parent / "sql"


def conectar(autocommit=False):
    return psycopg.connect(DB_DSN, autocommit=autocommit)


def ejecutar_sql(conn, archivo):
    conn.execute((SQL_DIR / archivo).read_text(encoding="utf-8"))


def copiar_df(conn, df: pl.DataFrame, tabla):
    buffer = io.BytesIO()
    df.write_csv(buffer)
    buffer.seek(0)

    columnas = ", ".join(df.columns)
    with conn.cursor().copy(f"COPY {tabla} ({columnas}) FROM STDIN (FORMAT csv, HEADER true)") as copy:
        while bloque := buffer.read(1024 * 1024):
            copy.write(bloque)