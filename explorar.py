import duckdb
duckdb.sql("SELECT * FROM 'data/raw/movimientos_dia_T.parquet'").show()