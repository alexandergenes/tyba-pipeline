CREATE TABLE IF NOT EXISTS control_cargas (
    archivo           TEXT PRIMARY KEY,
    orden_corte       INT NOT NULL,
    filas_leidas      INT NOT NULL,
    filas_validas     INT NOT NULL,
    filas_rechazadas  INT NOT NULL,
    nuevos            INT,
    corregidos        INT,
    eliminados        INT,
    sin_cambios       INT,
    procesado_en      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNLOGGED TABLE IF NOT EXISTS stg_movimientos (
    id_cliente       TEXT NOT NULL,
    date             DATE NOT NULL,
    product          TEXT NOT NULL,
    type             TEXT NOT NULL,
    fund             TEXT NOT NULL,
    amount           NUMERIC(18,2) NOT NULL,
    description      TEXT,
    commercial_name  TEXT,
    secuencia        INT NOT NULL
);

CREATE TABLE IF NOT EXISTS movimientos_rechazados (
    id               BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    motivo           TEXT NOT NULL,
    id_cliente       TEXT,
    date             TEXT,
    product          TEXT,
    type             TEXT,
    fund             TEXT,
    amount           DOUBLE PRECISION,
    description      TEXT,
    commercial_name  TEXT,
    rechazado_en     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNLOGGED TABLE IF NOT EXISTS stg_movimientos (
    id_cliente       TEXT NOT NULL,
    date             DATE NOT NULL,
    product          TEXT NOT NULL,
    type             TEXT NOT NULL,
    fund             TEXT NOT NULL,
    amount           NUMERIC(18,2) NOT NULL,
    description      TEXT,
    commercial_name  TEXT,
    secuencia        INT NOT NULL
);

CREATE TABLE IF NOT EXISTS movimientos_historico (
    id               BIGSERIAL PRIMARY KEY,
    id_cliente       TEXT NOT NULL,
    date             DATE NOT NULL,
    product          TEXT NOT NULL,
    fund             TEXT NOT NULL,
    type             TEXT NOT NULL,
    secuencia        INT NOT NULL,
    amount           NUMERIC(18,2) NOT NULL,
    description      TEXT,
    commercial_name  TEXT,
    corte_desde      INT NOT NULL,
    corte_hasta      INT,
    es_actual        BOOLEAN NOT NULL DEFAULT true,
    eliminado        BOOLEAN NOT NULL DEFAULT false
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_historico_actual
    ON movimientos_historico (id_cliente, date, product, fund, type, secuencia)
    WHERE es_actual;

CREATE OR REPLACE VIEW movimientos_actual AS
SELECT id_cliente, date, product, fund, type, secuencia,
       amount, description, commercial_name,
       corte_desde AS vigente_desde
FROM movimientos_historico
WHERE es_actual AND NOT eliminado;

CREATE UNLOGGED TABLE IF NOT EXISTS stg_llaves_rechazadas (
    id_cliente  TEXT NOT NULL,
    date        DATE NOT NULL,
    product     TEXT NOT NULL,
    fund        TEXT NOT NULL,
    type        TEXT NOT NULL
);