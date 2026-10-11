DROP TABLE IF EXISTS cambios;
CREATE TEMP TABLE cambios ON COMMIT DROP AS
SELECT *
FROM (
    SELECT
        COALESCE(s.id_cliente, h.id_cliente) AS id_cliente,
        COALESCE(s.date, h.date)             AS date,
        COALESCE(s.product, h.product)       AS product,
        COALESCE(s.fund, h.fund)             AS fund,
        COALESCE(s.type, h.type)             AS type,
        COALESCE(s.secuencia, h.secuencia)   AS secuencia,
        h.id AS id_version_actual,
        CASE
            WHEN s.id_cliente IS NULL AND h.eliminado THEN NULL
            WHEN h.id IS NULL OR h.eliminado THEN 'nuevo'
            WHEN s.id_cliente IS NULL AND r.id_cliente IS NOT NULL THEN 'protegido'
            WHEN s.id_cliente IS NULL THEN 'eliminado'
            WHEN (s.amount, s.description, s.commercial_name)
                 IS DISTINCT FROM (h.amount, h.description, h.commercial_name) THEN 'corregido'
            ELSE 'sin_cambios'
        END AS tipo
    FROM stg_movimientos s
    FULL JOIN (SELECT * FROM movimientos_historico WHERE es_actual) h
        ON  s.id_cliente = h.id_cliente
        AND s.date = h.date
        AND s.product = h.product
        AND s.fund = h.fund
        AND s.type = h.type
        AND s.secuencia = h.secuencia
    LEFT JOIN stg_llaves_rechazadas r
        ON  r.id_cliente = h.id_cliente
        AND r.date = h.date
        AND r.product = h.product
        AND r.fund = h.fund
        AND r.type = h.type
) clasificados
WHERE tipo IS NOT NULL;


UPDATE movimientos_historico h
SET es_actual = false,
    corte_hasta = current_setting('pipeline.corte')::int
FROM cambios c
WHERE h.id = c.id_version_actual
  AND c.tipo IN ('nuevo', 'corregido', 'eliminado');


INSERT INTO movimientos_historico (
    id_cliente, date, product, fund, type, secuencia,
    amount, description, commercial_name, corte_desde
)
SELECT s.id_cliente, s.date, s.product, s.fund, s.type, s.secuencia,
       s.amount, s.description, s.commercial_name,
       current_setting('pipeline.corte')::int
FROM stg_movimientos s
JOIN cambios c USING (id_cliente, date, product, fund, type, secuencia)
WHERE c.tipo IN ('nuevo', 'corregido');


INSERT INTO movimientos_historico (
    id_cliente, date, product, fund, type, secuencia,
    amount, description, commercial_name, corte_desde, eliminado
)
SELECT h.id_cliente, h.date, h.product, h.fund, h.type, h.secuencia,
       h.amount, h.description, h.commercial_name,
       current_setting('pipeline.corte')::int, true
FROM movimientos_historico h
JOIN cambios c ON h.id = c.id_version_actual
WHERE c.tipo = 'eliminado';