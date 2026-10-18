from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DATA_PATH = Path("data/processed/mrt_station_demand_multi_month_enriched.csv")
FORECAST_PATH = Path("outputs/tables/monthly_activity_forecast.csv")


st.set_page_config(
    page_title="Singapore MRT Demand Analytics",
    page_icon="🚆",
    layout="wide",
)


@st.cache_data
def load_data() -> pd.DataFrame:
    data = pd.read_csv(DATA_PATH)
    data["year_month"] = pd.to_datetime(data["year_month"])
    data["month_label"] = data["year_month"].dt.strftime("%Y-%m")
    return data


@st.cache_data
def load_forecast() -> pd.DataFrame:
    if not FORECAST_PATH.exists():
        return pd.DataFrame()
    forecast = pd.read_csv(FORECAST_PATH)
    forecast["year_month"] = pd.to_datetime(forecast["year_month"])
    forecast["month_label"] = forecast["year_month"].dt.strftime("%Y-%m")
    return forecast


data = load_data()
forecast = load_forecast()


def format_compact(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"

st.title("Singapore MRT Demand & Station Operations Analytics")
st.caption(
    "Interactive analysis using LTA DataMall passenger volume data. "
    "Activity = tap-ins + tap-outs; it measures station entries/exits, not unique passengers."
)

st.sidebar.header("Filters")
months = sorted(data["month_label"].unique())
selected_months = st.sidebar.multiselect(
    "Month",
    options=months,
    default=months,
)

lines = sorted(data["line_name"].dropna().unique())
selected_lines = st.sidebar.multiselect(
    "MRT line",
    options=lines,
    default=lines,
)

day_types = sorted(data["day_type"].dropna().unique())
selected_day_types = st.sidebar.multiselect(
    "Day type",
    options=day_types,
    default=day_types,
)

filtered = data[
    data["month_label"].isin(selected_months)
    & data["line_name"].isin(selected_lines)
    & data["day_type"].isin(selected_day_types)
].copy()

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

total_activity = filtered["total_volume"].sum()
station_count = filtered["station_code"].nunique()
peak_by_hour = filtered.groupby("hour", as_index=False)["total_volume"].sum()
peak_hour = int(peak_by_hour.loc[peak_by_hour["total_volume"].idxmax(), "hour"])
top_station = (
    filtered.groupby("station_name", as_index=False)["total_volume"]
    .sum()
    .sort_values("total_volume", ascending=False)
    .iloc[0]["station_name"]
)
top_station_activity = (
    filtered.groupby("station_name")["total_volume"].sum().max()
)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("Total activity", format_compact(total_activity))
metric_2.metric("Stations covered", f"{station_count:,}")
metric_3.metric("Peak hour", f"{peak_hour:02d}:00")
metric_4.metric(
    "Top station",
    f"{str(top_station)[:16]} ({format_compact(top_station_activity)})",
)

st.subheader("Key findings")
line_summary_for_findings = (
    filtered.groupby("line_name", as_index=False)["total_volume"]
    .sum()
    .sort_values("total_volume", ascending=False)
)
weekday_activity = filtered.loc[
    filtered["day_type"].eq("weekday"), "total_volume"
].sum()
weekend_activity = filtered.loc[
    filtered["day_type"].eq("weekends/holiday"), "total_volume"
].sum()
findings = [
    f"**{peak_hour:02d}:00** is the highest-demand hour in the selected data ({format_compact(peak_by_hour['total_volume'].max())} activity).",
    f"**{line_summary_for_findings.iloc[0]['line_name']}** has the highest activity among the selected lines ({format_compact(line_summary_for_findings.iloc[0]['total_volume'])}).",
]
if weekday_activity > weekend_activity > 0:
    weekday_share = weekday_activity / (weekday_activity + weekend_activity) * 100
    findings.append(
        f"Weekday activity represents **{weekday_share:.1f}%** of selected activity."
    )
for finding in findings:
    st.markdown(f"- {finding}")

st.divider()

left, right = st.columns(2)

with left:
    hourly = (
        filtered.groupby(["hour", "day_type"], as_index=False)["total_volume"]
        .sum()
    )
    fig_hourly = px.line(
        hourly,
        x="hour",
        y="total_volume",
        color="day_type",
        markers=True,
        title="MRT Activity by Hour",
        labels={"total_volume": "Tap-in + tap-out activity", "hour": "Hour"},
    )
    st.plotly_chart(fig_hourly, width="stretch")

with right:
    station_summary = (
        filtered.groupby(["station_name", "line_name"], as_index=False)["total_volume"]
        .sum()
        .sort_values("total_volume", ascending=False)
        .head(10)
    )
    fig_station = px.bar(
        station_summary.sort_values("total_volume"),
        x="total_volume",
        y="station_name",
        color="line_name",
        orientation="h",
        title="Top 10 MRT Stations",
        labels={"total_volume": "Activity", "station_name": "Station"},
    )
    st.plotly_chart(fig_station, width="stretch")

trend = filtered.groupby("month_label", as_index=False)["total_volume"].sum()
fig_trend = px.line(
    trend,
    x="month_label",
    y="total_volume",
    markers=True,
    title="Monthly MRT Activity Trend",
    labels={"total_volume": "Activity", "month_label": "Month"},
)
fig_trend.update_xaxes(type="category", categoryorder="category ascending")
st.plotly_chart(fig_trend, width="stretch")

coverage = (
    filtered.groupby("month_label")
    .agg(rows=("station_code", "size"), stations=("station_code", "nunique"))
    .reset_index()
    .sort_values("month_label")
)
if len(coverage) >= 2:
    previous_coverage = coverage.iloc[-2]
    latest_coverage = coverage.iloc[-1]
    if latest_coverage["stations"] < previous_coverage["stations"] * 0.95:
        st.warning(
            f"The latest month ({latest_coverage['month_label']}) covers "
            f"{int(latest_coverage['stations'])} stations versus "
            f"{int(previous_coverage['stations'])} in the previous month. "
            "Treat month-over-month decreases as provisional until LTA coverage is confirmed."
        )
    else:
        st.caption(
            f"Latest comparison coverage: {int(latest_coverage['stations'])} stations "
            f"and {int(latest_coverage['rows']):,} station-hour records in {latest_coverage['month_label']}."
        )

if not forecast.empty:
    st.subheader("Baseline next-month forecast")
    st.caption(
        "Network-wide forecast based on all available months; it does not change with the selected line or day-type filters."
    )
    fig_forecast = px.line(
        forecast,
        x="month_label",
        y="activity",
        color="record_type",
        markers=True,
        title="Actual activity and baseline forecast",
        labels={"activity": "Activity", "month_label": "Month", "record_type": "Series"},
    )
    fig_forecast.update_xaxes(type="category", categoryorder="category ascending")
    st.plotly_chart(fig_forecast, width="stretch")
    st.caption(
        "The forecast is a transparent linear-trend baseline and should not be treated as a production prediction model."
    )

st.subheader("Monthly movement alerts")
trend_months = sorted(filtered["month_label"].unique())
if len(trend_months) >= 2:
    previous_label, latest_label = trend_months[-2:]
    station_monthly = (
        filtered.groupby(["month_label", "station_name", "line_name"], as_index=False)[
            "total_volume"
        ]
        .sum()
        .pivot_table(
            index=["station_name", "line_name"],
            columns="month_label",
            values="total_volume",
        )
        .reset_index()
    )
    station_monthly["absolute_change"] = (
        station_monthly[latest_label] - station_monthly[previous_label]
    )
    station_monthly["percent_change"] = station_monthly.apply(
        lambda row: row["absolute_change"] / row[previous_label] * 100
        if row[previous_label] > 0
        else None,
        axis=1,
    )
    movement = station_monthly.dropna(
        subset=[previous_label, latest_label, "percent_change"]
    )
    increase, decrease = st.columns(2)
    with increase:
        st.markdown(f"**Largest increases: {previous_label} → {latest_label}**")
        st.dataframe(
            movement.sort_values("percent_change", ascending=False)
            [["station_name", "line_name", "percent_change", "absolute_change"]]
            .head(5)
            .assign(
                percent_change=lambda frame: frame["percent_change"].round(1),
                absolute_change=lambda frame: frame["absolute_change"].round(0),
            )
            .rename(columns={"percent_change": "% change", "absolute_change": "Activity change"}),
            width="stretch",
            hide_index=True,
        )
    with decrease:
        st.markdown(f"**Largest decreases: {previous_label} → {latest_label}**")
        st.dataframe(
            movement.sort_values("percent_change")
            [["station_name", "line_name", "percent_change", "absolute_change"]]
            .head(5)
            .assign(
                percent_change=lambda frame: frame["percent_change"].round(1),
                absolute_change=lambda frame: frame["absolute_change"].round(0),
            )
            .rename(columns={"percent_change": "% change", "absolute_change": "Activity change"}),
            width="stretch",
            hide_index=True,
        )
else:
    st.info("Select at least two months to compare station movements.")

st.subheader("Recommended actions")

line_summary = (
    filtered.groupby("line_name", as_index=False)["total_volume"]
    .sum()
    .sort_values("total_volume", ascending=False)
)
top_line = line_summary.iloc[0]["line_name"]
recommendations = [
    f"Review capacity and disruption-readiness for **{top_line}**, the busiest selected line; high volume alone does not indicate an operational problem.",
    f"Use **{top_station}** as the first station for a deeper review of crowding, interchange flows and service conditions.",
]
if weekday_activity > weekend_activity > 0:
    recommendations.append(
        f"Check staffing coverage, queue conditions and service incidents around **{peak_hour:02d}:00** on weekdays, when demand is concentrated."
    )
else:
    recommendations.append(
        f"Check staffing coverage, queue conditions and service incidents around **{peak_hour:02d}:00**; volume alone does not confirm a staffing shortage."
    )

for recommendation in recommendations:
    st.markdown(f"- {recommendation}")

st.subheader("Filtered data export")
st.download_button(
    "Download filtered CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="mrt_filtered_analysis.csv",
    mime="text/csv",
)

st.caption(
    "total activity = tap-in volume + tap-out volume; this is station activity, not unique passenger counts."
)
