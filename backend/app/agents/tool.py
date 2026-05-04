"""Tool framework for Agent function calling."""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class ToolCall:
    """Represents a tool call from the model."""
    id: str
    name: str
    arguments: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: dict) -> "ToolCall":
        """Create a ToolCall from a dictionary."""
        function = data.get("function", {})
        return cls(
            id=data.get("id", ""),
            name=function.get("name", ""),
            arguments=json.loads(function.get("arguments", "{}")) if isinstance(function.get("arguments"), str) else function.get("arguments", {})
        )


@dataclass
class ToolResult:
    """Result of a tool execution."""
    tool_call_id: str
    content: str
    is_error: bool = False
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "tool_call_id": self.tool_call_id,
            "content": self.content,
            "is_error": self.is_error,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms
        }


class Tool(ABC):
    """Abstract base class for tools."""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict = None
    ):
        self.name = name
        self.description = description
        self.parameters = parameters or self._get_parameters()
    
    @abstractmethod
    def _get_parameters(self) -> dict:
        """Return the JSON Schema for tool parameters."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        pass
    
    def get_definition(self) -> dict:
        """Get the tool definition for function calling."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    def __repr__(self) -> str:
        return f"<Tool(name={self.name})>"


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
    
    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        if name in self._tools:
            del self._tools[name]
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> list[Tool]:
        """List all registered tools."""
        return list(self._tools.values())
    
    def get_definitions(self) -> list[dict]:
        """Get definitions for all registered tools."""
        return [tool.get_definition() for tool in self._tools.values()]
    
    async def execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call."""
        tool = self.get(tool_call.name)
        if not tool:
            return ToolResult(
                tool_call_id=tool_call.id,
                content="",
                is_error=True,
                error_message=f"Tool '{tool_call.name}' not found"
            )
        
        try:
            start_time = datetime.now()
            result = await tool.execute(**tool_call.arguments)
            end_time = datetime.now()
            
            if isinstance(result, str):
                result = ToolResult(
                    tool_call_id=tool_call.id,
                    content=result
                )
            
            result.tool_call_id = tool_call.id
            result.execution_time_ms = (end_time - start_time).total_seconds() * 1000
            return result
            
        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                content="",
                is_error=True,
                error_message=str(e)
            )
    
    async def execute_tools(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        """Execute multiple tool calls."""
        results = []
        for tool_call in tool_calls:
            result = await self.execute_tool(tool_call)
            results.append(result)
        return results


# Global tool registry
_tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _tool_registry


def register_tool(tool: Tool) -> None:
    """Register a tool in the global registry."""
    _tool_registry.register(tool)


def list_tools() -> list[Tool]:
    """List all registered tools."""
    return _tool_registry.list_tools()


def get_tool_definitions() -> list[dict]:
    """Get all tool definitions."""
    return _tool_registry.get_definitions()
