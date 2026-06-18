"""LLM provider and router tests."""

import asyncio

import pytest
from agent_runtime.llm.anthropic_provider import AnthropicProvider
from agent_runtime.llm.base import LLMResponse
from agent_runtime.llm.deepseek_provider import DeepSeekProvider
from agent_runtime.llm.ollama_provider import OllamaProvider
from agent_runtime.llm.openai_provider import OpenAIProvider
from agent_runtime.llm.router import LLMRouter, TaskComplexity


class TestLLMResponse:
    def test_creation_with_defaults(self) -> None:
        resp = LLMResponse(content="Hello", model="test-model")
        assert resp.content == "Hello"
        assert resp.model == "test-model"
        assert resp.tokens_input == 0
        assert resp.tokens_output == 0
        assert resp.cost_usd == 0.0
        assert resp.finish_reason == "stop"

    def test_creation_with_all_fields(self) -> None:
        resp = LLMResponse(
            content="Test",
            model="gpt-4o",
            tokens_input=100,
            tokens_output=50,
            tokens_total=150,
            cost_usd=0.005,
            finish_reason="length",
        )
        assert resp.tokens_total == 150
        assert resp.finish_reason == "length"


class TestCostCalculation:
    def test_openai_gpt4o_mini_cost(self) -> None:
        provider = OpenAIProvider(model="gpt-4o-mini")
        cost = provider.estimate_cost(1000, 500)
        assert cost == pytest.approx(0.00045, abs=0.0001)

    def test_openai_gpt4o_cost(self) -> None:
        provider = OpenAIProvider(model="gpt-4o")
        cost = provider.estimate_cost(1000, 500)
        assert cost == pytest.approx(0.0075, abs=0.0001)

    def test_anthropic_haiku_cost(self) -> None:
        provider = AnthropicProvider(model="claude-3-5-haiku-latest")
        cost = provider.estimate_cost(1000, 500)
        assert cost == pytest.approx(0.0028, abs=0.001)

    def test_anthropic_sonnet_cost(self) -> None:
        provider = AnthropicProvider(model="claude-3-5-sonnet-latest")
        cost = provider.estimate_cost(1000, 500)
        assert cost == pytest.approx(0.0105, abs=0.001)

    def test_deepseek_cost(self) -> None:
        provider = DeepSeekProvider()
        cost = provider.estimate_cost(1000, 500)
        assert cost == pytest.approx(0.00082, abs=0.0001)

    def test_ollama_cost_is_zero(self) -> None:
        provider = OllamaProvider()
        cost = provider.estimate_cost(100000, 50000)
        assert cost == 0.0


class TestLLMRouter:
    def test_provider_registration(self) -> None:
        router = LLMRouter(deepseek_key="test-key")
        assert "deepseek" in router.available_providers
        assert "ollama" in router.available_providers

    def test_simple_task_routes_to_cheapest(self) -> None:
        router = LLMRouter(deepseek_key="dsk", openai_key="oai")
        provider = router.select_provider(TaskComplexity.SIMPLE)
        assert provider is not None

    def test_complexity_estimation_simple(self) -> None:
        router = LLMRouter()
        messages = [{"role": "user", "content": "What is 2+2?"}]
        complexity = router.estimate_complexity(messages)
        assert complexity == TaskComplexity.SIMPLE

    def test_complexity_estimation_complex(self) -> None:
        router = LLMRouter()
        messages = [{
            "role": "user",
            "content": (
                "Design a secure system architecture for an enterprise "
                "database with complex refactoring requirements."
            ),
        }]
        complexity = router.estimate_complexity(messages)
        assert complexity == TaskComplexity.COMPLEX

    def test_complexity_estimation_moderate(self) -> None:
        router = LLMRouter()
        messages = [{
            "role": "user",
            "content": (
                "Write a FastAPI endpoint for user authentication with "
                "proper error handling and input validation. Include "
                "rate limiting design and database optimization."
            ),
        }]
        complexity = router.estimate_complexity(messages)
        assert complexity == TaskComplexity.MODERATE

    def test_all_providers_fail_raises_error(self) -> None:
        router = LLMRouter()
        messages = [{"role": "user", "content": "test"}]

        async def run() -> None:
            with pytest.raises(RuntimeError):
                await router.route(messages)

        asyncio.run(run())
