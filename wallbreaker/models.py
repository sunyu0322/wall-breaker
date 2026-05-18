from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class RawItem:
    source: str
    query: str
    raw_text: str
    url: str | None = None
    title: str | None = None
    author: str | None = None
    captured_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvidenceAnchor:
    claim: str
    source_item_id: str
    source: str
    url: str | None
    quote: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VisualCue:
    section: str
    narration_hint: str
    visual_strategy: str
    evidence_item_ids: list[str]
    screenshot_targets: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

