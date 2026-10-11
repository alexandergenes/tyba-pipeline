import polars as pl

from etl.extraccion import COLUMNAS

TIPOS = {
    "entrada": "entrada",
    "in": "entrada",
    "salida": "salida",
    "out": "salida",
}

LLAVE = ["id_cliente", "date", "product", "fund", "type"]

def _texto(col):
    limpio = pl.col(col).str.replace_all(r"\s+", " ").str.strip_chars()
    return pl.when(limpio == "").then(None).otherwise(limpio)


def normalizar(lf: pl.LazyFrame) -> pl.LazyFrame:
    fecha = _texto("date")

    return lf.with_columns(
        _texto("id_cliente").str.to_uppercase().alias("_id_cliente"),
        pl.coalesce(
            fecha.str.to_date("%Y-%m-%d", strict=False),
            fecha.str.to_date("%d/%m/%Y", strict=False),
        ).alias("_date"),
        _texto("product").alias("_product"),
        _texto("type").str.to_lowercase().replace_strict(TIPOS, default=None).alias("_type"),
        _texto("fund").str.to_lowercase().str.to_titlecase().alias("_fund"),
        pl.col("amount").alias("_amount"),
        _texto("description").alias("_description"),
        _texto("commercial_name").alias("_commercial_name"),
    )


def validar(lf: pl.LazyFrame):
    reglas = [
        pl.when(~pl.col("_id_cliente").str.contains(r"^CLI\d{6}$").fill_null(False))
        .then(pl.lit("id_cliente_invalido")),
        pl.when(pl.col("_date").is_null()).then(pl.lit("fecha_invalida")),
        pl.when(pl.col("_product").is_null()).then(pl.lit("product_nulo")),
        pl.when(pl.col("_type").is_null()).then(pl.lit("type_invalido")),
        pl.when(pl.col("_fund").is_null()).then(pl.lit("fund_nulo")),
        pl.when(pl.col("_amount").is_null() | pl.col("_amount").is_nan())
        .then(pl.lit("amount_nulo")),
        pl.when(pl.col("_amount") < 0).then(pl.lit("amount_negativo")),
    ]

    lf = lf.with_columns(
        pl.concat_str(reglas, separator=";", ignore_nulls=True).fill_null("").alias("motivo")
    )
    es_valido = pl.col("motivo") == ""

    validos = lf.filter(es_valido).select([pl.col(f"_{c}").alias(c) for c in COLUMNAS])
    rechazados = lf.filter(~es_valido).select(
        [*COLUMNAS, "motivo", *[f"_{c}" for c in LLAVE]])
    return validos, rechazados


def identificar(lf: pl.LazyFrame) -> pl.LazyFrame:
    # El origen no trae id de transacción: los movimientos que comparten llave
    # se diferencian por una secuencia ordenada por sus atributos
    return lf.sort(
        [*LLAVE, "amount", "description", "commercial_name"], nulls_last=True
    ).with_columns(
        pl.int_range(1, pl.len() + 1, dtype=pl.Int32).over(LLAVE).alias("secuencia")
    )