-- Singapore MRT business analysis queries
-- Run with DuckDB, for example:
-- duckdb mrt.duckdb -c ".read sql/mrt_business_queries.sql"

-- 1. Monthly network activity
SELECT
    year_month,
    SUM(total_volume) AS total_activity,
    COUNT(DISTINCT station_code) AS station_codes_covered
FROM read_csv_auto('data/processed/mrt_station_demand_multi_month_enriched.csv')
GROUP BY year_month
ORDER BY year_month;

-- 2. Peak hours by day type
SELECT
    day_type,
    hour,
    SUM(total_volume) AS activity
FROM read_csv_auto('data/processed/mrt_station_demand_multi_month_enriched.csv')
GROUP BY day_type, hour
QUALIFY ROW_NUMBER() OVER (PARTITION BY day_type ORDER BY activity DESC) <= 3
ORDER BY day_type, activity DESC;

-- 3. Top stations in the latest available month
WITH latest_month AS (
    SELECT MAX(year_month) AS month
    FROM read_csv_auto('data/processed/mrt_station_demand_multi_month_enriched.csv')
)
SELECT
    station_name,
    line_name,
    SUM(total_volume) AS activity
FROM read_csv_auto('data/processed/mrt_station_demand_multi_month_enriched.csv')
WHERE year_month = (SELECT month FROM latest_month)
GROUP BY station_name, line_name
ORDER BY activity DESC
LIMIT 10;

-- 4. All consecutive month pairs by line, on the exported comparable-code cohort.
-- Rebuild with: python src/analyze_monthly_growth.py
-- Missing station codes and changed hour/day-type coverage are excluded.
SELECT
    previous_month,
    latest_month,
    line_name,
    COUNT(DISTINCT station_code) AS comparable_codes,
    SUM(previous_activity) AS previous_activity,
    SUM(latest_activity) AS latest_activity,
    ROUND(100.0 * (SUM(latest_activity) - SUM(previous_activity))
          / NULLIF(SUM(previous_activity), 0), 2) AS percent_change
FROM read_csv_auto('outputs/tables/station_monthly_growth.csv')
WHERE growth_quality IN ('comparable', 'zero_baseline')
GROUP BY previous_month, latest_month, line_name
ORDER BY latest_month DESC, percent_change DESC;
