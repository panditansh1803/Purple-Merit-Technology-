"""
Tool: Trend Comparator
Compares pre-launch (days 1-7) vs. post-launch (days 8-14) windows for
each metric and produces a comparison table with status flags.
Called by the Data Analyst Agent.
"""

import statistics
from typing import Any


def _classify_metric_direction(metric_key: str) -> str:
    """
    Returns 'higher_is_better' or 'lower_is_better' for a given metric key.
    """
    lower_is_better = {
        "crash_rate", "api_latency_p95", "support_tickets",
    }
    return "lower_is_better" if metric_key in lower_is_better else "higher_is_better"


def compare_metric_trend(
    series: list[dict],
    metric_key: str,
    metric_label: str,
    baseline_target: float | None,
    alert_threshold: float | None,
) -> dict[str, Any]:
    """
    Compare pre-launch vs. post-launch for a single metric.

    Returns:
        Dict with pre/post means, delta, pct_change, status flag
    """
    pre_vals = [p["value"] for p in series if p["phase"] == "pre"]
    post_vals = [p["value"] for p in series if p["phase"] == "post"]

    if not pre_vals or not post_vals:
        return {"metric": metric_label, "status": "no_data"}

    pre_mean = statistics.mean(pre_vals)
    post_mean = statistics.mean(post_vals)
    delta = post_mean - pre_mean
    pct_change = round((delta / pre_mean) * 100, 2) if pre_mean != 0 else 0

    direction = _classify_metric_direction(metric_key)
    improvement = (direction == "higher_is_better" and delta > 0) or \
                  (direction == "lower_is_better" and delta < 0)
    degradation = not improvement and abs(pct_change) > 2

    # Status determination
    if alert_threshold is not None:
        if direction == "lower_is_better" and post_mean > alert_threshold:
            status = "CRITICAL"
        elif direction == "higher_is_better" and post_mean < alert_threshold:
            status = "CRITICAL"
        elif degradation and abs(pct_change) > 10:
            status = "WARNING"
        else:
            status = "OK"
    elif degradation and abs(pct_change) > 15:
        status = "WARNING"
    elif improvement:
        status = "OK"
    else:
        status = "WATCH"

    # Target vs actual (latest post value)
    latest_post = post_vals[-1]
    vs_target = None
    if baseline_target is not None:
        vs_target = round(((latest_post - baseline_target) / baseline_target) * 100, 2)

    return {
        "metric_key": metric_key,
        "metric_label": metric_label,
        "direction_preference": direction,
        "pre_mean": round(pre_mean, 3),
        "post_mean": round(post_mean, 3),
        "latest_value": round(latest_post, 3),
        "delta": round(delta, 3),
        "pct_change": pct_change,
        "baseline_target": baseline_target,
        "alert_threshold": alert_threshold,
        "vs_target_pct": vs_target,
        "improvement": improvement,
        "status": status,
    }


def compare_all_trends(metrics_data: dict) -> dict[str, Any]:
    """
    Run trend comparison for all metrics in the dataset.

    Returns:
        Dict with per-metric comparisons + summary roll-up
    """
    comparisons = {}
    critical_count = 0
    warning_count = 0

    for key, metric in metrics_data["metrics"].items():
        result = compare_metric_trend(
            series=metric["data"],
            metric_key=key,
            metric_label=metric["label"],
            baseline_target=metric.get("baseline_target"),
            alert_threshold=metric.get("alert_threshold"),
        )
        comparisons[key] = result
        if result.get("status") == "CRITICAL":
            critical_count += 1
        elif result.get("status") == "WARNING":
            warning_count += 1

    return {
        "comparisons": comparisons,
        "summary": {
            "critical_metrics": critical_count,
            "warning_metrics": warning_count,
            "ok_metrics": len(comparisons) - critical_count - warning_count,
        },
    }
