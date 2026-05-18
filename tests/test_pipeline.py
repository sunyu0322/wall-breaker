from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from wallbreaker.pipeline import run_pipeline


class PipelineTest(unittest.TestCase):
    def test_pipeline_generates_core_artifacts(self) -> None:
        old_value = os.environ.get("WALLBREAKER_USE_MOCK_LLM")
        os.environ["WALLBREAKER_USE_MOCK_LLM"] = "true"
        try:
            with tempfile.TemporaryDirectory() as tmp:
                output_root = Path(tmp)
                report = run_pipeline("测试议题", output_root=output_root, per_source_limit=1)

                run_dir = output_root / report["run_id"]
                self.assertTrue((run_dir / "raw_items.jsonl").exists())
                self.assertTrue((run_dir / "analysis.json").exists())
                self.assertTrue((run_dir / "script.md").exists())
                self.assertTrue((run_dir / "visual_timeline.json").exists())

                analysis = json.loads((run_dir / "analysis.json").read_text(encoding="utf-8"))
                timeline = json.loads((run_dir / "visual_timeline.json").read_text(encoding="utf-8"))
                script = (run_dir / "script.md").read_text(encoding="utf-8")
                self.assertEqual(analysis["status"], "insufficient_evidence")
                self.assertEqual(timeline, [])
                self.assertIn("研究缺口清单", script)
                self.assertEqual(report["raw_items"], 5)
                self.assertEqual(report["ingestion_mode"], "mock")
        finally:
            if old_value is None:
                os.environ.pop("WALLBREAKER_USE_MOCK_LLM", None)
            else:
                os.environ["WALLBREAKER_USE_MOCK_LLM"] = old_value


if __name__ == "__main__":
    unittest.main()
