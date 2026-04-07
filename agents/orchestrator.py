"""
Orchestrator Agent
Drives the full war room workflow:
  PM -> Data Analyst -> Marketing/Comms -> Risk/Critic -> Final Decision

Aggregates all agent reports and produces the structured final JSON output.
"""

import datetime
import logging
from typing import Any

from agents.base_agent import get_logger
from agents.pm_agent import PMAgent
from agents.data_analyst_agent import DataAnalystAgent
from agents.marketing_agent import MarketingAgent
from agents.risk_agent import RiskAgent


# Weights for final score calculation
AGENT_WEIGHTS = {
    "pm": 0.25,
    "data_analyst": 0.35,
    "marketing": 0.15,
    "risk": 0.25,
}


class Orchestrator:
    """
    Coordinates the war room agent workflow and produces the final decision.

    Flow:
        1. PM Agent - defines criteria & first-pass go/no-go
        2. Data Analyst Agent - quantitative analysis
        3. Marketing Agent - sentiment & comms (reads analyst data)
        4. Risk Agent - reads all three reports, builds risk register
        5. Orchestrator - weighs scores -> Final Decision JSON
    """

    def __init__(self, metrics_raw: dict, user_feedback: list, release_notes: str):
        self.logger = get_logger("Orchestrator")
        self.metrics_raw = metrics_raw
        self.user_feedback = user_feedback
        self.release_notes = release_notes
        self.all_tool_calls: list[dict] = []

    def _separator(self, title: str) -> None:
        self.logger.info(f"\n" + "-" * 60)
        self.logger.info(f"  ORCHESTRATOR STEP: {title}")
        self.logger.info("-" * 60)

    def _determine_decision(self, weighted_score: float, agent_reports: dict) -> tuple[str, float]:
        """
        Map weighted risk score -> final decision + confidence.

        Returns:
            (decision_str, confidence_score 0.0–1.0)
        """
        # Hard overrides: if rollback triggers exist from PM, escalate
        pm_rollback = agent_reports["pm"].get("rollback_triggers", [])
        risk_critical = agent_reports["risk"].get("critical_risk_count", 0)

        if len(pm_rollback) >= 2 and risk_critical >= 2:
            decision = "Roll Back"
            confidence = min(0.97, 0.80 + weighted_score * 0.05)
        elif weighted_score >= 3.5 or len(pm_rollback) >= 2:
            decision = "Roll Back"
            confidence = min(0.92, 0.70 + weighted_score * 0.06)
        elif weighted_score >= 2.0:
            decision = "Pause"
            confidence = min(0.85, 0.60 + weighted_score * 0.10)
        else:
            decision = "Proceed"
            confidence = max(0.55, 0.90 - weighted_score * 0.10)

        return decision, round(confidence, 2)

    def _build_action_plan(self, decision: str, agent_reports: dict) -> dict:
        """Generate 24h and 48h action plans based on decision and risk register."""

        risk_register = agent_reports["risk"].get("risk_register", [])

        if decision == "Roll Back":
            plan_24h = [
                {"action": "Execute rollback: flip feature flag `payment_routing_v2` to false", "owner": "Platform Engineering", "priority": "P0 - Immediate"},
                {"action": "Redeploy payments-service:v1.8.5", "owner": "DevOps / SRE", "priority": "P0 - Immediate"},
                {"action": "Run DB rollback script: scripts/rollback_routing_events.sql", "owner": "DBA", "priority": "P0 - Immediate"},
                {"action": "Emergency cache flush for gateway health cache", "owner": "Payments Engineering", "priority": "P0 - Immediate"},
                {"action": "Identify all double-charge affected users; initiate batch refunds", "owner": "Finance + Payments Eng", "priority": "P0 - Within 2h"},
                {"action": "Publish internal incident report to leadership + on-call", "owner": "PM + Engineering Lead", "priority": "P1 - Within 2h"},
                {"action": "Post user-facing status update acknowledging payment issues", "owner": "Marketing / Comms", "priority": "P1 - Within 2h"},
                {"action": "Activate T2 support surge team; triage all P0 tickets", "owner": "Customer Success", "priority": "P1 - Immediate"},
                {"action": "Verify payment success rate recovers to >98% post-rollback", "owner": "SRE / Data Analyst", "priority": "P1 - Monitor"},
            ]
            plan_48h = [
                {"action": "Root cause analysis (RCA) document: identify crash_rate and latency root cause", "owner": "Engineering + Data", "priority": "P1"},
                {"action": "Fix payment-router-sdk cold-start latency (downgrade or warm-up strategy)", "owner": "Platform Engineering", "priority": "P1"},
                {"action": "Disable ML routing for transactions < ₹500; use static fallback rules", "owner": "ML Team", "priority": "P1"},
                {"action": "Fix gateway health cache stale data bug (cache invalidation hotfix)", "owner": "Payments Engineering", "priority": "P1"},
                {"action": "Review and harden DB migration locking strategy", "owner": "DBA", "priority": "P2"},
                {"action": "Design A/B test framework for Smart Routing v2.1 re-launch (5% canary)", "owner": "PM + Engineering", "priority": "P2"},
                {"action": "Send personalized apology + compensation offer to all affected users", "owner": "Customer Success + Marketing", "priority": "P2"},
                {"action": "iOS Safari payment modal CSS fix deployment", "owner": "Frontend", "priority": "P3"},
            ]
        elif decision == "Pause":
            plan_24h = [
                {"action": "Pause rollout: stop new user exposure to Smart Routing v2.0", "owner": "Platform Engineering", "priority": "P0 - Immediate"},
                {"action": "Investigate crash_rate spike root cause - collect crash dumps", "owner": "Engineering", "priority": "P0"},
                {"action": "Emergency cache flush: gateway health cache", "owner": "Payments Engineering", "priority": "P0"},
                {"action": "Identify double-charge affected users; initiate refunds", "owner": "Finance", "priority": "P0"},
                {"action": "Increase support staff allocation by 50%", "owner": "Customer Success", "priority": "P1"},
                {"action": "Post in-app banner acknowledging payment delays", "owner": "Marketing", "priority": "P1"},
            ]
            plan_48h = [
                {"action": "RCA on crash_rate and payment success degradation", "owner": "Engineering", "priority": "P1"},
                {"action": "Disable ML routing for <₹500 transactions", "owner": "ML Team", "priority": "P1"},
                {"action": "Prepare v2.0.1 hotfix with known bug fixes; re-run QA", "owner": "Engineering", "priority": "P1"},
                {"action": "Design canary release strategy (5%) for re-launch", "owner": "PM + Engineering", "priority": "P2"},
                {"action": "User sentiment recovery campaign for impacted cohort", "owner": "Marketing", "priority": "P2"},
            ]
        else:  # Proceed
            plan_24h = [
                {"action": "Increase monitoring frequency on crash_rate and payment_success_rate to every 5 min", "owner": "SRE", "priority": "P1"},
                {"action": "Investigate ML model performance for micro-transactions", "owner": "ML Team", "priority": "P1"},
                {"action": "Deploy cache invalidation hotfix for gateway health cache", "owner": "Payments Engineering", "priority": "P1"},
                {"action": "Brief support team on known issues and resolution paths", "owner": "Customer Success", "priority": "P1"},
            ]
            plan_48h = [
                {"action": "Review D1/D7 retention trend - escalate if continues declining", "owner": "PM + Data", "priority": "P2"},
                {"action": "Prepare rollback runbook drill with Engineering", "owner": "SRE", "priority": "P2"},
            ]

        return {"24h": plan_24h, "48h": plan_48h}

    def _build_confidence_boosters(self, decision: str, agent_reports: dict) -> list[str]:
        return [
            "Confirm root cause of crash_rate spike (crash dump analysis)",
            "A/B test data isolating new routing logic vs baseline",
            "Exact count of double-charge affected users from DB query",
            "Real-time payment success rate per gateway (Stripe vs Razorpay vs PayU breakdown)",
            "D1 retention for cohort exposed ONLY to new routing (not entire user base)",
            "ML model routing decision audit log for past 48 hours",
        ]

    def _collect_all_tool_calls(self, agent_reports: dict) -> list[dict]:
        calls = []
        for report in agent_reports.values():
            calls.extend(report.get("tool_calls", []))
        return calls

    def run(self) -> dict[str, Any]:
        """
        Execute the full war room workflow and return the final decision dict.
        """
        self.logger.info("\n" + "*" * 60)
        self.logger.info("  WAR ROOM INITIATED - PurpleMerit Smart Payment Routing v2.0")
        self.logger.info("*" * 60)

        # -- Shared context bundle ----------------------------------
        context: dict[str, Any] = {
            "metrics_raw": self.metrics_raw,
            "user_feedback": self.user_feedback,
            "release_notes": self.release_notes,
        }

        # -- Step 1: PM Agent ---------------------------------------
        self._separator("Step 1 / 4 - PM Agent")
        pm_agent = PMAgent()
        pm_report = pm_agent.analyze(context)
        context["pm_report"] = pm_report
        self.logger.info(f"  [OK] PM Agent complete. Recommendation: {pm_report['pm_recommendation']}")

        # -- Step 2: Data Analyst Agent -----------------------------
        self._separator("Step 2 / 4 - Data Analyst Agent")
        analyst_agent = DataAnalystAgent()
        analyst_report = analyst_agent.analyze(context)
        context["analyst_report"] = analyst_report
        self.logger.info(f"  [OK] Data Analyst complete. Risk Score: {analyst_report['risk_score']}/5.0")

        # -- Step 3: Marketing / Comms Agent -----------------------
        self._separator("Step 3 / 4 - Marketing / Comms Agent")
        marketing_agent = MarketingAgent()
        marketing_report = marketing_agent.analyze(context)
        context["marketing_report"] = marketing_report
        self.logger.info(f"  [OK] Marketing Agent complete. Risk Score: {marketing_report['risk_score']}/5.0")

        # -- Step 4: Risk / Critic Agent ----------------------------
        self._separator("Step 4 / 4 - Risk / Critic Agent")
        risk_agent = RiskAgent()
        risk_report = risk_agent.analyze(context)
        self.logger.info(f"  [OK] Risk Agent complete. Risk Score: {risk_report['risk_score']}/5.0")

        # -- Orchestrator: Final Synthesis --------------------------
        self._separator("ORCHESTRATOR - Final Decision Synthesis")

        agent_reports = {
            "pm": pm_report,
            "data_analyst": analyst_report,
            "marketing": marketing_report,
            "risk": risk_report,
        }

        weighted_score = sum(
            agent_reports[key]["risk_score"] * weight
            for key, weight in AGENT_WEIGHTS.items()
        )
        weighted_score = round(weighted_score, 3)
        self.logger.info(f"  Weighted Risk Score: {weighted_score:.3f}/5.0")

        decision, confidence = self._determine_decision(weighted_score, agent_reports)
        self.logger.info(f"  ⭐ FINAL DECISION: {decision.upper()} (confidence: {confidence:.0%})")

        action_plan = self._build_action_plan(decision, agent_reports)
        confidence_boosters = self._build_confidence_boosters(decision, agent_reports)
        all_tool_calls = self._collect_all_tool_calls(agent_reports)

        # -- Build rationale ----------------------------------------
        key_drivers = []
        metric_refs = analyst_report.get("metric_references", {})
        for key, ref in metric_refs.items():
            if ref.get("trend_status") in ("CRITICAL",):
                latest = ref.get("latest", "N/A")
                pct = ref.get("pct_change", 0)
                key_drivers.append(
                    f"{ref['label']}: {latest} {ref.get('unit','')} ({pct:+.1f}% vs pre-launch)"
                )

        rationale = {
            "summary": (
                f"Multiple critical metrics have breached rollback thresholds simultaneously "
                f"since the Smart Payment Routing v2.0 launch on 2026-03-31. "
                f"The crash rate is at {metric_refs.get('crash_rate', {}).get('latest', 'N/A')}% "
                f"(threshold: 2.0%), API latency p95 at "
                f"{metric_refs.get('api_latency_p95', {}).get('latest', 'N/A')}ms (threshold: 800ms), "
                f"and payment success rate at "
                f"{metric_refs.get('payment_success_rate', {}).get('latest', 'N/A')}% "
                f"(threshold: 92%). User sentiment is {marketing_report['sentiment_summary']['negative_pct']}% "
                f"negative with confirmed double-charge incidents."
            ),
            "key_drivers": key_drivers,
            "metric_references": {
                k: {
                    "label": v["label"],
                    "pre_mean": v["pre_mean"],
                    "post_latest": v["latest"],
                    "pct_change": v["pct_change"],
                    "status": v["trend_status"],
                    "unit": v.get("unit", ""),
                }
                for k, v in metric_refs.items()
            },
            "feedback_summary": (
                f"{marketing_report['sentiment_summary']['total_entries']} feedback entries analyzed. "
                f"{marketing_report['sentiment_summary']['negative_pct']}% negative. "
                f"Top pain points: {', '.join(list(marketing_report['pain_points'].keys())[:3])}. "
                f"NPS proxy: {marketing_report['sentiment_summary']['nps_proxy']}."
            ),
            "pm_framing": pm_report.get("pm_rationale"),
            "critic_note": risk_report.get("critic_recommendation"),
        }

        # -- Compose Final Output -----------------------------------
        final_output = {
            "decision": decision,
            "rationale": rationale,
            "risk_register": risk_report.get("risk_register", []),
            "action_plan": action_plan,
            "communication_plan": marketing_report.get("communication_plan", {}),
            "confidence_score": confidence,
            "confidence_boosters": confidence_boosters,
            "weighted_risk_score": weighted_score,
            "agent_reports": {
                "pm": {
                    "recommendation": pm_report.get("pm_recommendation"),
                    "rollback_triggers": pm_report.get("rollback_triggers"),
                    "warning_triggers": pm_report.get("warning_triggers"),
                    "risk_score": pm_report.get("risk_score"),
                    "user_impact": pm_report.get("user_impact_statement"),
                },
                "data_analyst": {
                    "trend_summary": analyst_report.get("trend_summary"),
                    "key_findings": analyst_report.get("findings"),
                    "confidence_note": analyst_report.get("confidence_note"),
                    "risk_score": analyst_report.get("risk_score"),
                },
                "marketing": {
                    "sentiment": marketing_report.get("sentiment_summary"),
                    "top_pain_points": marketing_report.get("pain_points"),
                    "perceptual_risks": marketing_report.get("perceptual_risks"),
                    "risk_score": marketing_report.get("risk_score"),
                },
                "risk": {
                    "critic_recommendation": risk_report.get("critic_recommendation"),
                    "assumption_challenges": risk_report.get("assumption_challenges"),
                    "evidence_gaps": risk_report.get("evidence_gaps"),
                    "critical_risk_count": risk_report.get("critical_risk_count"),
                    "risk_score": risk_report.get("risk_score"),
                },
            },
            "agent_weights_used": AGENT_WEIGHTS,
            "tool_call_trace": all_tool_calls,
            "metadata": {
                "feature": self.metrics_raw.get("feature", "Smart Payment Routing v2.0"),
                "launch_date": self.metrics_raw.get("launch_date"),
                "analysis_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "data_window_days": 14,
                "total_feedback_entries": len(self.user_feedback),
            },
        }

        self.logger.info("\n" + "*" * 60)
        self.logger.info(f"  WAR ROOM COMPLETE - Decision: {decision.upper()}")
        self.logger.info(f"  Confidence: {confidence:.0%} | Risk Score: {weighted_score:.2f}/5.0")
        self.logger.info("*" * 60 + "\n")

        return final_output
