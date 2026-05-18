from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"'))


@dataclass(frozen=True)
class Settings:
    siliconflow_api_key: str | None
    siliconflow_base_url: str
    reasoner_model: str
    writer_model: str
    use_mock_llm: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            siliconflow_api_key=os.getenv("SILICONFLOW_API_KEY") or None,
            siliconflow_base_url=os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.com/v1"),
            reasoner_model=os.getenv("DEEPSEEK_REASONER_MODEL", "deepseek-ai/DeepSeek-R1"),
            writer_model=os.getenv("DEEPSEEK_WRITER_MODEL", "deepseek-ai/DeepSeek-V3"),
            use_mock_llm=os.getenv("WALLBREAKER_USE_MOCK_LLM", "auto").lower(),
        )

    @property
    def should_mock_llm(self) -> bool:
        if self.use_mock_llm in {"1", "true", "yes", "on"}:
            return True
        if self.use_mock_llm in {"0", "false", "no", "off"}:
            return False
        return not self.siliconflow_api_key
