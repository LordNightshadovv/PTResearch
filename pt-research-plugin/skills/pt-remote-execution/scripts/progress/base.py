"""Defensible progress and ETA helpers shared by remote solver adapters."""
from __future__ import annotations
from dataclasses import dataclass
from statistics import median
from typing import Optional, Sequence

@dataclass(frozen=True)
class Progress:
    mode: str
    completed_units: Optional[float]
    total_units: Optional[float]
    progress_percent: Optional[float]
    estimated_remaining_seconds: Optional[float]
    eta_confidence: Optional[str]

def estimate(mode: str, completed: Optional[float], total: Optional[float], samples: Sequence[tuple[float, float]], minimum_samples: int = 5) -> Progress:
    if completed is None or total is None or total <= 0:
        return Progress("indeterminate", completed, total, None, None, None)
    percent = max(0.0, min(100.0, 100.0 * completed / total))
    if len(samples) < minimum_samples:
        return Progress(mode, completed, total, percent, None, "low")
    rates = [(b[0] - a[0]) / (b[1] - a[1]) for a, b in zip(samples[-minimum_samples:], samples[-minimum_samples + 1:]) if b[1] > a[1] and b[0] > a[0]]
    if not rates:
        return Progress(mode, completed, total, percent, None, "low")
    rate = median(rates)
    if rate <= 0:
        return Progress(mode, completed, total, percent, None, "low")
    spread = max(rates) / min(rates) if min(rates) else float("inf")
    confidence = "high" if spread < 1.2 and len(rates) >= 8 else "medium" if spread < 2 else "low"
    return Progress(mode, completed, total, percent, max(0.0, (total - completed) / rate), confidence)
