"""
Base Agent - defines the abstract interface all war room agents implement.
"""

import abc
import logging
import datetime
from typing import Any


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger


class BaseAgent(abc.ABC):
    """
    Abstract base for all war room agents.

    Every agent must implement `analyze()`, which receives the full
    shared context dict and returns a structured report dict.
    """

    name: str = "BaseAgent"
    role: str = "Generic"

    def __init__(self):
        self.logger = get_logger(self.name)
        self.tool_calls: list[dict] = []

    def _log_tool_call(self, tool_name: str, inputs: dict, output_summary: str) -> None:
        """Record a tool invocation for traceability."""
        record = {
            "agent": self.name,
            "tool": tool_name,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "inputs_summary": inputs,
            "output_summary": output_summary,
        }
        self.tool_calls.append(record)
        self.logger.info(f"  >> TOOL CALL: {tool_name} - {output_summary}")

    @abc.abstractmethod
    def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Run this agent's analysis.

        Args:
            context: Shared data bundle (metrics, feedback, release notes, etc.)

        Returns:
            Structured report dict with at minimum:
              - agent_name
              - role
              - findings
              - recommendations
              - risk_score (0.0 – 5.0)
              - tool_calls
        """
        raise NotImplementedError

    def report_header(self) -> str:
        return f"\n{'='*60}\n  AGENT: {self.name} ({self.role})\n{'='*60}"
