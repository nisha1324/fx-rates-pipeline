-- Which budget-rate policy forecasts USD supplier costs better?
--   annual    : budget rate = average AUD/USD of the previous December (as in 03)
--   quarterly : budget rate = average AUD/USD of the month before the quarter starts
--               (Dec for Q1, Mar for Q2, Jun for Q3, Sep for Q4)
-- Per month, both policies are scored on the AUD forecast error for :usd_spend of
-- invoices. Positive = actual cost came in under budget.
WITH monthly AS (
    SELECT substr(date, 1, 7) AS month, AVG(rate) AS actual_rate
    FROM fx_rates WHERE base = 'AUD' AND quote = 'USD'
    GROUP BY month
),
keyed AS (
    SELECT month, actual_rate,
           CAST(substr(month, 1, 4) AS INTEGER) AS yr,
           CAST(substr(month, 6, 2) AS INTEGER) AS mo
    FROM monthly
),
refs AS (
    SELECT k.month, k.actual_rate,
           printf('%04d-12', k.yr - 1) AS annual_ref,
           CASE WHEN k.mo <= 3 THEN printf('%04d-12', k.yr - 1)
                ELSE printf('%04d-%02d', k.yr, ((k.mo - 1) / 3) * 3) END AS quarterly_ref
    FROM keyed k
)
SELECT r.month,
       ROUND(a.actual_rate, 4) AS annual_budget_rate,
       ROUND(q.actual_rate, 4) AS quarterly_budget_rate,
       ROUND(r.actual_rate, 4) AS actual_rate,
       ROUND(:usd_spend / a.actual_rate - :usd_spend / r.actual_rate, 0) AS annual_error_aud,
       ROUND(:usd_spend / q.actual_rate - :usd_spend / r.actual_rate, 0) AS quarterly_error_aud
FROM refs r
JOIN monthly a ON a.month = r.annual_ref
JOIN monthly q ON q.month = r.quarterly_ref
ORDER BY r.month;
