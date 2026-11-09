# Singapore MRT Demand & Station Operations Analytics

## Project overview

This project analyzes Singapore MRT station activity using passenger volume data from LTA DataMall. The goal is to identify high-demand stations, peak operating hours, and lines that may require operational attention.

## Business questions

- Which MRT stations have the highest passenger activity?
- What are the busiest hours on weekdays and weekends/holidays?
- Which MRT lines account for the largest share of activity?
- Which stations should be prioritized for operational monitoring?

## Data

- Source: LTA DataMall
- Dataset: Passenger Volume by Train Stations
- Coverage starts in June 2026 and expands as additional LTA monthly data is published and successfully processed. The app's Month filter shows the months currently available.
- Latest processed coverage and row counts are recorded in [`outputs/tables/data_quality_report.csv`](outputs/tables/data_quality_report.csv).
- Granularity: station, hour, and day type
- Measures: total tap-in volume and total tap-out volume

`total_volume` is defined as:

```text
tap-in volume + tap-out volume
```

It represents station activity, not unique passenger counts.

## Key findings from the current analysis period

- Jurong East recorded the highest total station activity.
- Orchard and Woodlands were also among the highest-activity stations.
- East-West Line recorded the highest total activity among the lines analyzed.
- Weekday activity was substantially higher than weekend/holiday activity.
- Weekday demand showed clear morning and evening peaks, with the strongest peak around 18:00.
- Weekend/holiday activity was concentrated mainly in the afternoon and early evening.

## Dashboard

The Power BI dashboard includes:

- Total MRT activity KPI
- Number of stations covered
- Activity by hour and day type
- Top 10 MRT stations by activity
- Activity by MRT line
- Filters for line and day type

### Dashboard preview

#### August 2026 snapshot

![August 2026 MRT dashboard](outputs/figures/dashboard_snapshot.png)

#### Monthly trends

![Monthly MRT trends dashboard](outputs/figures/monthly_trends.png)

## Interactive web app

The project also includes a Streamlit analytics application. The app recalculates KPIs, peak hour, station rankings, monthly trends, station movement alerts and operational recommendations based on the selected month, MRT line and day type.

The data pipeline includes automated quality checks for required columns, missing station metadata, negative volumes and the total-volume calculation. A GitHub Actions workflow can download the latest available month, rebuild the processed tables and publish the updated outputs.

The repository also includes business-focused SQL queries, automated analytics tests and a transparent baseline forecast for the next month. The forecast is intentionally a simple linear-trend baseline because the current dataset contains only a short time series; it is not presented as a production prediction model.

Monthly actual activity and the next-month forecast appear in one chart. Both use the selected months, MRT lines and day types. A dashed segment connects the last observed month to the forecast; a forecast is displayed only when at least three consecutive months are selected. With fewer months or gaps in the selection, the chart displays actual activity only. The forecast has not been validated for operational planning.

### Live app

[Open the Singapore MRT Demand Analytics app](https://repository-name-mrt-demand-analytics-kaxxjaulszrvzwrrkdat6s.streamlit.app/)

Run locally:

```powershell
pip install -r requirements.txt
streamlit run app.py
```

The app also supports downloading the currently filtered dataset as a CSV file.

### Automated update workflow

The monthly workflow runs on GitHub Actions and uses an `LTA_ACCOUNT_KEY` repository secret. It downloads the latest available LTA month, combines all tracked monthly files, enriches station metadata, recalculates month-over-month growth and validates the resulting dataset before committing updated outputs.

The configured schedule runs on the 15th of each month at 02:00 UTC (10:00 Singapore time) and targets the previous calendar month. It can also be triggered manually. Coverage expands after a successful data update; if the download is unavailable or fails, existing coverage is retained. A successful workflow status alone does not confirm that a new month was added—check the Month filter or data-quality report. Historical months outside the available download window may require a separate archive or source.

### SQL analysis

Business queries are stored in `sql/mrt_business_queries.sql` and cover monthly activity, peak hours by day type, latest-month station ranking and line-level month-over-month movement. They can be run with DuckDB against the processed CSV.

## Project structure

```text
data/       Raw and processed data
src/        Data download, cleaning, mapping and analysis scripts
sql/        DuckDB business analysis queries
tests/      Automated data and forecast tests
outputs/    Summary tables and charts
dashboard/  Power BI dashboard
notebooks/  Exploratory notebooks
sql/        SQL analysis files
```

## Limitations

- Coverage is limited to monthly files successfully collected since June 2026; it is not a complete calendar-year dataset. The latest included month depends on LTA availability and successful pipeline runs, so coverage may lag the calendar date.
- The short time series and changes in station coverage limit month-over-month comparisons and forecast reliability. The linear-trend baseline does not model seasonality or establish the causes of demand changes.
- Activity is measured as combined tap-in and tap-out volume.
- The data does not represent unique passengers.
- A few newer station codes were assigned inferred line labels when they were not available in the older station reference file.

## Future improvements

- Extend the historical window as additional LTA months become available.
- Replace the baseline forecast with a validated time-series model after a longer history is available.
- Add weather and public holiday analysis.
