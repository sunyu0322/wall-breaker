from __future__ import annotations

import re

from wallbreaker.models import RawItem, VisualCue

EVIDENCE_RE = re.compile(r"\[E:([a-f0-9]+)\]")


def build_visual_timeline(script: str, items: list[RawItem]) -> list[VisualCue]:
    item_by_id = {item.id: item for item in items}
    cues: list[VisualCue] = []
    current_section = "开场"
    for paragraph in script.splitlines():
        line = paragraph.strip()
        if not line:
            continue
        if line.startswith("#"):
            current_section = line.lstrip("#").strip()
            continue
        evidence_ids = [match for match in EVIDENCE_RE.findall(line) if match in item_by_id]
        if not evidence_ids:
            continue
        targets = [item_by_id[item_id].url for item_id in evidence_ids if item_by_id[item_id].url]
        strategy = "视觉反差：朗读抽象判断时，展示对应原帖/评论截图，保留粗粝现场感。"
        if any(item_by_id[item_id].source in {"weibo", "bilibili", "xiaohongshu"} for item_id in evidence_ids):
            strategy = "微观体感/广场情绪：优先展示一线评论、亲历文本或弹幕热评截图。"
        cues.append(
            VisualCue(
                section=current_section,
                narration_hint=line[:90],
                visual_strategy=strategy,
                evidence_item_ids=evidence_ids,
                screenshot_targets=targets,
            )
        )
    return cues

