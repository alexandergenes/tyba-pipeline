-- nombre: rechazos_por_motivo
SELECT r.archivo,
       r.motivo,
       COUNT(*) AS filas,
       ROUND(100.0 * COUNT(*) / c.filas_leidas, 2) AS pct_del_corte
FROM movimientos_rechazados r
JOIN control_cargas c USING (archivo)
GROUP BY r.archivo, r.motivo, c.filas_leidas
ORDER BY r.archivo, filas DESC;

-- nombre: completitud
SELECT COUNT(*) AS movimientos,
       ROUND(100.0 * COUNT(*) FILTER (WHERE description IS NULL) / COUNT(*), 2) AS pct_sin_descripcion,
       ROUND(100.0 * COUNT(*) FILTER (WHERE commercial_name IS NULL) / COUNT(*), 2) AS pct_sin_entidad,
       ROUND(100.0 * COUNT(*) FILTER (WHERE amount = 0) / COUNT(*), 2) AS pct_monto_cero
FROM movimientos_actual;

-- nombre: rotacion_entre_cortes
SELECT archivo,
       sin_cambios + corregidos + eliminados + protegidos AS base_anterior,
       nuevos, corregidos, eliminados, protegidos,
       ROUND(100.0 * nuevos / NULLIF(sin_cambios + corregidos + eliminados + protegidos, 0), 2) AS pct_nuevos,
       ROUND(100.0 * corregidos / NULLIF(sin_cambios + corregidos + eliminados + protegidos, 0), 2) AS pct_corregidos,
       ROUND(100.0 * eliminados / NULLIF(sin_cambios + corregidos + eliminados + protegidos, 0), 2) AS pct_eliminados
FROM control_cargas
ORDER BY orden_corte;

-- nombre: cambios_por_fecha_del_movimiento
SELECT h.corte_desde AS corte,
       h.date,
       COUNT(*) FILTER (WHERE NOT h.eliminado AND a.id IS NULL) AS nuevos,
       COUNT(*) FILTER (WHERE h.eliminado) AS eliminados
FROM movimientos_historico h
LEFT JOIN movimientos_historico a
  ON  a.corte_hasta = h.corte_desde
  AND NOT a.eliminado
  AND a.id_cliente = h.id_cliente
  AND a.date = h.date
  AND a.product = h.product
  AND a.fund = h.fund
  AND a.type = h.type
  AND a.secuencia = h.secuencia
WHERE h.corte_desde > 0
GROUP BY h.corte_desde, h.date
ORDER BY corte, h.date;

-- nombre: impacto_correcciones
SELECT nueva.corte_desde AS corte,
       COUNT(*) AS correcciones,
       COUNT(*) FILTER (WHERE nueva.amount <> anterior.amount) AS cambiaron_monto,
       SUM(nueva.amount - anterior.amount) AS variacion_neta,
       SUM(ABS(nueva.amount - anterior.amount)) AS variacion_absoluta
FROM movimientos_historico nueva
JOIN movimientos_historico anterior
  ON  anterior.id_cliente = nueva.id_cliente
  AND anterior.date = nueva.date
  AND anterior.product = nueva.product
  AND anterior.fund = nueva.fund
  AND anterior.type = nueva.type
  AND anterior.secuencia = nueva.secuencia
  AND anterior.corte_hasta = nueva.corte_desde
WHERE NOT nueva.eliminado
  AND NOT anterior.eliminado
GROUP BY nueva.corte_desde
ORDER BY corte;

-- nombre: eliminaciones
SELECT corte_desde AS corte,
       type,
       COUNT(*) AS movimientos,
       SUM(amount) AS monto_total
FROM movimientos_historico
WHERE eliminado
GROUP BY corte_desde, type
ORDER BY corte, type;

-- nombre: descripcion_vs_tipo
SELECT COALESCE(description, '(sin descripción)') AS description,
       COUNT(*) FILTER (WHERE type = 'entrada') AS entradas,
       COUNT(*) FILTER (WHERE type = 'salida') AS salidas,
       ROUND(100.0 * COUNT(*) FILTER (WHERE type = 'entrada') / COUNT(*), 1) AS pct_entradas
FROM movimientos_actual
GROUP BY description
ORDER BY description NULLS LAST;

------------------------------------------------------------------------------------------------------------

-- nombre: flujo_por_fondo
SELECT fund,
       SUM(amount) FILTER (WHERE type = 'entrada') AS entradas,
       SUM(amount) FILTER (WHERE type = 'salida') AS salidas,
       SUM(CASE WHEN type = 'entrada' THEN amount ELSE -amount END) AS flujo_neto
FROM movimientos_actual
GROUP BY fund
ORDER BY flujo_neto DESC;

-- nombre: flujo_por_producto
SELECT product,
       SUM(amount) FILTER (WHERE type = 'entrada') AS entradas,
       SUM(amount) FILTER (WHERE type = 'salida') AS salidas,
       SUM(CASE WHEN type = 'entrada' THEN amount ELSE -amount END) AS flujo_neto
FROM movimientos_actual
GROUP BY product
ORDER BY flujo_neto DESC;

-- nombre: evolucion_diaria
SELECT date,
       SUM(amount) FILTER (WHERE type = 'entrada') AS entradas,
       SUM(amount) FILTER (WHERE type = 'salida') AS salidas,
       SUM(CASE WHEN type = 'entrada' THEN amount ELSE -amount END) AS flujo_neto
FROM movimientos_actual
GROUP BY date
ORDER BY date;

-- nombre: concentracion_por_clientes
WITH por_cliente AS (
    SELECT id_cliente, SUM(amount) AS volumen
    FROM movimientos_actual
    GROUP BY id_cliente
),
deciles AS (
    SELECT volumen, NTILE(10) OVER (ORDER BY volumen DESC) AS decil
    FROM por_cliente
)
SELECT decil,
       COUNT(*) AS clientes,
       SUM(volumen) AS volumen,
       ROUND(100.0 * SUM(volumen) / SUM(SUM(volumen)) OVER (), 2) AS pct_volumen,
       ROUND(100.0 * SUM(SUM(volumen)) OVER (ORDER BY decil) / SUM(SUM(volumen)) OVER (), 2) AS pct_acumulado
FROM deciles
GROUP BY decil
ORDER BY decil;

-- nombre: participacion_por_entidad
SELECT COALESCE(commercial_name, '(sin entidad)') AS entidad,
       COUNT(*) AS movimientos,
       SUM(amount) AS volumen,
       ROUND(100.0 * SUM(amount) / SUM(SUM(amount)) OVER (), 2) AS pct_volumen
FROM movimientos_actual
GROUP BY commercial_name
ORDER BY volumen DESC;