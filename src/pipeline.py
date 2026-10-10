from db import conectar, ejecutar_sql


def main():
    with conectar() as conn:
        ejecutar_sql(conn, "ddl.sql")
    print("Tablas listas")


if __name__ == "__main__":
    main()