from __future__ import annotations

import time
from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime


class Telemetry:
    """
    Observability layer for CRS Wiki Engine.

    Responsibilities:
    - Track pipeline performance
    - Monitor dataset growth
    - Detect anomalies in ingestion
    - Provide quality metrics for wiki generation
    """

    def __init__(self):
        self.start_time = time.time()

        self.metrics: Dict[str, Any] = {
            "cycles": 0,
            "total_bosses": 0,
            "total_items": 0,
            "total_loot": 0,
            "errors": 0,
        }

        self.timing: Dict[str, List[float]] = defaultdict(list)

    # -----------------------------
    # Cycle Tracking
    # -----------------------------

    def start_cycle(self) -> float:
        return time.time()

    def end_cycle(self, start: float) -> None:
        duration = time.time() - start
        self.metrics["cycles"] += 1
        self.timing["cycle_duration"].append(duration)

    # -----------------------------
    # Dataset Metrics
    # -----------------------------

    def update_dataset_stats(
        self,
        bosses: int = 0,
        items: int = 0,
        loot: int = 0
    ) -> None:
        self.metrics["total_bosses"] += bosses
        self.metrics["total_items"] += items
        self.metrics["total_loot"] += loot

    # -----------------------------
    # Error Tracking
    # -----------------------------

    def log_error(self) -> None:
        self.metrics["errors"] += 1

    # -----------------------------
    # Performance Analysis
    # -----------------------------

    def get_report(self) -> Dict[str, Any]:
        return {
            "runtime_seconds": time.time() - self.start_time,
            "cycles": self.metrics["cycles"],
            "dataset": {
                "bosses": self.metrics["total_bosses"],
                "items": self.metrics["total_items"],
                "loot": self.metrics["total_loot"],
            },
            "performance": {
                "avg_cycle_time": self._avg("cycle_duration"),
                "max_cycle_time": self._max("cycle_duration"),
            },
            "errors": self.metrics["errors"],
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

    # -----------------------------
    # Helpers
    # -----------------------------

    def _avg(self, key: str) -> float:
        values = self.timing.get(key, [])
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _max(self, key: str) -> float:
        values = self.timing.get(key, [])
        if not values:
            return 0.0
        return max(values)