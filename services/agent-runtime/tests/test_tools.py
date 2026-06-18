"""Tool execution framework tests."""

import asyncio

from agent_runtime.tools.base import BaseTool, ToolRegistry, ToolResult


class MockTool(BaseTool):
    async def execute(self, **kwargs):  # type: ignore[override]
        value = kwargs.get("value", 42)
        if value == "fail":
            return ToolResult(success=False, error="requested failure")
        return ToolResult(success=True, output={"result": value})

    def get_parameters(self):  # type: ignore[override]
        return {
            "type": "object",
            "properties": {
                "value": {"type": "string", "description": "Test parameter"},
            },
            "required": [],
        }


class TestToolResult:
    def test_success_result(self) -> None:
        result = ToolResult(success=True, output={"data": 123})
        assert result.success is True
        assert result.output == {"data": 123}
        assert result.error is None

    def test_failure_result(self) -> None:
        result = ToolResult(success=False, error="Something went wrong")
        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.output is None


class TestBaseTool:
    def test_tool_has_name_and_description(self) -> None:
        tool = MockTool("test_tool", "A test tool")
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"

    def test_to_schema(self) -> None:
        tool = MockTool("test_tool", "A test tool")
        schema = tool.to_schema()
        assert schema["name"] == "test_tool"
        assert schema["description"] == "A test tool"
        assert "parameters" in schema

    async def test_execute_success(self) -> None:
        tool = MockTool("test_tool", "")
        result = await tool.execute(value=99)
        assert result.success is True
        assert result.output == {"result": 99}  # type: ignore[union-attr]

    async def test_execute_failure(self) -> None:
        tool = MockTool("test_tool", "")
        result = await tool.execute(value="fail")
        assert result.success is False
        assert result.error == "requested failure"


class TestToolRegistry:
    def test_register_and_get(self) -> None:
        registry = ToolRegistry()
        tool = MockTool("my_tool", "desc")
        registry.register(tool)
        assert registry.get("my_tool") is tool

    def test_list_tools(self) -> None:
        registry = ToolRegistry()
        registry.register(MockTool("tool_a", ""))
        registry.register(MockTool("tool_b", ""))
        tools = registry.list_tools()
        assert len(tools) == 2

    def test_list_schemas(self) -> None:
        registry = ToolRegistry()
        registry.register(MockTool("tool_a", "Alpha"))
        schemas = registry.list_schemas()
        assert len(schemas) == 1
        assert schemas[0]["name"] == "tool_a"


class TestConcreteTools:
    def test_code_generation_tool(self) -> None:
        from agent_runtime.tools.code_generation import CodeGenerationTool
        tool = CodeGenerationTool()
        result = asyncio.run(tool.execute(
            language="python",
            specification="Create a FastAPI health endpoint",
            framework="fastapi",
        ))
        assert result.success is True

    def test_static_analysis_tool(self) -> None:
        from agent_runtime.tools.static_analysis import StaticAnalysisTool
        tool = StaticAnalysisTool()
        result = asyncio.run(tool.execute(
            path="services/agent-runtime/agent_runtime/tools",
            checks=["ruff"],
        ))
        assert result.success is True

    def test_git_ops_status(self) -> None:
        from agent_runtime.tools.git_ops import GitOpsTool
        tool = GitOpsTool()
        result = asyncio.run(tool.execute(operation="status", path="."))
        assert result.success is True
