"""
Tool: Metric Aggregator
Computes statistical summaries, rolling averages, and % changes for metric
time-series data. Called programmatically by the Data Analyst Agent.
"""

import statistics
from typing import Any


def aggregate_metric(series: list[dict], metric_name: str) -> dict[str, Any]:
    """
    Aggregate a single metric's time series.

    Args:
        series: List of dicts with keys: day, date, value, phase
        metric_name: Human-readable label for logging

    Returns:
        Dict with pre/post stats, % change, trend direction
    """
    pre_values = [p["value"] for p in series if p["phase"] == "pre" and p["value"] is not None]
    post_values = [p["value"] for p in series if p["phase"] == "post" and p["value"] is not None]

    def _stats(vals: list) -> dict:
        if not vals:
            return {}
        return {
            "mean": round(statistics.mean(vals), 3),
            "min": round(min(vals), 3),
            "max": round(max(vals), 3),
            "stdev": round(statistics.stdev(vals), 3) if len(vals) > 1 else 0.0,
            "p95": round(sorted(vals)[int(0.95 * len(vals)) - 1], 3),
            "latest": round(vals[-1], 3),
        }

    pre_stats = _stats(pre_values)
    post_stats = _stats(post_values)

    pct_change = None
    if pre_stats.get("mean") and post_stats.get("mean"):
        delta = post_stats["mean"] - pre_stats["mean"]
        pct_change = round((delta / pre_stats["mean"]) * 100, 2)

    # Determine trend: last 3 post values ascending/descending?
    trend = "stable"
    if len(post_values) >= 3:
        last3 = post_values[-3:]
        if last3[-1] > last3[0] * 1.02:
            trend = "increasing"
        elif last3[-1] < last3[0] * 0.98:
            trend = "decreasing"

    return {
        "metric_name": metric_name,
        "pre_launch": pre_stats,
        "post_launch": post_stats,
        "pct_change": pct_change,
        "trend": trend,
        "direction": "up" if (pct_change or 0) > 0 else "down",
    }


def aggregate_all_metrics(metrics_data: dict) -> dict[str, Any]:
    """
    Run aggregate_metric on all metrics in the dataset.

    Args:
        metrics_data: Full metrics JSON dict

    Returns:
        Dict mapping metric_key -> aggregation result
    """
    results = {}
    for key, metric in metrics_data["metrics"].items():
        result = aggregate_metric(metric["data"], metric["label"])
        result["unit"] = metric.get("unit", "")
        result["baseline_target"] = metric.get("baseline_target")
        result["alert_threshold"] = metric.get("alert_threshold")
        results[key] = result
    return results
