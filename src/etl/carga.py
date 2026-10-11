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


def verificar(conn, validas, cambios):
    llegaron = cambios.get("nuevo", 0) + cambios.get("corregido", 0) + cambios.get("sin_cambios", 0)
    if llegaron != validas:
        raise RuntimeError(f"Clasificados {llegaron} movimientos, pero staging tiene {validas}")

    actuales = conn.execute("SELECT COUNT(*) FROM movimientos_actual").fetchone()[0]
    esperados = validas + cambios.get("protegido", 0)
    if actuales != esperados:
        raise RuntimeError(f"movimientos_actual tiene {actuales} filas, se esperaban {esperados}")


def registrar_control(conn, archivo, orden, validas, rechazadas, cambios):
    conn.execute(
        """
        INSERT INTO control_cargas (
            archivo, orden_corte, filas_leidas, filas_validas, filas_rechazadas,
            nuevos, corregidos, eliminados, sin_cambios, protegidos
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            archivo, orden, validas + rechazadas, validas, rechazadas,
            cambios.get("nuevo", 0), cambios.get("corregido", 0),
            cambios.get("eliminado", 0), cambios.get("sin_cambios", 0),
            cambios.get("protegido", 0),
        ),
    )