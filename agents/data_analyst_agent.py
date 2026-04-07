"""
Data Analyst Agent
Runs metric_aggregator, anomaly_detector, and trend_comparator tools
to produce a quantitative analysis of the launch health.
"""

from typing import Any
from agents.base_agent import BaseAgent
from tools.metric_aggregator import aggregate_all_metrics
from tools.anomaly_detector import run_anomaly_detection
from tools.trend_comparator import compare_all_trends
from config import ANOMALY_Z_THRESHOLD


class DataAnalystAgent(BaseAgent):
    name = "DataAnalyst-Agent"
    role = "Data Analyst"

    def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        self.logger.info(self.report_header())
        self.logger.info("Running quantitative metric analysis...")

        metrics_raw = context["metrics_raw"]

        # -- Tool 1: Metric Aggregation ----------------------------
        self.logger.info("  Invoking tool: metric_aggregator")
        aggregations = aggregate_all_metrics(metrics_raw)
        self._log_tool_call(
            "metric_aggregator",
            {"metrics": list(aggregations.keys())},
            f"Aggregated {len(aggregations)} metrics (pre/post means, trends)",
        )

        # -- Tool 2: Anomaly Detection ------------------------------
        self.logger.info("  Invoking tool: anomaly_detector")
        anomalies = run_anomaly_detection(metrics_raw, z_threshold=ANOMALY_Z_THRESHOLD)
        critical_anomalies = [k for k, v in anomalies.items() if v.get("severity") == "critical"]
        self._log_tool_call(
            "anomaly_detector",
            {"z_threshold": ANOMALY_Z_THRESHOLD},
            f"Found {len(critical_anomalies)} critical anomaly metrics: {critical_anomalies}",
        )

        # -- Tool 3: Trend Comparison -------------------------------
        self.logger.info("  Invoking tool: trend_comparator")
        trends = compare_all_trends(metrics_raw)
        trend_summary = trends["summary"]
        self._log_tool_call(
            "trend_comparator",
            {"window": "pre-7 vs post-7 days"},
            f"CRITICAL: {trend_summary['critical_metrics']}, WARNING: {trend_summary['warning_metrics']}, OK: {trend_summary['ok_metrics']}",
        )

        # -- Synthesize Key Findings --------------------------------
        key_findings = []
        metric_references = {}

        for key, agg in aggregations.items():
            pct = agg.get("pct_change", 0) or 0
            label = agg["metric_name"]
            unit = agg.get("unit", "")
            trend_status = trends["comparisons"].get(key, {}).get("status", "WATCH")
            anomaly_sev = anomalies.get(key, {}).get("severity", "none")

            if trend_status in ("CRITICAL", "WARNING") or anomaly_sev in ("critical", "medium"):
                direction_word = "increased" if pct > 0 else "decreased"
                finding = (
                    f"{label} {direction_word} by {abs(pct):.1f}% "
                    f"[Status: {trend_status}, Anomaly: {anomaly_sev}]"
                )
                key_findings.append(finding)
                self.logger.info(f"  [WARN] {finding}")

            metric_references[key] = {
                "label": label,
                "pre_mean": agg.get("pre_launch", {}).get("mean"),
                "post_mean": agg.get("post_launch", {}).get("mean"),
                "latest": agg.get("post_launch", {}).get("latest"),
                "pct_change": pct,
                "trend": agg.get("trend"),
                "trend_status": trend_status,
                "anomaly_severity": anomaly_sev,
                "unit": unit,
            }

        # Weighted risk score from trend + anomaly
        critical_count = trend_summary["critical_metrics"]
        warning_count = trend_summary["warning_metrics"]
        risk_score = min(5.0, critical_count * 1.5 + warning_count * 0.5)

        self.logger.info(f"  Risk Score: {risk_score}/5.0")
        self.logger.info(f"  Key Findings: {len(key_findings)} degraded metrics")

        return {
            "agent_name": self.name,
            "role": self.role,
            "findings": key_findings,
            "metric_references": metric_references,
            "aggregations": aggregations,
            "anomaly_report": anomalies,
            "trend_report": trends,
            "trend_summary": trend_summary,
            "confidence_note": (
                "High confidence on payment_success_rate and crash_rate (clear monotonic degradation). "
                "Lower confidence on feature_adoption (only 7 post-launch data points)."
            ),
            "risk_score": risk_score,
            "tool_calls": self.tool_calls,
        }
