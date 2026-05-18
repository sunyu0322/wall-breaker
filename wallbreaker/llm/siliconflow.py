from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Protocol


class LlmClient(Protocol):
    def chat(self, model: str, system: str, user: str, temperature: float = 0.4) -> str:
        ...


class SiliconFlowClient:
    def __init__(self, api_key: str, base_url: str = "https://api.siliconflow.com/v1", timeout: int = 120) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def chat(self, model: str, system: str, user: str, temperature: float = 0.4) -> str:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"SiliconFlow HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"SiliconFlow network error: {exc}") from exc
        return data["choices"][0]["message"]["content"]


class MockLlmClient:
    def chat(self, model: str, system: str, user: str, temperature: float = 0.4) -> str:
        if "输出 JSON" in system:
            return json.dumps(
                {
                    "thesis": "把事件说成个体选择或偶发冲突，是最省事的伪命题。",
                    "antithesis": "真正需要计算的是成本如何被转嫁：时间、情绪、风险与尊严由普通人承担。",
                    "synthesis": "当解释反复压过诉求，反抗就不再是噪音，而是结构性失衡的回声。",
                    "evidence_map": [
                        {"claim": "公众质疑集中在成本转嫁", "raw_item_id": "AUTO_FIRST"},
                        {"claim": "亲历者表达了无力感", "raw_item_id": "AUTO_LAST"},
                    ],
                    "risks": ["真实上线前需要接入去重、反通稿和合规改写。"],
                    "outline": ["解构伪命题", "计算经济账", "揭示反噬"],
                },
                ensure_ascii=False,
                indent=2,
            )
        return (
            "# 这不是偶发事件，而是一套成本转嫁机器\n\n"
            "## 开场\n"
            "每次类似事件出现，最熟悉的解释总会第一时间赶到：不要上纲上线，不要情绪化，要理性看待。"
            "可问题恰恰在这里，所谓理性，常常只是要求承担代价的人把痛感说得更小声一点。[E:AUTO_FIRST]\n\n"
            "## 第一层：解构伪命题\n"
            "把矛盾说成个体选择，是一种非常轻巧的叙事。它绕开了规则是谁制定的，成本是谁承担的，只留下一个看似中立的问题：你为什么不能适应？[E:AUTO_FIRST]\n\n"
            "## 第二层：刺穿资产与阶级底色\n"
            "如果我们不做道德审判，只算账，就会发现普通人的时间、注意力、情绪稳定和风险承受能力，都被当成了可以无限透支的原材料。[E:AUTO_FIRST]\n\n"
            "## 第三层：结构性反噬\n"
            "当诉求长期被解释、被稀释、被礼貌地推回去，情绪爆发就不是不理性，而是最后一种可见性。[E:AUTO_LAST]\n\n"
            "## 结尾\n"
            "所以真正需要被讨论的，不是谁说话太冲，而是谁拥有把别人痛感定义为噪音的权力。"
        )
