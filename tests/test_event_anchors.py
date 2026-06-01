from __future__ import annotations

import unittest

from wallbreaker.models import RawItem
from wallbreaker.scripting.dialectical import extract_event_anchors


class EventAnchorTest(unittest.TestCase):
    def test_oppo_anchor_keeps_original_wording(self) -> None:
        item = RawItem(
            source="manual_text",
            query="oppo母亲节文案塌房事件",
            raw_text=(
                "2026年5月8日，OPPO发布母亲节活动文案引发争议。"
                "其争议文案内容为：我妈有两个“老公”，一个是我爸，另一个一年见两回。"
                "跟我爸约会基本不打扮，见另一个，她恨不得穿婚纱。"
                "5月10日，中国广告协会发声；5月11日，OPPO内部发布问责通告。"
            ),
        )

        anchors = extract_event_anchors("oppo母亲节文案塌房事件", [item])

        self.assertIn("original_wording", anchors["found"])
        self.assertIn("event_date", anchors["found"])
        self.assertIn("advertising_association", anchors["found"])
        self.assertIn("accountability", anchors["found"])
        self.assertIn("两个", anchors["found"]["original_wording"][0]["quote"])


if __name__ == "__main__":
    unittest.main()
