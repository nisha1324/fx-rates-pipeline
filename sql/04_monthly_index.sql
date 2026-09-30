-- Monthly average rate per currency, for the strength index chart.
SELECT substr(date, 1, 7) AS month, quote, AVG(rate) AS avg_rate
FROM fx_rates WHERE base = 'AUD'
GROUP BY month, quote
ORDER BY month, quote;
