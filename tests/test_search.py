from __future__ import annotations

import unittest

from wallbreaker.ingestion.search import build_platform_queries


class SearchPlanTest(unittest.TestCase):
    def test_platform_queries_cover_required_channels(self) -> None:
        platforms = [platform for platform, _ in build_platform_queries("测试事件")]
        self.assertIn("fact_web", platforms)
        self.assertIn("news", platforms)
        self.assertIn("wechat", platforms)
        self.assertIn("zhihu", platforms)
        self.assertIn("weibo", platforms)
        self.assertIn("bilibili", platforms)
        self.assertIn("xiaohongshu", platforms)


if __name__ == "__main__":
    unittest.main()
