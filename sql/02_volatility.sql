-- Annualised volatility of each AUD pair: stdev of daily log returns x sqrt(252).
-- SQLite has no STDEV, so variance = E[x^2] - E[x]^2 (population), with LN() from the math extension.
WITH returns AS (
    SELECT quote, date,
           LN(rate / LAG(rate) OVER (PARTITION BY quote ORDER BY date)) AS r
    FROM fx_rates WHERE base = 'AUD'
)
SELECT quote,
       COUNT(r) AS trading_days,
       ROUND(100.0 * SQRT(AVG(r * r) - AVG(r) * AVG(r)) * SQRT(252), 2) AS annual_vol_pct,
       ROUND(100.0 * MIN(r), 2) AS worst_day_pct,
       ROUND(100.0 * MAX(r), 2) AS best_day_pct
FROM returns
WHERE r IS NOT NULL
GROUP BY quote
ORDER BY annual_vol_pct DESC;
