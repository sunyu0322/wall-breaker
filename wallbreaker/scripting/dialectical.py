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
    if not items or all(item.is_placeholder for item in items):
        return {
            "status": "insufficient_evidence",
            "event_file": {
                "timeline": [],
                "actors": [],
                "original_claims": [],
                "responses": [],
                "sentiment_points": [],
            },
            "thesis": "",
            "antithesis": "",
            "synthesis": "",
            "evidence_map": [],
            "research_gaps": [
                "当前采集结果仍是 mock/占位素材，不能支撑真实事件研究。",
                "需要补充原始文案、品牌方回应、媒体报道、社交平台高互动评论或截图文本。",
            ],
            "outline": [
                "检索原始事件：品牌名 + 母亲节文案 + 道歉/回应",
                "检索舆论转折：微博/小红书/知乎/B站高互动讨论",
                "保存原文、链接、截图 OCR 或人工摘录后使用 --source-file 重新运行",
            ],
        }
    user = f"议题：{query}\n\n原样素材如下：\n{_items_payload(items)}"
    content = client.chat(model=model, system=REASONER_SYSTEM_PROMPT, user=user, temperature=0.2)
    content = normalize_mock_ids(content, items)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw_analysis": content, "outline": [], "evidence_map": []}


def generate_script(client: LlmClient, model: str, query: str, analysis: dict, items: list[RawItem]) -> str:
    if analysis.get("status") == "insufficient_evidence":
        gaps = "\n".join(f"- {gap}" for gap in analysis.get("research_gaps", []))
        outline = "\n".join(f"- {step}" for step in analysis.get("outline", []))
        return (
            f"# 研究缺口清单：{query}\n\n"
            "当前材料不足以生成正式解说稿。为了避免幻觉，系统已停止文案生成。\n\n"
            "## 缺失材料\n"
            f"{gaps}\n\n"
            "## 下一步检索\n"
            f"{outline}\n"
        )
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
