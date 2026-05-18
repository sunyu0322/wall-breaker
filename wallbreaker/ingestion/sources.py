from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from wallbreaker.models import RawItem


class SourceAdapter(Protocol):
    name: str

    def collect(self, query: str, limit: int) -> list[RawItem]:
        ...


@dataclass(slots=True)
class MockSource:
    name: str
    angle: str

    def collect(self, query: str, limit: int) -> list[RawItem]:
        examples = [
            f"关于{query}，有人说这只是个别现象，但评论区一直在追问：为什么每次代价都落到普通人身上？！！",
            f"{query}的争议点不在表面冲突，而在规则制定者把成本外包给沉默的人，然后要求他们保持体面。",
            f"一位亲历者写道：我不想被总结成宏大叙事里的一个数字，我只是觉得那一刻特别无力。",
        ]
        return [
            RawItem(
                source=self.name,
                query=query,
                title=f"{self.name} mock sample {index + 1}",
                raw_text=f"[{self.angle}] {text}",
                url=f"https://example.invalid/{self.name}/{index + 1}",
                metadata={"mock": True, "rank": index + 1},
            )
            for index, text in enumerate(examples[:limit])
        ]


def default_sources() -> list[SourceAdapter]:
    return [
        MockSource("baidu_bing", "全景事实骨架"),
        MockSource("zhihu", "逻辑深挖"),
        MockSource("weibo", "广场情绪"),
        MockSource("bilibili", "解构与弹幕"),
        MockSource("xiaohongshu", "微观体感"),
    ]


def collect_raw_items(query: str, per_source_limit: int = 3) -> list[RawItem]:
    items: list[RawItem] = []
    for source in default_sources():
        items.extend(source.collect(query, per_source_limit))
    return items

