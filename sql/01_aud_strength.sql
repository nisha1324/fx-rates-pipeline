-- How much stronger or weaker is AUD against each currency since the start of the history?
-- Rates are "units of quote currency per 1 AUD": a higher rate means a stronger AUD.
WITH bounds AS (
    SELECT quote, MIN(date) AS first_date, MAX(date) AS last_date
    FROM fx_rates WHERE base = 'AUD' GROUP BY quote
)
SELECT b.quote,
       b.first_date,
       f.rate AS first_rate,
       b.last_date,
       l.rate AS last_rate,
       ROUND(100.0 * (l.rate / f.rate - 1), 2) AS pct_change
FROM bounds b
JOIN fx_rates f ON f.quote = b.quote AND f.date = b.first_date AND f.base = 'AUD'
JOIN fx_rates l ON l.quote = b.quote AND l.date = b.last_date  AND l.base = 'AUD'
ORDER BY pct_change DESC;
