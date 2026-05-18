from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from wallbreaker.config import Settings
from wallbreaker.ingestion import collect_from_source_file, collect_raw_items, collect_search_items
from wallbreaker.llm import MockLlmClient, SiliconFlowClient
from wallbreaker.scripting import generate_analysis, generate_script
from wallbreaker.storage import JsonlRawStore
from wallbreaker.visual import build_visual_timeline


def make_client(settings: Settings):
    if settings.should_mock_llm:
        return MockLlmClient()
    if not settings.siliconflow_api_key:
        raise RuntimeError("SILICONFLOW_API_KEY is required when WALLBREAKER_USE_MOCK_LLM=false")
    return SiliconFlowClient(settings.siliconflow_api_key, settings.siliconflow_base_url)


def run_pipeline(
    query: str,
    output_root: Path = Path("runs"),
    per_source_limit: int = 3,
    source_file: Path | None = None,
    real_search: bool = False,
    search_provider: str | None = None,
    fetch_pages: bool | None = None,
) -> dict:
    settings = Settings.from_env()
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    if source_file:
        items = collect_from_source_file(source_file, query)
        ingestion_mode = "source_file"
    elif real_search:
        items = collect_search_items(
            query,
            provider_name=search_provider or settings.search_provider,
            per_platform_limit=per_source_limit,
            fetch_pages=settings.search_fetch_pages if fetch_pages is None else fetch_pages,
        )
        ingestion_mode = "real_search"
        if not items or all(item.is_placeholder for item in items):
            items = collect_raw_items(query, per_source_limit=per_source_limit)
            ingestion_mode = "real_search_unusable_fallback_mock"
    else:
        items = collect_raw_items(query, per_source_limit=per_source_limit)
        ingestion_mode = "mock"
    raw_store = JsonlRawStore(run_dir / "raw_items.jsonl")
    raw_store.append_many(items)

    client = make_client(settings)
    analysis = generate_analysis(client, settings.reasoner_model, query, items)
    script = generate_script(client, settings.writer_model, query, analysis, items)
    timeline = build_visual_timeline(script, items)

    (run_dir / "analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "script.md").write_text(script, encoding="utf-8")
    (run_dir / "visual_timeline.json").write_text(
        json.dumps([cue.to_dict() for cue in timeline], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report = {
        "query": query,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "mock_llm": settings.should_mock_llm,
        "ingestion_mode": ingestion_mode,
        "analysis_status": analysis.get("status", "unknown"),
        "raw_items": len(items),
        "visual_cues": len(timeline),
        "files": {
            "raw_items": str(run_dir / "raw_items.jsonl"),
            "analysis": str(run_dir / "analysis.json"),
            "script": str(run_dir / "script.md"),
            "visual_timeline": str(run_dir / "visual_timeline.json"),
        },
    }
    (run_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
