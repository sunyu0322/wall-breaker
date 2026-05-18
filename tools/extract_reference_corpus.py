from __future__ import annotations

import re
import sys
import zipfile
from html import unescape
from pathlib import Path
from xml.etree import ElementTree


def extract_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        parts = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def normalize_subtitles(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = re.sub(r"^\[(\d\d:\d\d)\s*-\s*(\d\d:\d\d)\]\s*", r"[\1-\2] ", text, flags=re.MULTILINE)
    return text.strip()


def write_text(path: Path, title: str, source: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = f"# {title}\n\n来源：{source}\n\n{unescape(content).strip()}\n"
    path.write_text(body, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(
            "Usage: python tools/extract_reference_corpus.py <debate.docx> <early-love.txt> <output-dir>"
        )
    debate_path = Path(sys.argv[1])
    early_love_path = Path(sys.argv[2])
    output_dir = Path(sys.argv[3])

    debate_text = extract_docx_text(debate_path)
    early_love_text = normalize_subtitles(early_love_path.read_text(encoding="utf-8-sig"))

    write_text(output_dir / "should-call-women-xiansheng.md", "风格参考：先生称谓议题", debate_path, debate_text)
    write_text(output_dir / "early-love-subtitle.md", "风格参考：早恋概念考古", early_love_path, early_love_text)


if __name__ == "__main__":
    main()
