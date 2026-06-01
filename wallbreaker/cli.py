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
    run.add_argument("--per-source-limit", type=int, default=3, help="每个平台/来源采集条数")
    run.add_argument("--source-file", help="本地真实材料文件。用单独一行 --- 分隔多条素材。")
    run.add_argument("--source-text", help="直接粘贴的一段背景材料。可用 --- 分隔多条素材。")
    run.add_argument("--source-clipboard", action="store_true", help="从系统剪贴板读取背景材料。")
    run.add_argument("--source-url", action="append", default=[], help="手动提供的网页链接，可传多次。系统会尝试抓取正文。")
    run.add_argument("--real-search", action="store_true", help="启用真实搜索 API/搜索页检索。")
    run.add_argument("--search-provider", default=None, help="搜索提供方：auto、bing、serper、brave、tavily、baidu_html、bing_html、duckduckgo。")
    run.add_argument("--fetch-pages", action="store_true", help="尝试抓取搜索结果页面正文。")
    run.add_argument(
        "--evidence-mode",
        choices=["basic", "standard", "strict"],
        default="basic",
        help="证据门槛：basic 可基于少量可信材料写简单稿；standard 需要较完整事件档案；strict 要求强证据链。",
    )
    run.add_argument("--target-length", default="10分钟左右，约2800-3400个中文汉字", help="目标文案长度描述。")
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
            source_text=args.source_text,
            source_clipboard=args.source_clipboard,
            source_urls=args.source_url,
            real_search=args.real_search,
            search_provider=args.search_provider,
            fetch_pages=args.fetch_pages,
            evidence_mode=args.evidence_mode,
            target_length=args.target_length,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
