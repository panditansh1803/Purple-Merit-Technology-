"""
Product Manager (PM) Agent
Defines success criteria, checks goal attainment against release note
thresholds, and frames the go/no-go from a product perspective.
"""

from typing import Any
from agents.base_agent import BaseAgent


class PMAgent(BaseAgent):
    name = "PM-Agent"
    role = "Product Manager"

    # Success criteria sourced from release_notes thresholds
    SUCCESS_CRITERIA = {
        "payment_success_rate": {"target": 98.5, "min_acceptable": 96.0, "rollback_if_below": 92.0, "direction": "higher_is_better"},
        "api_latency_p95":      {"target": 300,  "min_acceptable": 500,  "rollback_if_above": 800,  "direction": "lower_is_better"},
        "crash_rate":           {"target": 0.5,  "min_acceptable": 1.0,  "rollback_if_above": 2.0,  "direction": "lower_is_better"},
        "retention_d1":         {"target": 55.0, "min_acceptable": 50.0, "rollback_if_below": 45.0, "direction": "higher_is_better"},
        "support_tickets":      {"target": 100,  "min_acceptable": 180,  "rollback_if_above": 300,  "direction": "lower_is_better"},
    }

    def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        self.logger.info(self.report_header())
        self.logger.info("Evaluating success criteria and go/no-go framing...")

        metrics_raw = context["metrics_raw"]["metrics"]
        findings = []
        rollback_triggers = []
        warning_triggers = []
        scores = {}

        for metric_key, criteria in self.SUCCESS_CRITERIA.items():
            if metric_key not in metrics_raw:
                continue

            series = metrics_raw[metric_key]["data"]
            post_vals = [p["value"] for p in series if p["phase"] == "post"]
            if not post_vals:
                continue

            latest = post_vals[-1]
            label = metrics_raw[metric_key]["label"]
            direction = criteria["direction"]

            # Determine status
            if direction == "higher_is_better":
                if "rollback_if_below" in criteria and latest < criteria["rollback_if_below"]:
                    status = "ROLLBACK_TRIGGER"
                    rollback_triggers.append(f"{label} = {latest} (below rollback threshold {criteria['rollback_if_below']})")
                elif latest < criteria["min_acceptable"]:
                    status = "BELOW_MIN"
                    warning_triggers.append(f"{label} = {latest} (below min acceptable {criteria['min_acceptable']})")
                elif latest < criteria["target"]:
                    status = "BELOW_TARGET"
                else:
                    status = "ON_TARGET"
            else:  # lower_is_better
                if "rollback_if_above" in criteria and latest > criteria["rollback_if_above"]:
                    status = "ROLLBACK_TRIGGER"
                    rollback_triggers.append(f"{label} = {latest} (exceeds rollback threshold {criteria['rollback_if_above']})")
                elif latest > criteria["min_acceptable"]:
                    status = "BELOW_MIN"
                    warning_triggers.append(f"{label} = {latest} (exceeds min acceptable {criteria['min_acceptable']})")
                elif latest > criteria["target"]:
                    status = "BELOW_TARGET"
                else:
                    status = "ON_TARGET"

            scores[metric_key] = status
            finding = f"[{status}] {label}: latest={latest}, target={criteria['target']}"
            findings.append(finding)
            self.logger.info(f"  {finding}")

        # Determine PM go/no-go recommendation
        if len(rollback_triggers) >= 2:
            pm_recommendation = "Roll Back"
            pm_rationale = f"{len(rollback_triggers)} critical metrics have breached rollback thresholds."
        elif len(rollback_triggers) == 1:
            pm_recommendation = "Pause"
            pm_rationale = f"1 rollback trigger detected. Immediate investigation needed before proceeding."
        elif len(warning_triggers) >= 2:
            pm_recommendation = "Pause"
            pm_rationale = f"{len(warning_triggers)} metrics are below minimum acceptable levels."
        else:
            pm_recommendation = "Proceed with Caution"
            pm_rationale = "Metrics are within acceptable ranges with minor deviations."

        risk_score = min(5.0, len(rollback_triggers) * 2.0 + len(warning_triggers) * 0.75)

        self._log_tool_call(
            "success_criteria_evaluator",
            {"metrics_checked": list(self.SUCCESS_CRITERIA.keys())},
            f"{len(rollback_triggers)} rollback triggers, {len(warning_triggers)} warnings",
        )

        self.logger.info(f"  PM Recommendation: {pm_recommendation}")
        self.logger.info(f"  Risk Score: {risk_score}/5.0")

        return {
            "agent_name": self.name,
            "role": self.role,
            "findings": findings,
            "metric_status_scores": scores,
            "rollback_triggers": rollback_triggers,
            "warning_triggers": warning_triggers,
            "pm_recommendation": pm_recommendation,
            "pm_rationale": pm_rationale,
            "user_impact_statement": (
                "Payment failures and crash spikes are directly degrading the checkout "
                "experience for active users. Retention decline signals users are abandoning "
                "the platform post-launch. User trust is at risk."
            ),
            "risk_score": risk_score,
            "tool_calls": self.tool_calls,
        }
