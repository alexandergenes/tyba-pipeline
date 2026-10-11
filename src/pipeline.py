import logging
import time

import polars as pl

from db import conectar, ejecutar_sql
from etl.extraccion import listar_cortes, leer_corte
from etl.transformacion import normalizar, validar, identificar
from etl.carga import (
    cortes_procesados, ultimo_corte, cargar_staging, registrar_rechazados,
    consolidar, verificar, registrar_control,
)

log = logging.getLogger("pipeline")


def procesar_corte(conn, orden, archivo):
    inicio = time.perf_counter()

    validos, rechazados = pl.collect_all(validar(normalizar(leer_corte(archivo))))
    validos = identificar(validos.lazy()).collect()

    cargar_staging(conn, validos, rechazados)
    registrar_rechazados(conn, rechazados, archivo.name)
    cambios = consolidar(conn, orden)
    verificar(conn, validos.height, cambios)
    registrar_control(conn, archivo.name, orden, validos.height, rechazados.height, cambios)

    log.info(
        "%s | válidos=%d rechazados=%d | %s | %.1fs",
        archivo.name, validos.height, rechazados.height, cambios, time.perf_counter() - inicio,
    )


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with conectar(autocommit=True) as conn:
        ejecutar_sql(conn, "ddl.sql")

        procesados = cortes_procesados(conn)
        ultimo = ultimo_corte(conn)
        pendientes = [(o, a) for o, a in listar_cortes() if a.name not in procesados]

        if not pendientes:
            log.info("No hay cortes nuevos para procesar")

        for orden, archivo in pendientes:
            if orden <= ultimo:
                raise RuntimeError(
                    f"{archivo.name} (corte {orden}) es anterior al último procesado ({ultimo})"
                )
            with conn.transaction():
                procesar_corte(conn, orden, archivo)
            ultimo = orden


if __name__ == "__main__":
    main()