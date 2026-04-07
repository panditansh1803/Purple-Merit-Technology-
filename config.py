"""
Configuration - loads API keys and settings from environment variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ----------------------------------------------
# LLM Configuration (optional - system works
# in pure rule-based mode without any API key)
# ----------------------------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")
USE_LLM = bool(GOOGLE_API_KEY)

# ----------------------------------------------
# Data Paths
# ----------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

METRICS_FILE = os.path.join(DATA_DIR, "metrics.json")
FEEDBACK_FILE = os.path.join(DATA_DIR, "user_feedback.json")
RELEASE_NOTES_FILE = os.path.join(DATA_DIR, "release_notes.md")

# ----------------------------------------------
# Decision Thresholds
# ----------------------------------------------
ROLLBACK_SCORE_THRESHOLD = 3.5   # weighted score above this -> Roll Back
PAUSE_SCORE_THRESHOLD = 2.0      # weighted score above this -> Pause
ANOMALY_Z_THRESHOLD = 2.0        # z-score threshold to flag anomaly
