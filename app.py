from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.forecast_monthly_activity import build_forecast
from src.analyze_monthly_growth import build_monthly_comparisons, monthly_coverage
from src.operations_review import build_review_priorities, hourly_activity, station_activity

DATA_PATH = Path(__file__).resolve().parent / "data/processed/mrt_station_demand_multi_month_enriched.csv"


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


data = load_data()


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

st.sidebar.markdown(
    "[Read the case study](https://github.com/ngcanhh/Repository-name-mrt-demand-analytics/blob/main/docs/operations-case-study.md)"
    " · [View source code](https://github.com/ngcanhh/Repository-name-mrt-demand-analytics)"
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
    "MRT/LRT line label",
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
metric_2.metric("Station codes covered", f"{station_count:,}")
metric_3.metric("Peak hour", f"{peak_hour:02d}:00")
metric_4.metric(
    "Top station",
    str(top_station),
    help=f"Recorded activity: {top_station_activity:,.0f}",
)
metric_4.caption(f"{format_compact(top_station_activity)} recorded activity")

scope_label = ", ".join(sorted(filtered["month_label"].unique()))
st.caption(
    f"Selected months: {scope_label}. KPIs, hourly activity and the top 10 combine all "
    "selected months, lines and day types. Monthly trends show each month separately. "
    "Station codes are source identifiers, not a count of unique physical stations."
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
    hourly = hourly_activity(filtered)
    fig_hourly = px.line(
        hourly,
        x="hour",
        y="total_volume",
        color="day_type",
        markers=True,
        title="MRT/LRT Activity by Hour",
        labels={"total_volume": "Tap-in + tap-out activity", "hour": "Hour"},
    )
    st.plotly_chart(fig_hourly, width="stretch")

with right:
    station_summary = station_activity(filtered).head(10)
    fig_station = px.bar(
        station_summary.sort_values("total_volume"),
        x="total_volume",
        y="station_name",
        color="line_name",
        orientation="h",
        title="Top 10 MRT/LRT Stations by Recorded Activity",
        hover_data=["station_codes"],
        category_orders={"station_name": station_summary["station_name"].tolist()},
        labels={"total_volume": "Activity", "station_name": "Station", "line_name": "Line label"},
    )
    st.plotly_chart(fig_station, width="stretch")

st.caption(
    "Both charts above sum every selected month; they do not show month-over-month growth. "
    "Hourly values are monthly totals by day type, not activity per individual day. "
    "The top 10 combines source codes that share the same station name."
)

st.subheader("Monthly activity and next-month forecast")
trend = (
    filtered.groupby("year_month", as_index=False)["total_volume"]
    .sum()
    .sort_values("year_month")
)
fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=trend["year_month"],
    y=trend["total_volume"],
    mode="lines+markers",
    name="Actual activity",
    line=dict(color="#0068c9"),
    hovertemplate="%{x|%Y-%m}<br>Actual activity: %{y:,.0f}<extra></extra>",
))
consecutive_months = pd.date_range(
    trend["year_month"].min(), trend["year_month"].max(), freq="MS"
)
has_forecast = len(trend) >= 3 and len(consecutive_months) == len(trend)
if has_forecast:
    # Reuse the pipeline model on exactly the same scope as the actual series.
    scoped_forecast = build_forecast(filtered)
    forecast_segment = scoped_forecast.iloc[-2:]
    fig_trend.add_trace(go.Scatter(
        x=forecast_segment["year_month"],
        y=forecast_segment["activity"],
        mode="lines+markers",
        name="Baseline forecast",
        line=dict(color="#e88b00", dash="dash"),
        marker=dict(symbol=["circle", "diamond"], size=[6, 10]),
        customdata=["Actual activity (forecast starting point)", "Baseline forecast"],
        hovertemplate="%{x|%Y-%m}<br>%{customdata}: %{y:,.0f}<extra></extra>",
    ))
fig_trend.update_layout(
    xaxis_title="Month",
    yaxis_title="Activity (tap-ins + tap-outs)",
    legend_title_text="Series",
)
fig_trend.update_xaxes(type="date", dtick="M1", tickformat="%Y-%m")
st.plotly_chart(fig_trend, width="stretch")
if has_forecast:
    st.caption(
        "Actual activity and forecast follow the selected months, lines and day types. "
        "The dashed segment connects the latest actual month to a one-month-ahead "
        "linear-trend baseline; it is exploratory and has not been validated for operational planning."
    )
else:
    st.caption(
        "Actual activity follows the selected filters. Select at least three consecutive "
        "months to also display a next-month baseline forecast."
    )

st.subheader("Monthly coverage and comparable growth")
st.caption(
    "Recorded totals include all available rows in each selected month. Growth compares "
    "only station codes present in both months with matching hour/day-type coverage. "
    "Each pair has its own comparable cohort; monthly totals are not adjusted for the "
    "number of weekdays, weekends or holidays."
)
coverage = monthly_coverage(filtered)
st.dataframe(
    coverage.rename(columns={"month_label": "Month", "station_codes": "Station codes",
                             "records": "Records", "recorded_activity": "Recorded activity"}),
    hide_index=True, width="stretch",
)
movement, comparisons = build_monthly_comparisons(filtered)
if not comparisons.empty:
    comparison_display = comparisons[[
        "previous_month", "latest_month", "common_codes", "comparable_codes",
        "previous_comparable_activity", "latest_comparable_activity", "percent_change",
    ]].rename(columns={
        "previous_month": "From", "latest_month": "To", "common_codes": "Codes in both months",
        "comparable_codes": "Comparable codes", "previous_comparable_activity": "Previous activity",
        "latest_comparable_activity": "Latest activity", "percent_change": "Change (%)",
    })
    st.dataframe(comparison_display.round({"Change (%)": 2}), hide_index=True, width="stretch")
    st.download_button(
        "Download all monthly comparisons", comparisons.to_csv(index=False).encode("utf-8"),
        "mrt_monthly_comparisons.csv", "text/csv",
    )

st.subheader("Monthly station movements")
if not comparisons.empty:
    labels = [f"{row.previous_month} → {row.latest_month}" for row in comparisons.itertuples()]
    selected_pair = st.selectbox("Month-over-month comparison", labels, index=len(labels) - 1)
    summary = comparisons.iloc[labels.index(selected_pair)]
    pair = movement[
        movement["previous_month"].eq(summary["previous_month"])
        & movement["latest_month"].eq(summary["latest_month"])
    ]
    st.caption(
        f"{int(summary['comparable_codes'])} comparable codes out of "
        f"{int(summary['previous_codes'])} previous / {int(summary['latest_codes'])} latest codes. "
        f"Excluded: {int(summary['previous_only_codes'])} previous-only, "
        f"{int(summary['latest_only_codes'])} latest-only, and "
        f"{int(summary['changed_hour_coverage_codes'])} with changed hour/day-type coverage. "
        "Rankings are by source code; codes sharing a station name remain separate here. "
        "A zero baseline has no percentage change."
    )
    comparable = pair[pair["growth_quality"].eq("comparable")]
    increase, decrease = st.columns(2)
    for column, title, rows in [
        (increase, "Largest increases", comparable[comparable["percent_change"] > 0]
         .sort_values(["percent_change", "station_code"], ascending=[False, True]).head(5)),
        (decrease, "Largest decreases", comparable[comparable["percent_change"] < 0]
         .sort_values(["percent_change", "station_code"]).head(5)),
    ]:
        with column:
            st.markdown(f"**{title}: {selected_pair}**")
            if rows.empty:
                st.info("No comparable station codes in this direction.")
            else:
                st.dataframe(
                    rows[["station_code", "station_name", "percent_change", "absolute_change"]]
                    .round({"percent_change": 1, "absolute_change": 0})
                    .rename(columns={"station_code": "Code", "station_name": "Station",
                                     "percent_change": "% change", "absolute_change": "Activity change"}),
                    width="stretch", hide_index=True,
                )
    st.download_button(
        "Download station movements for this pair", pair.to_csv(index=False).encode("utf-8"),
        "mrt_station_movements.csv", "text/csv",
    )
else:
    st.info("Select at least two consecutive calendar months to compare station movements. "
            "Months separated by a gap are not treated as month-over-month growth.")

st.subheader("Stations and hours to review")
st.caption(
    "Priorities use recorded activity across every selected month. "
    "Peak-hour share is the fraction of a station's weekday activity at that hour "
    "(or selected day types if weekdays are absent). Higher volume suggests where to "
    "investigate; it does not establish crowding or a staffing shortage."
)
priorities = build_review_priorities(filtered)
priority_display = priorities[[
    "review_rank", "station_name", "total_volume", "months_observed", "peak_day_type",
    "peak_hour", "peak_hour_share_pct",
]].copy()
priority_display["peak_hour"] = priority_display["peak_hour"].map(lambda hour: f"{hour:02d}:00–{hour + 1:02d}:00")
st.dataframe(
    priority_display.round({"peak_hour_share_pct": 1}).rename(columns={
        "review_rank": "Priority", "station_name": "Station", "total_volume": "Recorded activity",
        "months_observed": "Months observed", "peak_day_type": "Peak day type",
        "peak_hour": "Review window", "peak_hour_share_pct": "Peak-hour share (%)",
    }), hide_index=True, width="stretch",
)

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
