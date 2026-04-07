"""
main.py - Entry point for the War Room Multi-Agent System

Usage:
    python main.py
    python main.py --output output/custom_name.json

Environment Variables (optional):
    GOOGLE_API_KEY   - Gemini API key (enables LLM synthesis if set)
    LLM_MODEL        - Gemini model name (default: gemini-1.5-flash)
"""

import argparse
import json
import os
import sys
import logging
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from config import METRICS_FILE, FEEDBACK_FILE, RELEASE_NOTES_FILE, OUTPUT_DIR
from agents.orchestrator import Orchestrator


def setup_root_logging():
    """Configure root logger format for clean console output."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def load_json(path: str) -> dict | list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def print_banner():
    banner = """
+----------------------------------------------------------+
|     WAR ROOM - Multi-Agent Product Launch Decision       |
|     PurpleMerit Technologies  |  AI/ML Assessment 1      |
+----------------------------------------------------------+
"""
    print(banner)


def print_decision_summary(output: dict) -> None:
    decision = output["decision"]
    confidence = output["confidence_score"]
    weighted = output["weighted_risk_score"]

    icons = {"Roll Back": "[ROLL BACK]", "Pause": "[PAUSE]", "Proceed": "[PROCEED]"}
    icon = icons.get(decision, "[?]")

    print("\n" + "=" * 60)
    print(f"  {icon}  FINAL DECISION: {decision.upper()}")
    print(f"  Confidence     : {confidence:.0%}")
    print(f"  Weighted Risk  : {weighted:.2f} / 5.0")
    print("=" * 60)
    print(f"\n  Summary: {output['rationale']['summary'][:300]}...")
    print(f"\n  Key Drivers:")
    for d in output["rationale"]["key_drivers"][:5]:
        print(f"    • {d}")

    print(f"\n  Risk Register ({len(output['risk_register'])} entries):")
    for r in output["risk_register"]:
        print(f"    [{r['severity']}] {r['risk_id']}: {r['risk'][:70]}")

    print(f"\n  Action Plan (24h, top 5):")
    for a in output["action_plan"]["24h"][:5]:
        print(f"    [{a['priority'].split('-')[0].strip()}] {a['action'][:70]}")
        print(f"           Owner: {a['owner']}")

    print(f"\n  Communication:")
    comms = output.get("communication_plan", {})
    print(f"    Internal: {comms.get('internal', '')[:120]}")
    print(f"    External: {comms.get('external', '')[:120]}")

    print(f"\n  Confidence Boosters:")
    for b in output["confidence_boosters"][:3]:
        print(f"    >> {b}")

    print("\n" + "=" * 60 + "\n")


def main():
    setup_root_logging()
    print_banner()

    parser = argparse.ArgumentParser(description="War Room Multi-Agent Decision System")
    parser.add_argument("--output", default=None, help="Path to save final JSON output")
    args = parser.parse_args()

    # -- Load data --------------------------------------------------
    print("[main] Loading data files...")
    try:
        metrics_raw = load_json(METRICS_FILE)
        user_feedback = load_json(FEEDBACK_FILE)
        release_notes = load_text(RELEASE_NOTES_FILE)
    except FileNotFoundError as e:
        print(f"[ERROR] Data file not found: {e}")
        sys.exit(1)

    print(f"[main] Metrics loaded: {len(metrics_raw['metrics'])} metrics, 14-day window")
    print(f"[main] Feedback loaded: {len(user_feedback)} entries")
    print(f"[main] Release notes loaded: {len(release_notes)} chars")

    # -- Run orchestrator -------------------------------------------
    orchestrator = Orchestrator(
        metrics_raw=metrics_raw,
        user_feedback=user_feedback,
        release_notes=release_notes,
    )
    final_output = orchestrator.run()

    # -- Print summary ----------------------------------------------
    print_decision_summary(final_output)

    # -- Save output ------------------------------------------------
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = args.output or os.path.join(OUTPUT_DIR, "final_decision.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print(f"[main] ✅ Full JSON output saved to: {output_path}")
    print(f"[main] Tool call trace: {len(final_output['tool_call_trace'])} tool invocations recorded\n")

    return final_output


if __name__ == "__main__":
    main()
