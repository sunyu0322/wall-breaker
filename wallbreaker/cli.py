from __future__ import annotations

import argparse
import json
from pathlib import Path

from wallbreaker.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wallbreaker", description="Wall-Breaker content automation MVP")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="run MVP pipeline for a topic")
    run.add_argument("query", help="热点关键词、事件名或 URL")
    run.add_argument("--output", default="runs", help="输出目录")
    run.add_argument("--per-source-limit", type=int, default=3, help="每个 source 采集条数")
    run.add_argument("--source-file", help="本地真实材料文件。用 --- 分隔多条素材。")
    run.add_argument("--real-search", action="store_true", help="启用真实搜索 API/搜索页检索。")
    run.add_argument("--search-provider", default=None, help="搜索提供方：auto、bing、serper、duckduckgo。")
    run.add_argument("--fetch-pages", action="store_true", help="尝试抓取搜索结果页面正文。")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "run":
        report = run_pipeline(
            args.query,
            output_root=Path(args.output),
            per_source_limit=args.per_source_limit,
            source_file=Path(args.source_file) if args.source_file else None,
            real_search=args.real_search,
            search_provider=args.search_provider,
            fetch_pages=args.fetch_pages,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
