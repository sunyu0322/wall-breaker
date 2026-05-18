from __future__ import annotations

import json

from wallbreaker.llm.prompts import REASONER_SYSTEM_PROMPT, WRITER_SYSTEM_PROMPT
from wallbreaker.llm.siliconflow import LlmClient
from wallbreaker.models import RawItem


def _items_payload(items: list[RawItem]) -> str:
    return json.dumps([item.to_dict() for item in items], ensure_ascii=False, indent=2)


def normalize_mock_ids(text: str, items: list[RawItem]) -> str:
    if not items:
        return text
    return text.replace("AUTO_FIRST", items[0].id).replace("AUTO_LAST", items[-1].id)


def generate_analysis(client: LlmClient, model: str, query: str, items: list[RawItem]) -> dict:
    user = f"议题：{query}\n\n原样素材如下：\n{_items_payload(items)}"
    content = client.chat(model=model, system=REASONER_SYSTEM_PROMPT, user=user, temperature=0.2)
    content = normalize_mock_ids(content, items)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw_analysis": content, "outline": [], "evidence_map": []}


def generate_script(client: LlmClient, model: str, query: str, analysis: dict, items: list[RawItem]) -> str:
    user = json.dumps(
        {
            "query": query,
            "analysis": analysis,
            "raw_items": [item.to_dict() for item in items],
            "target_length": "MVP 默认 2500-3500 中文字，可按信息密度增减",
        },
        ensure_ascii=False,
        indent=2,
    )
    content = client.chat(model=model, system=WRITER_SYSTEM_PROMPT, user=user, temperature=0.55)
    return normalize_mock_ids(content, items)

