# War Room — Multi-Agent Product Launch Decision System

> **AI/ML Assessment 1 — PurpleMerit Technologies**  
> Candidate: Simra | April 2026

A Python multi-agent system that simulates a cross-functional **war room** during a product feature launch. Four specialized AI agents analyze a 14-day mock metrics dashboard and 45 user feedback entries to produce a structured launch decision: **Proceed / Pause / Roll Back**.

---

## 📐 Architecture

```
┌─────────────────────────────────────────────┐
│           Orchestrator Agent                 │
│  Manages workflow, aggregates reports,       │
│  computes weighted risk score, decides       │
└──────┬──────────┬──────────┬────────────────┘
       │          │          │
  ┌────▼──┐ ┌────▼────┐ ┌───▼──────┐
  │  PM   │ │  Data   │ │Marketing │
  │ Agent │ │Analyst  │ │  Agent   │
  └────┬──┘ │ Agent   │ └───┬──────┘
       │    └────┬────┘     │
       │         │          │
       └────────►▼◄─────────┘
            ┌───────┐
            │ Risk  │
            │ Agent │
            └───────┘
```

### Agent Responsibilities

| Agent | Role | Tools Used |
|---|---|---|
| **PM Agent** | Defines success criteria, evaluates go/no-go thresholds | `success_criteria_evaluator` |
| **Data Analyst** | Quantitative analysis, anomaly detection, trend comparison | `metric_aggregator`, `anomaly_detector`, `trend_comparator` |
| **Marketing/Comms** | Sentiment analysis, channel breakdown, comms plan | `sentiment_analyzer` |
| **Risk/Critic** | Challenges assumptions, builds risk register | `risk_register_builder` |
| **Orchestrator** | Drives workflow, aggregates, decides | — |

---

## 📁 Project Structure

```
purple merit/
├── data/
│   ├── metrics.json          # 14-day time series, 9 metrics
│   ├── user_feedback.json    # 45 feedback entries
│   └── release_notes.md      # Feature description + known risks
├── agents/
│   ├── base_agent.py         # Abstract base with tracing/logging
│   ├── pm_agent.py
│   ├── data_analyst_agent.py
│   ├── marketing_agent.py
│   ├── risk_agent.py
│   └── orchestrator.py
├── tools/
│   ├── metric_aggregator.py  # Aggregation tool (stdlib only)
│   ├── anomaly_detector.py   # Z-score anomaly detection
│   ├── sentiment_analyzer.py # Rule-based sentiment + pain points
│   └── trend_comparator.py   # Pre/post launch trend comparison
├── output/
│   └── final_decision.json   # Generated output
├── main.py
├── config.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.10 or higher
- pip

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** The system runs fully in **rule-based mode** with no API key required.  
> All tools use Python's standard library (`statistics`, `re`, `collections`).

### 2. (Optional) Enable LLM synthesis via Gemini

```bash
# Windows PowerShell
$env:GOOGLE_API_KEY = "your-gemini-api-key-here"

# Linux / macOS
export GOOGLE_API_KEY="your-gemini-api-key-here"
```

---

## ▶️ How to Run

```bash
# Run with default output path (output/final_decision.json)
python main.py

# Run with custom output path
python main.py --output output/my_run.json
```

### Example Command (Windows PowerShell)

```powershell
cd "c:\Users\Simra\OneDrive\Desktop\purple merit"
python main.py
```

---

## 📤 Output

The system produces:

1. **Console logs** — full agent trace with tool calls and step-by-step reasoning
2. **`output/final_decision.json`** — structured JSON containing:

```json
{
  "decision": "Roll Back",
  "rationale": { "summary": "...", "key_drivers": [...], "metric_references": {...} },
  "risk_register": [ { "risk_id": "R-001", "severity": "Critical", ... } ],
  "action_plan": {
    "24h": [ { "action": "...", "owner": "...", "priority": "P0" } ],
    "48h": [ ... ]
  },
  "communication_plan": { "internal": "...", "external": "..." },
  "confidence_score": 0.92,
  "confidence_boosters": [...],
  "agent_reports": { "pm": {...}, "data_analyst": {...}, "marketing": {...}, "risk": {...} },
  "tool_call_trace": [ { "agent": "...", "tool": "...", "timestamp": "...", ... } ]
}
```

---

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | No | `""` | Gemini API key (enables LLM synthesis) |
| `LLM_MODEL` | No | `gemini-1.5-flash` | Gemini model to use |

---

## 🧪 Mock Data Summary

- **Feature:** Smart Payment Routing v2.0 (launched 2026-03-31)
- **Metrics:** 9 time-series metrics over 14 days (activation, DAU, D1/D7 retention, crash rate, API latency p95, payment success rate, support tickets, feature adoption)
- **Feedback:** 45 entries across app store, play store, Twitter, support email, in-app survey
- **Release Notes:** Known risks including SDK cold-start latency, DB migration, ML model confidence gaps

---

## 📋 Agent Workflow (Execution Order)

```
1. Orchestrator initializes shared context (metrics + feedback + release notes)
2. PM Agent → evaluates success criteria thresholds → returns go/no-go framing
3. Data Analyst Agent → runs 3 tools → anomaly + aggregation + trend comparison
4. Marketing Agent → sentiment analysis → comms plan
5. Risk Agent → reads all 3 reports → challenges assumptions → builds risk register
6. Orchestrator → weighted score (PM 25%, Data 35%, Mktg 15%, Risk 25%) → final decision
7. Final JSON written to output/final_decision.json
```

---

## 📼 Demo Video

[Screen recording demonstrating system run and final JSON output]

---

*Submission: AI/ML Engineer Assessment — PurpleMerit Technologies, April 2026*
