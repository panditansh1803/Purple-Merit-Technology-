"""
Tool: Anomaly Detector
Uses z-score analysis to flag metrics that deviate significantly
from their pre-launch baseline. Called by the Data Analyst Agent.
"""

import statistics
import math
from typing import Any


def detect_anomalies(
    series: list[dict],
    metric_name: str,
    alert_threshold: float | None = None,
    z_threshold: float = 2.0,
) -> dict[str, Any]:
    """
    Detect anomalous data points in a metric series using z-score.

    For metrics with alert_threshold, also check hard-limit breaches.

    Args:
        series: List of {day, date, value, phase} dicts
        metric_name: Label for reporting
        alert_threshold: Optional hard threshold to check against
        z_threshold: Z-score cutoff (default 2.0)

    Returns:
        Dict with anomaly flags, breached points, and severity
    """
    all_values = [p["value"] for p in series if p["value"] is not None]
    post_series = [p for p in series if p["phase"] == "post"]

    if len(all_values) < 3:
        return {"metric_name": metric_name, "anomalies": [], "severity": "unknown"}

    mean = statistics.mean(all_values)
    stdev = statistics.stdev(all_values) if len(all_values) > 1 else 0

    anomalies = []
    threshold_breaches = []

    for point in post_series:
        val = point["value"]
        z = abs((val - mean) / stdev) if stdev > 0 else 0

        if z >= z_threshold:
            anomalies.append({
                "day": point["day"],
                "date": point["date"],
                "value": val,
                "z_score": round(z, 2),
                "type": "z_score_outlier",
            })

        if alert_threshold is not None:
            # For metrics where higher = worse (crash rate, latency, tickets)
            # We flag breach if value > alert_threshold
            # For metrics where lower = worse (payment success, retention, dau)
            # We flag breach if value < alert_threshold
            # Heuristic: if post mean > pre mean, metric is "increasing metric"
            pre_values = [p["value"] for p in series if p["phase"] == "pre"]
            pre_mean = statistics.mean(pre_values) if pre_values else mean
            is_bad_high = pre_mean <= alert_threshold  # e.g. crash rate baseline < threshold

            if is_bad_high and val > alert_threshold:
                threshold_breaches.append({
                    "day": point["day"],
                    "date": point["date"],
                    "value": val,
                    "threshold": alert_threshold,
                    "type": "threshold_exceeded",
                })
            elif not is_bad_high and val < alert_threshold:
                threshold_breaches.append({
                    "day": point["day"],
                    "date": point["date"],
                    "value": val,
                    "threshold": alert_threshold,
                    "type": "threshold_breached_low",
                })

    total_anomalies = len(anomalies) + len(threshold_breaches)
    if total_anomalies == 0:
        severity = "none"
    elif total_anomalies <= 2:
        severity = "low"
    elif total_anomalies <= 4:
        severity = "medium"
    else:
        severity = "critical"

    return {
        "metric_name": metric_name,
        "anomalies": anomalies,
        "threshold_breaches": threshold_breaches,
        "total_anomaly_count": total_anomalies,
        "severity": severity,
        "mean_used": round(mean, 3),
        "stdev_used": round(stdev, 3),
    }


def run_anomaly_detection(metrics_data: dict, z_threshold: float = 2.0) -> dict[str, Any]:
    """
    Run anomaly detection across all metrics.

    Args:
        metrics_data: Full metrics JSON
        z_threshold: Z-score threshold

    Returns:
        Dict mapping metric_key -> anomaly result
    """
    results = {}
    for key, metric in metrics_data["metrics"].items():
        result = detect_anomalies(
            series=metric["data"],
            metric_name=metric["label"],
            alert_threshold=metric.get("alert_threshold"),
            z_threshold=z_threshold,
        )
        results[key] = result
    return results
