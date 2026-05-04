"""Code execution tool."""
from typing import Optional
from app.agents.tool import Tool
from app.agents.sandbox import CodeExecutor, CodeExecutionTool


# Singleton instance
_code_tool: Optional[CodeTool] = None


def get_code_tool() -> CodeTool:
    """Get the singleton code tool instance."""
    global _code_tool
    if _code_tool is None:
        executor = CodeExecutor()
        _code_tool = CodeTool(executor)
        # Register the tool globally
        register_tool(_code_tool)
    return _code_tool


class CodeTool(CodeExecutionTool):
    """Tool for executing Python code (alias for CodeExecutionTool)."""
    pass
