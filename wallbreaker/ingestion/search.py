from __future__ import annotations

import html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from wallbreaker.models import RawItem


@dataclass(frozen=True)
class SearchHit:
    title: str
    url: str
    snippet: str
    provider: str
    rank: int


class SearchProvider(Protocol):
    name: str

    def search(self, query: str, limit: int) -> list[SearchHit]:
        ...


class BingSearchProvider:
    name = "bing"

    def __init__(self, api_key: str, endpoint: str = "https://api.bing.microsoft.com/v7.0/search") -> None:
        self.api_key = api_key
        self.endpoint = endpoint

    def search(self, query: str, limit: int) -> list[SearchHit]:
        params = urllib.parse.urlencode({"q": query, "count": min(limit, 10), "mkt": "zh-CN"})
        request = urllib.request.Request(
            f"{self.endpoint}?{params}",
            headers={"Ocp-Apim-Subscription-Key": self.api_key},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        rows = data.get("webPages", {}).get("value", [])
        return [
            SearchHit(row.get("name", ""), row.get("url", ""), row.get("snippet", ""), self.name, index + 1)
            for index, row in enumerate(rows[:limit])
            if row.get("url")
        ]


class BraveSearchProvider:
    name = "brave"

    def __init__(self, api_key: str, endpoint: str = "https://api.search.brave.com/res/v1/web/search") -> None:
        self.api_key = api_key
        self.endpoint = endpoint

    def search(self, query: str, limit: int) -> list[SearchHit]:
        params = urllib.parse.urlencode({"q": query, "count": min(limit, 10), "country": "cn", "search_lang": "zh-hans"})
        request = urllib.request.Request(
            f"{self.endpoint}?{params}",
            headers={"X-Subscription-Token": self.api_key, "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        rows = data.get("web", {}).get("results", [])
        return [
            SearchHit(row.get("title", ""), row.get("url", ""), row.get("description", ""), self.name, index + 1)
            for index, row in enumerate(rows[:limit])
            if row.get("url")
        ]


class SerperSearchProvider:
    name = "serper"

    def __init__(self, api_key: str, endpoint: str = "https://google.serper.dev/search") -> None:
        self.api_key = api_key
        self.endpoint = endpoint

    def search(self, query: str, limit: int) -> list[SearchHit]:
        payload = json.dumps({"q": query, "num": min(limit, 10), "hl": "zh-cn"}).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        rows = data.get("organic", [])
        return [
            SearchHit(row.get("title", ""), row.get("link", ""), row.get("snippet", ""), self.name, index + 1)
            for index, row in enumerate(rows[:limit])
            if row.get("link")
        ]


class TavilySearchProvider:
    name = "tavily"

    def __init__(self, api_key: str, endpoint: str = "https://api.tavily.com/search") -> None:
        self.api_key = api_key
        self.endpoint = endpoint

    def search(self, query: str, limit: int) -> list[SearchHit]:
        payload = json.dumps(
            {
                "query": query,
                "max_results": min(limit, 10),
                "search_depth": "basic",
                "include_raw_content": "text",
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
        rows = data.get("results", [])
        return [
            SearchHit(
                row.get("title", ""),
                row.get("url", ""),
                row.get("content") or row.get("raw_content") or "",
                self.name,
                index + 1,
            )
            for index, row in enumerate(rows[:limit])
            if row.get("url")
        ]


class BingHtmlProvider:
    name = "bing_html"

    def search(self, query: str, limit: int) -> list[SearchHit]:
        params = urllib.parse.urlencode({"q": query, "mkt": "zh-CN"})
        page = _request_text(f"https://www.bing.com/search?{params}", timeout=30)
        rows = re.findall(r'<li class="b_algo".*?<a href="(.*?)".*?>(.*?)</a>.*?<p>(.*?)</p>', page, flags=re.S)
        return [
            SearchHit(_strip_html(title), html.unescape(url), _strip_html(snippet), self.name, index + 1)
            for index, (url, title, snippet) in enumerate(rows[:limit])
            if url.startswith("http")
        ]


class BaiduHtmlProvider:
    name = "baidu_html"

    def search(self, query: str, limit: int) -> list[SearchHit]:
        params = urllib.parse.urlencode({"wd": query, "rn": min(limit, 10)})
        page = _request_text(f"https://www.baidu.com/s?{params}", timeout=30)
        blocks = re.findall(r'<div[^>]+class="[^"]*result[^"]*"[^>]*>(.*?)</div>\s*</div>', page, flags=re.S)
        hits: list[SearchHit] = []
        for block in blocks:
            link_match = re.search(r'<a[^>]+href="(http.*?)"[^>]*>(.*?)</a>', block, flags=re.S)
            if not link_match:
                continue
            snippet = _strip_html(block)
            hits.append(SearchHit(_strip_html(link_match.group(2)), html.unescape(link_match.group(1)), snippet, self.name, len(hits) + 1))
            if len(hits) >= limit:
                break
        return hits


class DuckDuckGoHtmlProvider:
    name = "duckduckgo_html"

    def search(self, query: str, limit: int) -> list[SearchHit]:
        params = urllib.parse.urlencode({"q": query, "kl": "cn-zh"})
        page = _request_text(f"https://duckduckgo.com/html/?{params}", timeout=30)
        rows = re.findall(
            r'<a rel="nofollow" class="result__a" href="(?P<url>.*?)".*?>(?P<title>.*?)</a>.*?'
            r'<a class="result__snippet".*?>(?P<snippet>.*?)</a>',
            page,
            flags=re.S,
        )
        hits: list[SearchHit] = []
        for index, row in enumerate(rows[:limit]):
            url = html.unescape(row[0])
            if "uddg=" in url:
                url = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("uddg", [url])[0]
            hits.append(SearchHit(_strip_html(row[1]), urllib.parse.unquote(url), _strip_html(row[2]), self.name, index + 1))
        return hits


def make_search_provider(provider: str = "auto") -> SearchProvider | None:
    provider = provider.lower()
    bing_key = os.getenv("BING_SEARCH_API_KEY") or os.getenv("AZURE_BING_SEARCH_KEY")
    serper_key = os.getenv("SERPER_API_KEY")
    brave_key = os.getenv("BRAVE_SEARCH_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    if provider in {"auto", "bing"} and bing_key:
        return BingSearchProvider(bing_key)
    if provider in {"auto", "brave"} and brave_key:
        return BraveSearchProvider(brave_key)
    if provider in {"auto", "tavily"} and tavily_key:
        return TavilySearchProvider(tavily_key)
    if provider in {"auto", "serper"} and serper_key:
        return SerperSearchProvider(serper_key)
    if provider == "baidu_html":
        return BaiduHtmlProvider()
    if provider == "bing_html":
        return BingHtmlProvider()
    if provider in {"auto", "duckduckgo"}:
        return DuckDuckGoHtmlProvider()
    return None


def build_platform_queries(query: str) -> list[tuple[str, str]]:
    return [
        ("fact_web", f"{query} 原文 回应 争议 时间线"),
        ("news", f"{query} 媒体报道 回应 道歉"),
        ("wechat", f"{query} site:mp.weixin.qq.com"),
        ("zhihu", f"{query} site:zhihu.com"),
        ("weibo", f"{query} site:weibo.com"),
        ("bilibili", f"{query} site:bilibili.com"),
        ("xiaohongshu", f"{query} site:xiaohongshu.com"),
    ]


def collect_search_items(
    query: str,
    provider_name: str = "auto",
    per_platform_limit: int = 3,
    fetch_pages: bool = False,
) -> list[RawItem]:
    provider = make_search_provider(provider_name)
    if provider is None:
        return []
    items: list[RawItem] = []
    for platform, search_query in build_platform_queries(query):
        try:
            hits = provider.search(search_query, per_platform_limit)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            items.append(
                RawItem(
                    source=f"search_error:{platform}",
                    query=query,
                    title=f"{platform} search failed",
                    raw_text=f"检索失败：{type(exc).__name__}: {exc}",
                    metadata={"provider": provider.name, "search_query": search_query, "error": True},
                )
            )
            continue
        for hit in hits:
            page_text = fetch_page_text(hit.url) if fetch_pages else ""
            raw_text = "\n".join(
                part
                for part in [
                    f"搜索查询：{search_query}",
                    f"标题：{hit.title}",
                    f"摘要：{hit.snippet}",
                    f"页面正文摘录：{page_text}" if page_text else "",
                ]
                if part
            )
            items.append(
                RawItem(
                    source=platform,
                    query=query,
                    title=hit.title,
                    raw_text=raw_text,
                    url=hit.url,
                    metadata={
                        "provider": hit.provider,
                        "rank": hit.rank,
                        "search_query": search_query,
                        "fetch_pages": fetch_pages,
                    },
                )
            )
    return items


def fetch_page_text(url: str, max_chars: int = 6000) -> str:
    try:
        raw, content_type = _request_bytes(url, timeout=20)
    except (urllib.error.URLError, TimeoutError, OSError):
        return ""
    if "text/html" not in content_type and "text/plain" not in content_type:
        return ""
    text = raw.decode(_guess_encoding(content_type), errors="replace")
    text = _strip_html(text)
    return text[:max_chars]


def _request_text(url: str, timeout: int) -> str:
    raw, content_type = _request_bytes(url, timeout)
    return raw.decode(_guess_encoding(content_type), errors="replace")


def _request_bytes(url: str, timeout: int) -> tuple[bytes, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 WallBreaker/0.1",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.5",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(1_000_000), response.headers.get("Content-Type", "")


def _guess_encoding(content_type: str) -> str:
    match = re.search(r"charset=([\w-]+)", content_type, flags=re.I)
    return match.group(1) if match else "utf-8"


def _strip_html(text: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
