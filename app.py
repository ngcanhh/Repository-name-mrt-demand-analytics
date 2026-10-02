from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DATA_PATH = Path("data/processed/mrt_station_demand_multi_month_enriched.csv")
GROWTH_PATH = Path("outputs/tables/station_monthly_growth.csv")


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
def load_growth() -> pd.DataFrame:
    return pd.read_csv(GROWTH_PATH)


data = load_data()
growth = load_growth()


def format_compact(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"

st.title("Singapore MRT Demand & Station Operations Analytics")
st.caption("Interactive analysis using LTA DataMall passenger volume data")

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

metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("Total activity", format_compact(total_activity))
metric_2.metric("Stations covered", f"{station_count:,}")
metric_3.metric("Peak hour", f"{peak_hour:02d}:00")
metric_4.metric("Top station", str(top_station)[:18])

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
st.plotly_chart(fig_trend, width="stretch")

st.subheader("Operational recommendations")

line_summary = (
    filtered.groupby("line_name", as_index=False)["total_volume"]
    .sum()
    .sort_values("total_volume", ascending=False)
)
top_line = line_summary.iloc[0]["line_name"]
weekday_activity = filtered.loc[
    filtered["day_type"].eq("weekday"), "total_volume"
].sum()
weekend_activity = filtered.loc[
    filtered["day_type"].eq("weekends/holiday"), "total_volume"
].sum()

recommendations = [
    f"Prioritize monitoring for **{top_line}**, which has the highest activity under the current filters.",
    f"Focus operational resources around **{peak_hour:02d}:00**, the highest-demand hour in the selected data.",
    f"Monitor **{top_station}**, currently the highest-activity station under the selected filters.",
]
if weekday_activity > weekend_activity > 0:
    recommendations.append(
        "Weekday activity is higher than weekend/holiday activity; prioritize weekday peak-period staffing."
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

st.subheader("Station month-over-month growth")
growth_view = growth[growth["growth_quality"] == "reliable"].copy()
growth_view = growth_view[growth_view["line_name"].isin(selected_lines)]
growth_view["percent_change"] = growth_view["percent_change"].round(2)
st.dataframe(
    growth_view[
        ["station_name", "line_name", "percent_change", "absolute_change"]
    ].sort_values("percent_change", ascending=False),
    width="stretch",
    hide_index=True,
)

st.caption(
    "total activity = tap-in volume + tap-out volume; this is station activity, not unique passenger counts."
)
