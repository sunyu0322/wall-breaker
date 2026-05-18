from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from wallbreaker.models import RawItem


class JsonlRawStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append_many(self, items: Iterable[RawItem]) -> None:
        with self.path.open("a", encoding="utf-8") as file:
            for item in items:
                file.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")

    def read_all(self) -> list[RawItem]:
        if not self.path.exists():
            return []
        rows: list[RawItem] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(RawItem(**json.loads(line)))
        return rows

