import polars as pl

from db import copiar_df, ejecutar_sql
from etl.extraccion import COLUMNAS
from etl.transformacion import LLAVE


def cortes_procesados(conn):
    return {fila[0] for fila in conn.execute("SELECT archivo FROM control_cargas")}


def ultimo_corte(conn):
    return conn.execute("SELECT COALESCE(MAX(orden_corte), -1) FROM control_cargas").fetchone()[0]


def cargar_staging(conn, validos: pl.DataFrame, rechazados: pl.DataFrame):
    conn.execute("TRUNCATE stg_movimientos, stg_llaves_rechazadas")
    copiar_df(conn, validos, "stg_movimientos")

    llaves_rechazadas = (
        rechazados.select([pl.col(f"_{c}").alias(c) for c in LLAVE])
        .drop_nulls()
        .unique()
    )
    copiar_df(conn, llaves_rechazadas, "stg_llaves_rechazadas")


def registrar_rechazados(conn, rechazados: pl.DataFrame, archivo):
    log = rechazados.select([*COLUMNAS, "motivo"]).with_columns(pl.lit(archivo).alias("archivo"))
    copiar_df(conn, log, "movimientos_rechazados")


def consolidar(conn, orden):
    conn.execute("SELECT set_config('pipeline.corte', %s, true)", (str(orden),))
    ejecutar_sql(conn, "consolidacion.sql")
    return dict(conn.execute("SELECT tipo, COUNT(*) FROM cambios GROUP BY tipo").fetchall())