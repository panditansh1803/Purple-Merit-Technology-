"""
Marketing / Comms Agent
Runs sentiment analysis, assesses customer perception, identifies channels
with the most negative signal, and recommends communication actions.
"""

from typing import Any
from agents.base_agent import BaseAgent
from tools.sentiment_analyzer import analyze_sentiment


class MarketingAgent(BaseAgent):
    name = "Marketing-Agent"
    role = "Marketing & Communications"

    def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        self.logger.info(self.report_header())
        self.logger.info("Analyzing user feedback sentiment and comms posture...")

        feedback = context["user_feedback"]

        # -- Tool: Sentiment Analysis -------------------------------
        self.logger.info("  Invoking tool: sentiment_analyzer")
        sentiment = analyze_sentiment(feedback)
        self._log_tool_call(
            "sentiment_analyzer",
            {"total_entries": len(feedback)},
            (
                f"Positive: {sentiment['positive_pct']}%, "
                f"Neutral: {sentiment['neutral_pct']}%, "
                f"Negative: {sentiment['negative_pct']}%"
            ),
        )

        # -- Channel Analysis ---------------------------------------
        high_risk_channels = []
        channel_breakdown = sentiment.get("channel_breakdown", {})
        for channel, counts in channel_breakdown.items():
            total_ch = sum(counts.values())
            neg_pct = (counts.get("negative", 0) / total_ch * 100) if total_ch else 0
            if neg_pct >= 50:
                high_risk_channels.append({"channel": channel, "negative_pct": round(neg_pct, 1)})
                self.logger.info(f"  [WARN] High-negativity channel: {channel} ({neg_pct:.1f}% negative)")

        # -- Key Perceptual Risks -----------------------------------
        pain_points = sentiment.get("pain_points", {})
        top_pain = sorted(pain_points.items(), key=lambda x: x[1], reverse=True)[:5]

        perceptual_risks = []
        if sentiment["negative_pct"] > 50:
            perceptual_risks.append("Majority of user feedback is negative - brand trust at risk")
        if "double charge" in pain_points and pain_points["double charge"] >= 3:
            perceptual_risks.append("Multiple reports of double charges - legal/chargeback liability risk")
        if "payment failure" in pain_points and pain_points["payment failure"] >= 5:
            perceptual_risks.append("High-volume payment failure complaints - churn acceleration likely")
        if sentiment["nps_proxy"] < -20:
            perceptual_risks.append(f"NPS proxy at {sentiment['nps_proxy']} - actively damaging word-of-mouth")

        # -- Communication Recommendations --------------------------
        if sentiment["negative_pct"] > 55:
            internal_msg = (
                "ESCALATE: Negative feedback has crossed 55%. Leadership must be briefed. "
                "Prepare a war room incident report within 2 hours."
            )
            external_msg = (
                "Issue a proactive user-facing status update acknowledging payment delays. "
                "Offer compensation (fee waiver / cashback) to affected users. "
                "Avoid technical jargon - keep messaging empathetic and action-oriented."
            )
        elif sentiment["negative_pct"] > 35:
            internal_msg = "Elevated negativity signal. Monitor closely and prepare escalation draft."
            external_msg = "Post in-app banner: 'We are aware of payment issues and our team is working on a fix.'"
        else:
            internal_msg = "Sentiment within acceptable range. Continue standard monitoring."
            external_msg = "No external communication required at this time."

        risk_score = min(5.0, (sentiment["negative_pct"] / 100) * 5 + len(perceptual_risks) * 0.5)

        findings = [
            f"Overall sentiment: {sentiment['negative_pct']}% negative, {sentiment['positive_pct']}% positive",
            f"NPS proxy: {sentiment['nps_proxy']}",
            f"Top pain point: {top_pain[0][0] if top_pain else 'N/A'} ({top_pain[0][1] if top_pain else 0} mentions)",
            f"High-risk channels: {[c['channel'] for c in high_risk_channels]}",
        ]

        for f in findings:
            self.logger.info(f"  {f}")

        self.logger.info(f"  Risk Score: {risk_score}/5.0")

        return {
            "agent_name": self.name,
            "role": self.role,
            "findings": findings,
            "sentiment_summary": {
                "positive_pct": sentiment["positive_pct"],
                "neutral_pct": sentiment["neutral_pct"],
                "negative_pct": sentiment["negative_pct"],
                "nps_proxy": sentiment["nps_proxy"],
                "total_entries": sentiment["total_entries"],
            },
            "pain_points": dict(top_pain),
            "top_negative_samples": sentiment.get("top_negative_samples", []),
            "high_risk_channels": high_risk_channels,
            "perceptual_risks": perceptual_risks,
            "communication_plan": {
                "internal": internal_msg,
                "external": external_msg,
                "suggested_tone": "Empathetic, transparent, action-oriented",
                "channels_to_address": [c["channel"] for c in high_risk_channels],
            },
            "risk_score": risk_score,
            "tool_calls": self.tool_calls,
        }
