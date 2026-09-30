-- Budget-rate variance for an importer paying USD suppliers.
-- Assumption: each year's budget rate = the average AUD/USD of the previous December
-- (a common "set it before the year starts" practice). Monthly USD spend is a
-- parameter (:usd_spend). A negative variance means AUD bought fewer USD than
-- budgeted, so the same invoices cost more AUD.
WITH monthly AS (
    SELECT substr(date, 1, 7) AS month, AVG(rate) AS actual_rate
    FROM fx_rates WHERE base = 'AUD' AND quote = 'USD'
    GROUP BY month
),
budget AS (
    SELECT CAST(substr(month, 1, 4) AS INTEGER) + 1 AS year, actual_rate AS budget_rate
    FROM monthly WHERE substr(month, 6, 2) = '12'
)
SELECT m.month,
       ROUND(b.budget_rate, 4) AS budget_rate,
       ROUND(m.actual_rate, 4) AS actual_rate,
       ROUND(:usd_spend / b.budget_rate, 0) AS budget_aud_cost,
       ROUND(:usd_spend / m.actual_rate, 0) AS actual_aud_cost,
       ROUND(:usd_spend / b.budget_rate - :usd_spend / m.actual_rate, 0) AS variance_aud
FROM monthly m
JOIN budget b ON b.year = CAST(substr(m.month, 1, 4) AS INTEGER)
ORDER BY m.month;
