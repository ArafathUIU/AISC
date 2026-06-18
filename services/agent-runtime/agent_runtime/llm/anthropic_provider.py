"""Anthropic Claude LLM provider."""

from __future__ import annotations

from typing import Any

from anthropic import AsyncAnthropic

from .base import LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        api_key: str = "",
        model: str = "claude-3-5-haiku-latest",
        base_url: str = "",
    ) -> None:
        super().__init__(model=model, api_key=api_key, base_url=base_url)
        self._client: AsyncAnthropic | None = None

    def _get_client(self) -> AsyncAnthropic:
        if self._client is None:
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        client = self._get_client()
        system_msg = ""
        user_messages: list[dict[str, str]] = []

        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_messages.append(msg)

        response = await client.messages.create(
            model=self.model,
            system=system_msg if system_msg else None,
            messages=user_messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            tokens_input=response.usage.input_tokens if response.usage else 0,
            tokens_output=response.usage.output_tokens if response.usage else 0,
            tokens_total=(
                response.usage.input_tokens + response.usage.output_tokens
                if response.usage else 0
            ),
            cost_usd=self.estimate_cost(
                response.usage.input_tokens if response.usage else 0,
                response.usage.output_tokens if response.usage else 0,
            ),
            finish_reason=response.stop_reason or "stop",
        )

    def cost_per_token_input(self) -> float:
        if "sonnet" in self.model:
            return 3.00 / 1_000_000
        if "haiku" in self.model:
            return 0.80 / 1_000_000
        return 15.00 / 1_000_000

    def cost_per_token_output(self) -> float:
        if "sonnet" in self.model:
            return 15.00 / 1_000_000
        if "haiku" in self.model:
            return 4.00 / 1_000_000
        return 75.00 / 1_000_000
