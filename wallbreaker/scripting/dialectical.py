from __future__ import annotations

import json
import re

from wallbreaker.llm.prompts import REASONER_SYSTEM_PROMPT, WRITER_SYSTEM_PROMPT
from wallbreaker.llm.siliconflow import LlmClient
from wallbreaker.models import RawItem


def _items_payload(items: list[RawItem]) -> str:
    return json.dumps([item.to_dict() for item in items], ensure_ascii=False, indent=2)


def normalize_mock_ids(text: str, items: list[RawItem]) -> str:
    if not items:
        return text
    return text.replace("AUTO_FIRST", items[0].id).replace("AUTO_LAST", items[-1].id)


def _quote_window(text: str, pattern: str, radius: int = 90) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    return re.sub(r"\s+", " ", text[start:end]).strip()


def extract_event_anchors(query: str, items: list[RawItem]) -> dict:
    """Deterministically surface hard facts so the LLM cannot drift past them."""
    anchor_specs = [
        ("original_wording", r"我妈有两个[“\"']?老公[”\"']?.{0,120}?婚纱"),
        ("oppo_brand", r"OPPO|欧珀|绿厂"),
        ("event_date", r"2026年5月8日|5月8日"),
        ("apology", r"道歉|致歉|下架.{0,30}物料|评论精选|控评"),
        ("wuhan_university", r"武汉大学|武大|文学院|立德树人"),
        ("advertising_association", r"中国广告协会|中广协|无底线炒作|低俗玩梗|扭曲亲情"),
        ("accountability", r"问责|职级直降|冻结调薪|绩效不高于C|段要辉|王怡|马新"),
        ("duan_yongping", r"段永平|错了就改"),
        ("context_collapse", r"饭圈|追星|偶像|老公|圈层|语境|玩梗"),
    ]
    found: dict[str, list[dict[str, str | None]]] = {}
    for item in items:
        text = item.raw_text or ""
        if not text:
            continue
        for name, pattern in anchor_specs:
            quote = _quote_window(text, pattern)
            if quote:
                found.setdefault(name, []).append(
                    {
                        "raw_item_id": item.id,
                        "source": item.source,
                        "title": item.title,
                        "url": item.url,
                        "quote": quote,
                    }
                )

    return {
        "query": query,
        "priority": [
            "先锁定原始争议句、发布时间、平台/品牌、回应、二次舆情，再做观点分析。",
            "如果检测到 original_wording，成稿开头必须复述或转述这条原文，不能改写成不存在的文案。",
            "事件事实优先级高于风格参考。风格参考只能提供讲法，不能替代当前事件事实。",
        ],
        "found": found,
        "hallucination_guards": [
            "不要把 2026 年事件写成 2023 年。",
            "不要发明“全年无休的超级英雄”“永远美丽”“用母爱卖手机”等材料里不存在的争议文案。",
            "不要先套性别议题、节日商业化、公关危机三段论，再倒填事实。",
            "OPPO 案的核心不是一般母亲节营销，而是饭圈称谓“老公”进入母亲节主流品牌广告后造成的语境坍塌，以及随后道歉、控评、武大下场、中广协表态和内部问责。",
        ],
    }


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
            "detected_event_anchors": extract_event_anchors(query, items),
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
            "detected_event_anchors": extract_event_anchors(query, items),
            "raw_items": [item.to_dict() for item in items],
            "target_length": target_length,
            "length_policy": "basic 模式也尽量写成完整口播稿，只降低断言强度，不缩成短评。不要用提纲、列表或摘要替代正文。",
        },
        ensure_ascii=False,
        indent=2,
    )
    content = client.chat(model=model, system=WRITER_SYSTEM_PROMPT, user=user, temperature=0.55)
    return normalize_mock_ids(content, items)
