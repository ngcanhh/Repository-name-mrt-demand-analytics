"""Descriptive summaries using every month in the supplied data scope."""

import pandas as pd


def station_activity(data: pd.DataFrame) -> pd.DataFrame:
    """Combine codes sharing a display name; retain their code and line labels."""
    return (
        data.groupby("station_name", as_index=False)
        .agg(total_volume=("total_volume", "sum"),
             station_codes=("station_code", lambda codes: ", ".join(sorted(set(codes)))),
             line_name=("line_name", lambda lines: " | ".join(sorted(set(lines.str.strip())))))
        .sort_values(["total_volume", "station_name"], ascending=[False, True])
        .reset_index(drop=True)
    )


def hourly_activity(data: pd.DataFrame) -> pd.DataFrame:
    return (data.groupby(["hour", "day_type"], as_index=False)["total_volume"]
            .sum().sort_values(["day_type", "hour"]))


def build_review_priorities(data: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    """Rank named stations by recorded activity, then describe their peak windows.

    Peak windows use each station's weekday records (or the selected day types
    if weekdays are absent). Volume alone does not establish a capacity problem.
    """
    ranked = station_activity(data).head(limit).copy()
    data = data.assign(month_label=pd.to_datetime(data["year_month"]).dt.strftime("%Y-%m"))
    ranked.insert(0, "review_rank", range(1, len(ranked) + 1))
    results = []
    for row in ranked.to_dict("records"):
        station = data[data["station_name"].eq(row["station_name"])]
        weekday = station[station["day_type"].eq("weekday")]
        scope = weekday if not weekday.empty else station
        by_hour = scope.groupby("hour")["total_volume"].sum().sort_index()
        peak = int(by_hour.idxmax())
        row.update(
            months_observed=station["month_label"].nunique(),
            activity_share_pct=(row["total_volume"] / data["total_volume"].sum() * 100
                                if data["total_volume"].sum() > 0 else 0.0),
            peak_day_type="weekday" if not weekday.empty else "selected day types",
            peak_hour=peak,
            peak_hour_activity=int(by_hour.loc[peak]),
            peak_hour_share_pct=by_hour.loc[peak] / by_hour.sum() * 100 if by_hour.sum() > 0 else 0.0,
        )
        results.append(row)
    return pd.DataFrame(results)
