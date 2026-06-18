"""OpenAI LLM provider."""

from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from .base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        api_key: str = "",
        model: str = "gpt-4o-mini",
        base_url: str = "",
    ) -> None:
        super().__init__(model=model, api_key=api_key, base_url=base_url)
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            tokens_input=response.usage.prompt_tokens if response.usage else 0,
            tokens_output=response.usage.completion_tokens if response.usage else 0,
            tokens_total=response.usage.total_tokens if response.usage else 0,
            cost_usd=self.estimate_cost(
                response.usage.prompt_tokens if response.usage else 0,
                response.usage.completion_tokens if response.usage else 0,
            ),
            finish_reason=choice.finish_reason or "stop",
        )

    def cost_per_token_input(self) -> float:
        if "gpt-4o" in self.model and "mini" in self.model:
            return 0.15 / 1_000_000
        if "gpt-4o" in self.model:
            return 2.50 / 1_000_000
        return 0.15 / 1_000_000

    def cost_per_token_output(self) -> float:
        if "gpt-4o" in self.model and "mini" in self.model:
            return 0.60 / 1_000_000
        if "gpt-4o" in self.model:
            return 10.00 / 1_000_000
        return 0.60 / 1_000_000
