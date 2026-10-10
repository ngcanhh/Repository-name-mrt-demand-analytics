-- Singapore MRT business analysis queries
-- Run with DuckDB, for example:
-- duckdb mrt.duckdb -c ".read sql/mrt_business_queries.sql"

-- 1. Monthly network activity
SELECT
    year_month,
    SUM(total_volume) AS total_activity,
    COUNT(DISTINCT station_code) AS stations_covered
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

-- 4. Latest month-over-month line movement
WITH monthly AS (
    SELECT
        line_name,
        year_month,
        SUM(total_volume) AS activity
    FROM read_csv_auto('data/processed/mrt_station_demand_multi_month_enriched.csv')
    GROUP BY line_name, year_month
), ranked AS (
    SELECT
        *,
        LAG(activity) OVER (PARTITION BY line_name ORDER BY year_month) AS previous_activity
    FROM monthly
)
SELECT
    line_name,
    year_month,
    activity,
    previous_activity,
    ROUND(100.0 * (activity - previous_activity) / NULLIF(previous_activity, 0), 2) AS percent_change
FROM ranked
WHERE previous_activity IS NOT NULL
ORDER BY year_month DESC, percent_change DESC;
