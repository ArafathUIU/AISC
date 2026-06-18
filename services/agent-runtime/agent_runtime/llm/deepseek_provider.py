"""DeepSeek LLM provider."""

from __future__ import annotations

from typing import Any

import httpx

from .base import LLMProvider, LLMResponse


class DeepSeekProvider(LLMProvider):
    def __init__(
        self,
        api_key: str = "",
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com",
    ) -> None:
        super().__init__(model=model, api_key=api_key, base_url=base_url)

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs,
                },
            )
            data = response.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return LLMResponse(
                content=choice["message"]["content"],
                model=data["model"],
                tokens_input=usage.get("prompt_tokens", 0),
                tokens_output=usage.get("completion_tokens", 0),
                tokens_total=usage.get("total_tokens", 0),
                cost_usd=self.estimate_cost(
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0),
                ),
                finish_reason=choice.get("finish_reason", "stop"),
            )

    def cost_per_token_input(self) -> float:
        if "reasoner" in self.model:
            return 0.55 / 1_000_000
        return 0.27 / 1_000_000

    def cost_per_token_output(self) -> float:
        if "reasoner" in self.model:
            return 2.19 / 1_000_000
        return 1.10 / 1_000_000
