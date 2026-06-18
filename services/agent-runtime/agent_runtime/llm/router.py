"""Cost-aware LLM router — selects cheapest capable model per task."""

from __future__ import annotations

from enum import StrEnum

from .anthropic_provider import AnthropicProvider
from .base import LLMProvider, LLMResponse
from .deepseek_provider import DeepSeekProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider


class TaskComplexity(StrEnum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


ROUTING_TABLE: dict[TaskComplexity, list[str]] = {
    TaskComplexity.SIMPLE: ["ollama", "deepseek", "gpt-4o-mini", "haiku"],
    TaskComplexity.MODERATE: ["deepseek", "gpt-4o-mini", "haiku", "sonnet"],
    TaskComplexity.COMPLEX: ["sonnet", "gpt-4o", "deepseek-reasoner"],
}


class LLMRouter:
    def __init__(self, openai_key: str = "", anthropic_key: str = "",
                 deepseek_key: str = "") -> None:
        self._providers: dict[str, LLMProvider] = {}

        if openai_key:
            self._providers["gpt-4o-mini"] = OpenAIProvider(
                api_key=openai_key, model="gpt-4o-mini"
            )
            self._providers["gpt-4o"] = OpenAIProvider(
                api_key=openai_key, model="gpt-4o"
            )
        if anthropic_key:
            self._providers["sonnet"] = AnthropicProvider(
                api_key=anthropic_key, model="claude-3-5-sonnet-latest"
            )
            self._providers["haiku"] = AnthropicProvider(
                api_key=anthropic_key, model="claude-3-5-haiku-latest"
            )
        if deepseek_key:
            self._providers["deepseek"] = DeepSeekProvider(
                api_key=deepseek_key, model="deepseek-chat"
            )
        self._providers["ollama"] = OllamaProvider()

    def register(self, name: str, provider: LLMProvider) -> None:
        self._providers[name] = provider

    def select_provider(self, complexity: TaskComplexity) -> LLMProvider:
        for name in ROUTING_TABLE.get(complexity, []):
            if name in self._providers:
                return self._providers[name]
        return next(iter(self._providers.values()))

    def estimate_complexity(self, messages: list[dict[str, str]]) -> TaskComplexity:
        text = " ".join(m["content"] for m in messages)
        word_count = len(text.split())

        complexity_indicators = [
            "architecture", "design", "system", "security", "database",
            "refactor", "optimize", "complex", "enterprise",
        ]
        indicator_count = sum(1 for w in complexity_indicators if w in text.lower())

        if word_count > 3000 or indicator_count >= 3:
            return TaskComplexity.COMPLEX
        if word_count > 1000 or indicator_count >= 1:
            return TaskComplexity.MODERATE
        return TaskComplexity.SIMPLE

    async def route(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        complexity: TaskComplexity | None = None,
    ) -> LLMResponse:
        if complexity is None:
            complexity = self.estimate_complexity(messages)

        provider_names = ROUTING_TABLE.get(complexity, [])
        last_error: Exception | None = None

        for name in provider_names:
            provider = self._providers.get(name)
            if provider is None:
                continue
            try:
                return await provider.chat(
                    messages, temperature=temperature, max_tokens=max_tokens
                )
            except Exception as e:
                last_error = e
                continue

        if last_error:
            raise RuntimeError(
                f"All LLM providers failed. Last error: {last_error}"
            )
        raise RuntimeError("No LLM providers available")

    @property
    def available_providers(self) -> list[str]:
        return list(self._providers.keys())
