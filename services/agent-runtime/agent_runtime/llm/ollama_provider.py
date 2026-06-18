"""Ollama local LLM provider (Llama, Mistral, etc.)."""

from __future__ import annotations

from typing import Any

import httpx

from .base import LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    def __init__(
        self,
        api_key: str = "",
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
    ) -> None:
        super().__init__(model=model, api_key=api_key, base_url=base_url)

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                    "stream": False,
                    **kwargs,
                },
            )
            data = response.json()
            return LLMResponse(
                content=data["message"]["content"],
                model=data["model"],
                tokens_input=data.get("prompt_eval_count", 0),
                tokens_output=data.get("eval_count", 0),
                tokens_total=(
                    data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                ),
                cost_usd=0.0,
                finish_reason=data.get("done_reason", "stop"),
            )

    def cost_per_token_input(self) -> float:
        return 0.0

    def cost_per_token_output(self) -> float:
        return 0.0
