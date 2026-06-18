"""LLM Provider base class and factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0
    cost_usd: float = 0.0
    finish_reason: str = "stop"
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    def __init__(self, model: str, api_key: str = "", base_url: str = "") -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        ...

    @abstractmethod
    def cost_per_token_input(self) -> float:
        ...

    @abstractmethod
    def cost_per_token_output(self) -> float:
        ...

    def estimate_cost(self, tokens_input: int, tokens_output: int) -> float:
        return (tokens_input * self.cost_per_token_input()
                + tokens_output * self.cost_per_token_output())
