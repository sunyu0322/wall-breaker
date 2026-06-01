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


def generate_analysis(
    client: LlmClient,
    model: str,
    query: str,
    items: list[RawItem],
    evidence_mode: str = "basic",
) -> dict:
    if not items or all(item.is_placeholder for item in items):
        return {
            "status": "insufficient_evidence",
            "evidence_mode": evidence_mode,
            "event_file": {"timeline": [], "actors": [], "original_claims": [], "responses": [], "sentiment_points": []},
            "thesis": "",
            "antithesis": "",
            "synthesis": "",
            "evidence_map": [],
            "research_gaps": [
                "当前只有 mock、检索错误或占位材料，不能支撑真实事件写作。",
                "请至少提供一个可读网页链接、百科/媒体条目、原始截图 OCR、或开启可用的真实搜索。",
            ],
            "outline": [
                "可先用 --source-url 粘贴百科或报道链接生成简单版。",
                "可用 --real-search --search-provider baidu_html 自动补充更多材料。",
                "若要做深稿，再补充原文、回应和社交平台高互动讨论。",
            ],
        }

    user = json.dumps(
        {
            "query": query,
            "evidence_mode": evidence_mode,
            "evidence_mode_policy": {
                "basic": "只要有一到两个可读来源，如百科、媒体报道、官方页面或用户提供链接，就可以生成简单版；必须标注信源限制，不能强行要求内部材料、流量数据、审核日志等高门槛证据。",
                "standard": "需要较完整的事件本体、回应和至少一种舆论材料；缺口只列真正影响判断的材料。",
                "strict": "用于调查型深稿，要求多源交叉验证、原文/截图、回应、舆论转折和反方材料。",
            },
            "raw_items": [item.to_dict() for item in items],
        },
        ensure_ascii=False,
        indent=2,
    )
    content = client.chat(model=model, system=REASONER_SYSTEM_PROMPT, user=user, temperature=0.2)
    content = normalize_mock_ids(content, items)
    try:
        analysis = json.loads(content)
    except json.JSONDecodeError:
        analysis = {"status": "ready", "raw_analysis": content, "outline": [], "evidence_map": []}
    analysis.setdefault("evidence_mode", evidence_mode)
    return analysis


def generate_script(
    client: LlmClient,
    model: str,
    query: str,
    analysis: dict,
    items: list[RawItem],
    target_length: str = "10分钟左右，约2800-3400个中文汉字",
) -> str:
    if analysis.get("status") == "insufficient_evidence":
        gaps = "\n".join(f"- {gap}" for gap in analysis.get("research_gaps", []))
        outline = "\n".join(f"- {step}" for step in analysis.get("outline", []))
        return (
            f"# 研究缺口清单：{query}\n\n"
            "当前材料不足以生成正式解说稿。为了避免幻觉，系统已停止文案生成。\n\n"
            "## 缺失材料\n"
            f"{gaps}\n\n"
            "## 下一步\n"
            f"{outline}\n"
        )

    user = json.dumps(
        {
            "query": query,
            "analysis": analysis,
            "raw_items": [item.to_dict() for item in items],
            "target_length": target_length,
            "length_policy": "basic 模式也尽量写成完整口播稿，只降低断言强度，不缩成短评。不要用提纲、列表或摘要替代正文。",
        },
        ensure_ascii=False,
        indent=2,
    )
    content = client.chat(model=model, system=WRITER_SYSTEM_PROMPT, user=user, temperature=0.55)
    return normalize_mock_ids(content, items)
