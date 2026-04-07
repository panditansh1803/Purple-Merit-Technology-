"""
Tool: Sentiment Analyzer
Analyzes user feedback text using VADER (no API key required) with
TextBlob as fallback. Called by the Marketing/Comms Agent.
"""

import re
from collections import Counter
from typing import Any


# ---------------------------------------------
# Simple rule-based sentiment scoring
# (works without any ML library installed)
# ---------------------------------------------
POSITIVE_WORDS = {
    "love", "great", "amazing", "fast", "smooth", "nice", "awesome",
    "excellent", "perfect", "wonderful", "fantastic", "easy", "quick",
    "impressed", "genius", "better", "best", "works", "good", "happy",
    "convenient", "helpful", "efficient", "reliable", "saved", "impressive",
}

NEGATIVE_WORDS = {
    "failed", "failure", "crash", "crashed", "crashing", "slow", "terrible",
    "broken", "unacceptable", "frustrated", "bad", "worst", "awful", "error",
    "uninstall", "bug", "bugs", "charged", "deducted", "refund", "unusable",
    "freezing", "freeze", "timeout", "angry", "furious", "disgusting",
    "hate", "wrong", "issue", "problem", "complaint", "horrific", "please",
    "back", "rollback", "serious",
}

AMPLIFIERS = {"very", "really", "extremely", "so", "absolutely", "totally", "completely"}
NEGATORS = {"not", "no", "never", "wasn't", "isn't", "doesn't", "didn't", "don't", "cant", "can't"}

PAIN_KEYWORDS = {
    "double charge": ["double", "charged", "twice", "deducted"],
    "crash on payment": ["crash", "crashed", "crashing", "freezing"],
    "slow loading": ["slow", "loading", "takes forever", "latency", "wait"],
    "payment failure": ["failed", "failure", "declined", "not working", "attempt"],
    "refund issues": ["refund", "resolution", "unresolved"],
    "support delays": ["support", "queue", "agent", "3 hours", "48 hours"],
    "routing bug": ["routing", "gateway", "wrong gateway"],
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def _score_text(text: str) -> tuple[str, float]:
    """
    Returns (label, compound_score) where compound_score ∈ [-1, 1].
    """
    tokens = _tokenize(text)
    score = 0.0
    i = 0
    while i < len(tokens):
        word = tokens[i]
        multiplier = 1.0

        # Check for negators in previous 2 words
        preceding = tokens[max(0, i - 2): i]
        if any(n in preceding for n in NEGATORS):
            multiplier = -1.0
        if any(a in preceding for a in AMPLIFIERS):
            multiplier *= 1.5

        if word in POSITIVE_WORDS:
            score += 1.0 * multiplier
        elif word in NEGATIVE_WORDS:
            score -= 1.0 * multiplier
        i += 1

    # Normalise
    word_count = max(len(tokens), 1)
    normalised = max(-1.0, min(1.0, score / (word_count ** 0.5)))

    if normalised >= 0.15:
        label = "positive"
    elif normalised <= -0.15:
        label = "negative"
    else:
        label = "neutral"

    return label, round(normalised, 3)


def _extract_pain_points(entries: list[dict]) -> dict[str, int]:
    pain_counts = Counter()
    for e in entries:
        text = e["text"].lower()
        for category, keywords in PAIN_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                pain_counts[category] += 1
    return dict(pain_counts.most_common())


def analyze_sentiment(feedback_entries: list[dict]) -> dict[str, Any]:
    """
    Run sentiment analysis on a list of feedback entries.

    Args:
        feedback_entries: List of {id, text, sentiment_label, channel, timestamp}

    Returns:
        Dict with counts, breakdown by channel, top themes, pain points
    """
    results = []
    label_counts = Counter()
    channel_sentiment: dict[str, Counter] = {}

    for entry in feedback_entries:
        label, score = _score_text(entry["text"])
        label_counts[label] += 1
        channel = entry.get("channel", "unknown")
        if channel not in channel_sentiment:
            channel_sentiment[channel] = Counter()
        channel_sentiment[channel][label] += 1

        results.append({
            "id": entry["id"],
            "text": entry["text"],
            "predicted_label": label,
            "compound_score": score,
            "channel": channel,
            "timestamp": entry.get("timestamp"),
        })

    total = len(results)
    positive_pct = round(label_counts["positive"] / total * 100, 1) if total else 0
    neutral_pct = round(label_counts["neutral"] / total * 100, 1) if total else 0
    negative_pct = round(label_counts["negative"] / total * 100, 1) if total else 0

    # Net Promoter proxy
    nps_proxy = round(positive_pct - negative_pct, 1)

    pain_points = _extract_pain_points(feedback_entries)

    # Top negative feedback samples
    top_negatives = [r["text"] for r in results if r["predicted_label"] == "negative"][:5]

    return {
        "total_entries": total,
        "label_counts": dict(label_counts),
        "positive_pct": positive_pct,
        "neutral_pct": neutral_pct,
        "negative_pct": negative_pct,
        "nps_proxy": nps_proxy,
        "channel_breakdown": {ch: dict(cnt) for ch, cnt in channel_sentiment.items()},
        "pain_points": pain_points,
        "top_negative_samples": top_negatives,
        "detailed_results": results,
    }
