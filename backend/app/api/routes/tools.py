"""Tools API routes."""
from typing import Optional, List
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/tools", tags=["Tools"])


class ToolDefinition(BaseModel):
    """Tool definition schema."""
    name: str
    description: str
    parameters: dict


# Predefined tools
PREDEFINED_TOOLS = {
    "web_search": ToolDefinition(
        name="web_search",
        description="Search the web for information. Use this when you need to find current or specific information.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find information"
                }
            },
            "required": ["query"]
        }
    ),
    "calculator": ToolDefinition(
        name="calculator",
        description="Perform mathematical calculations. Use this for complex math operations.",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    ),
    "code_executor": ToolDefinition(
        name="code_executor",
        description="Execute Python code and return the result. Use this for running code snippets.",
        parameters={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code to execute"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language (default: python)",
                    "enum": ["python", "javascript"]
                }
            },
            "required": ["code"]
        }
    ),
    "weather": ToolDefinition(
        name="weather",
        description="Get current weather information for a location.",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or location"
                },
                "units": {
                    "type": "string",
                    "description": "Temperature units",
                    "enum": ["celsius", "fahrenheit"]
                }
            },
            "required": ["location"]
        }
    ),
    "file_reader": ToolDefinition(
        name="file_reader",
        description="Read content from a file in the workspace.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file relative to workspace"
                }
            },
            "required": ["path"]
        }
    ),
}


@router.get("")
async def list_tools() -> List[ToolDefinition]:
    """List all available tools."""
    return list(PREDEFINED_TOOLS.values())


@router.get("/{tool_name}")
async def get_tool(tool_name: str) -> ToolDefinition:
    """Get a specific tool by name."""
    if tool_name not in PREDEFINED_TOOLS:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    return PREDEFINED_TOOLS[tool_name]


@router.get("/by-category/{category}")
async def list_tools_by_category(category: str) -> List[ToolDefinition]:
    """List tools by category."""
    # For now, return all tools - could be extended with categories
    return list(PREDEFINED_TOOLS.values())


@router.post("/execute/{tool_name}")
async def execute_tool(tool_name: str, parameters: dict):
    """Execute a tool with given parameters."""
    if tool_name not in PREDEFINED_TOOLS:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    # Tool execution would be handled by the agent service
    # This is a placeholder for the API
    return {
        "tool": tool_name,
        "status": "not_implemented",
        "message": "Tool execution is handled by the agent service"
    }
