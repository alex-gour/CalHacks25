"""Lightweight telemetry aggregation for observability during demos."""

from __future__ import annotations

import time
from collections import Counter, deque
from dataclasses import dataclass
from typing import Deque, Dict, Iterable, Tuple


@dataclass(frozen=True)
class TelemetryEvent:
    timestamp_ms: int
    event_type: str
    payload: Dict[str, str]


class TelemetryClient:
    """Stores recent events in-memory and provides counts on demand."""

    def __init__(self, max_events: int = 200) -> None:
        self._events: Deque[TelemetryEvent] = deque(maxlen=max_events)

    def emit(self, event_type: str, **payload: str) -> None:
        event = TelemetryEvent(
            timestamp_ms=self._now_ms(),
            event_type=event_type,
            payload={k: str(v) for k, v in payload.items()},
        )
        self._events.append(event)

    def recent(self) -> Iterable[TelemetryEvent]:
        return list(self._events)[-20:]

    def summary(self) -> Dict[str, Dict[str, int]]:
        counts = Counter(event.event_type for event in self._events)
        by_object = Counter(
            (event.payload.get("object_class") or "unknown")
            for event in self._events
            if event.event_type == "detection"
        )
        return {
            "events": dict(counts),
            "detections_by_object": dict(by_object),
        }

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)
