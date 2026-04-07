"""
Risk / Critic Agent
Challenges assumptions from other agents, identifies systemic risks,
highlights gaps in evidence, and populates the risk register.
"""

from typing import Any
from agents.base_agent import BaseAgent


class RiskAgent(BaseAgent):
    name = "Risk-Agent"
    role = "Risk & Critic"

    # Known risks from release notes - seeded into the register
    KNOWN_RISKS_FROM_RELEASE = [
        {
            "risk_id": "R-001",
            "risk": "Third-party SDK cold-start latency (payment-router-sdk v3.1.2)",
            "category": "Technical",
            "severity": "High",
            "probability": "High",
            "impact": "Increased API latency -> payment timeouts -> revenue loss",
            "evidence": "Latency p95 increased 308% post-launch (250ms -> 1020ms)",
            "mitigation": "Downgrade to v3.1.1 or implement SDK warm-up pre-call. Hotfix ETA: 4h.",
            "owner": "Platform Engineering",
        },
        {
            "risk_id": "R-002",
            "risk": "DB migration lock causing read contention on transactions table",
            "category": "Infrastructure",
            "severity": "Medium",
            "probability": "Medium",
            "impact": "Intermittent payment processing failures during peak hours",
            "evidence": "Known pre-launch risk - not confirmed as root cause yet",
            "mitigation": "Run EXPLAIN ANALYZE on routing queries. Optimize with index on routing_events.created_at.",
            "owner": "DBA / Infrastructure",
        },
        {
            "risk_id": "R-003",
            "risk": "ML routing model mis-classifying transactions leading to wrong gateway selection",
            "category": "AI/ML",
            "severity": "High",
            "probability": "High",
            "impact": "Payment failures for micro-transactions; cascading retry storms",
            "evidence": "User reports of 'routing to wrong gateway'; model confidence < 8% for <₹500 txns",
            "mitigation": "Disable ML routing for transactions < ₹500 immediately; use static fallback rules.",
            "owner": "ML Team",
        },
        {
            "risk_id": "R-004",
            "risk": "Double-charge incidents due to gateway health cache stale data",
            "category": "Financial",
            "severity": "Critical",
            "probability": "Confirmed",
            "impact": "User trust erosion, chargeback liability, possible regulatory attention",
            "evidence": "15+ support tickets reporting double deduction; cache TTL bug identified in release notes",
            "mitigation": "Emergency cache flush NOW. Deploy R-004-hotfix to invalidate stale gateway cache. Proactive refund batch for affected users.",
            "owner": "Payments Engineering + Finance",
        },
        {
            "risk_id": "R-005",
            "risk": "Support queue saturation",
            "category": "Operational",
            "severity": "High",
            "probability": "Confirmed",
            "impact": "Delayed resolution of payment failures -> churn acceleration",
            "evidence": "Support tickets: 84/day (pre) -> 445/day (post) - 430% increase",
            "mitigation": "Activate T2 support surge team. Deploy chatbot auto-response for known issues. Triage double-charge tickets as P0.",
            "owner": "Customer Success",
        },
        {
            "risk_id": "R-006",
            "risk": "Cascading user churn if rollback is delayed",
            "category": "Business",
            "severity": "Critical",
            "probability": "High",
            "impact": "D1 retention declined 21.7%; continued decline will compress revenue",
            "evidence": "DAU dropped 13.3% in 7 days post-launch; retention trend is monotonically decreasing",
            "mitigation": "Rollback or pause within next 2 hours. Offer retention incentive to recently churned users.",
            "owner": "Product + Growth",
        },
    ]

    def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        self.logger.info(self.report_header())
        self.logger.info("Challenging assumptions and building risk register...")

        pm_report = context.get("pm_report", {})
        analyst_report = context.get("analyst_report", {})
        marketing_report = context.get("marketing_report", {})

        # -- Assumption Challenges ----------------------------------
        challenges = []

        # Challenge PM assumptions
        if pm_report.get("pm_recommendation") in ("Proceed with Caution",):
            challenges.append(
                "CHALLENGE [PM]: 'Proceed with Caution' underweights the payment double-charge "
                "incidents - these are confirmed financial integrity failures, not caution-level concerns."
            )

        # Challenge data assumptions
        analyst_trends = analyst_report.get("trend_summary", {})
        critical_count = analyst_trends.get("critical_metrics", 0)
        if critical_count >= 3:
            challenges.append(
                f"CHALLENGE [Data]: {critical_count} CRITICAL metrics simultaneously - "
                "this is not a coincidence. Root cause is likely systemic (SDK or ML model), "
                "not individual metric noise."
            )

        # Challenge marketing communications
        marketing_ext = marketing_report.get("communication_plan", {}).get("external", "")
        if "status update" in marketing_ext.lower() and "double charge" in str(
            marketing_report.get("pain_points", {})
        ):
            challenges.append(
                "CHALLENGE [Marketing]: A generic status update is insufficient when double-charge "
                "incidents are confirmed. Proactive individual outreach to affected users is required."
            )

        # Evidence gaps
        evidence_gaps = [
            "Root cause of crash_rate spike not yet identified - is it SDK, ML model, or DB?",
            "No A/B test data available to isolate new routing logic impact vs. baseline",
            "Double-charge affected user count unknown - quantify before proceeding",
            "iOS Safari affected user % unknown - may be larger than assumed",
        ]

        for c in challenges:
            self.logger.info(f"  !! {c}")

        for g in evidence_gaps:
            self.logger.info(f"  ? Evidence gap: {g}")

        # -- Risk Register Augmentation -----------------------------
        # Add data-driven risks from analyst report
        risk_register = list(self.KNOWN_RISKS_FROM_RELEASE)

        # Check if payment success is in confirmed critical territory
        metric_refs = analyst_report.get("metric_references", {})
        if metric_refs.get("payment_success_rate", {}).get("latest", 100) < 90:
            risk_register.append({
                "risk_id": "R-007",
                "risk": "Payment success rate below 90% - approaching regulatory reporting threshold",
                "category": "Compliance",
                "severity": "Critical",
                "probability": "Confirmed",
                "impact": "Possible RBI / payment network compliance violations if sustained",
                "evidence": f"Latest payment success rate: {metric_refs['payment_success_rate']['latest']}%",
                "mitigation": "Immediate rollback. Brief legal/compliance team. Prepare incident report.",
                "owner": "Legal + Payments",
            })

        critical_risks = [r for r in risk_register if r["severity"] == "Critical"]
        high_risks = [r for r in risk_register if r["severity"] == "High"]

        risk_score = min(5.0, len(critical_risks) * 1.5 + len(high_risks) * 0.75)

        self._log_tool_call(
            "risk_register_builder",
            {"sources": ["release_notes", "pm_report", "analyst_report", "marketing_report"]},
            f"Built risk register: {len(risk_register)} risks ({len(critical_risks)} Critical, {len(high_risks)} High)",
        )

        self.logger.info(f"  Risk Register: {len(risk_register)} entries")
        self.logger.info(f"  Risk Score: {risk_score}/5.0")

        return {
            "agent_name": self.name,
            "role": self.role,
            "findings": challenges + [f"Evidence gap: {g}" for g in evidence_gaps],
            "assumption_challenges": challenges,
            "evidence_gaps": evidence_gaps,
            "risk_register": risk_register,
            "critical_risk_count": len(critical_risks),
            "high_risk_count": len(high_risks),
            "critic_recommendation": (
                "Roll Back immediately. The confluence of a payment success rate collapse, "
                "confirmed double-charge incidents, crash rate above rollback threshold, and "
                "a 430% support ticket surge indicates a systemic failure - not transient noise."
            ),
            "risk_score": risk_score,
            "tool_calls": self.tool_calls,
        }
