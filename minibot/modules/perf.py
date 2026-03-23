import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


def _enabled() -> bool:
    return os.getenv("PERF_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}


def _include_in_response() -> bool:
    return os.getenv("PERF_INCLUDE_IN_RESPONSE", "0").strip().lower() in {"1", "true", "yes", "on"}


def _base_dir() -> str:
    return os.getenv("PERF_LOG_DIR", "minibot_logs/perf")


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class Span:
    name: str
    ms: float
    meta: Dict[str, Any]


class PerfTracer:
    def __init__(self, enabled: Optional[bool] = None):
        self.enabled = _enabled() if enabled is None else enabled
        self._start = time.perf_counter()
        self._spans: List[Span] = []
        self._counters: Dict[str, int] = {}

    def _since_start_ms(self) -> float:
        return (time.perf_counter() - self._start) * 1000.0

    def mark(self, name: str, ms: float, meta: Optional[Dict[str, Any]] = None) -> None:
        if not self.enabled:
            return
        self._spans.append(Span(name=name, ms=float(ms), meta=meta or {}))

    def incr(self, key: str, inc: int = 1) -> None:
        if not self.enabled:
            return
        self._counters[key] = int(self._counters.get(key, 0)) + int(inc)

    def total_ms(self) -> float:
        return self._since_start_ms()

    def spans(self) -> List[Span]:
        return list(self._spans)

    def counters(self) -> Dict[str, int]:
        return dict(self._counters)

    def summary(self, top_k: int = 6) -> Dict[str, Any]:
        if not self.enabled:
            return {"enabled": False}
        spans = sorted(self._spans, key=lambda s: s.ms, reverse=True)
        top = [
            {"name": s.name, "ms": round(s.ms, 2), "meta": s.meta}
            for s in spans[: max(0, int(top_k))]
        ]
        return {
            "enabled": True,
            "ts": _now_iso(),
            "total_ms": round(self.total_ms(), 2),
            "top_spans": top,
            "counts": self._counters,
        }

    def persist(self, event: Dict[str, Any]) -> Optional[str]:
        if not self.enabled:
            return None
        base = _base_dir()
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, f"{_today()}.jsonl")
        payload = dict(event)
        payload["perf"] = self.summary()
        payload["spans"] = [{"name": s.name, "ms": round(s.ms, 2), "meta": s.meta} for s in self._spans]
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return path


def perf_enabled() -> bool:
    return _enabled()


def perf_include_in_response() -> bool:
    return _include_in_response()

