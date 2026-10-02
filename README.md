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
- Current analysis period: August 2026
- Granularity: station, hour, and day type
- Measures: total tap-in volume and total tap-out volume

`total_volume` is defined as:

```text
tap-in volume + tap-out volume
```

It represents station activity, not unique passenger counts.

## Key findings from August 2026

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

## Project structure

```text
data/       Raw and processed data
src/        Data download, cleaning, mapping and analysis scripts
outputs/    Summary tables and charts
dashboard/  Power BI dashboard
notebooks/  Exploratory notebooks
sql/        SQL analysis files
```

## Limitations

- The current dashboard covers one month only.
- Activity is measured as combined tap-in and tap-out volume.
- The data does not represent unique passengers.
- A few newer station codes were assigned inferred line labels when they were not available in the older station reference file.

## Future improvements

- Download and combine multiple months through the LTA API.
- Add month-over-month growth analysis.
- Add a refreshable data pipeline.
- Deploy the dashboard as a Streamlit web application.
- Add weather and public holiday analysis.
