"""Code execution sandbox for secure code running."""
import ast
import io
import sys
import traceback
import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass
from contextlib import redirect_stdout, redirect_stderr

from app.agents.tool import Tool, ToolResult


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time_ms: float = 0


class CodeExecutor:
    """Safe code execution sandbox."""
    
    def __init__(self, timeout: int = 30, max_output_length: int = 10000):
        self.timeout = timeout
        self.max_output_length = max_output_length
        
        # Restricted modules and builtins
        self.allowed_modules = {
            "math", "random", "datetime", "time", "json", "re",
            "collections", "itertools", "functools", "operator",
            "string", "textwrap", "decimal", "fractions", "complex"
        }
        
        self.restricted_names = {
            "open", "eval", "exec", "compile", "__import__",
            "breakpoint", "exit", "quit", "help", "copyright",
            "license", "credits", "input"
        }
    
    def _create_safe_globals(self) -> Dict[str, Any]:
        """Create safe global namespace for execution."""
        safe_globals = {
            "__builtins__": {
                name: getattr(__builtins__, name) 
                for name in dir(__builtins__) 
                if name not in self.restricted_names
            }
        }
        
        # Add allowed modules
        for module_name in self.allowed_modules:
            try:
                safe_globals[module_name] = __import__(module_name)
            except ImportError:
                pass
        
        return safe_globals
    
    def execute(self, code: str, language: str = "python") -> ExecutionResult:
        """Execute code in a sandbox."""
        import time
        start_time = time.time()
        
        if language.lower() != "python":
            return ExecutionResult(
                success=False,
                output="",
                error=f"Language '{language}' is not supported. Only Python is supported."
            )
        
        # Check for potentially dangerous patterns
        if self._is_dangerous(code):
            return ExecutionResult(
                success=False,
                output="",
                error="Code contains potentially dangerous patterns and was blocked."
            )
        
        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        safe_globals = self._create_safe_globals()
        
        try:
            # Compile the code first to check for syntax errors
            compiled = compile(code, "<string>", "exec")
            
            # Execute with output capture
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(compiled, safe_globals, {})
            
            output = stdout_capture.getvalue()
            error = stderr_capture.getvalue()
            
            # Truncate output if too long
            if len(output) > self.max_output_length:
                output = output[:self.max_output_length] + f"\n... (output truncated, {len(output)} chars total)"
            
            execution_time = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                success=True,
                output=output,
                error=error if error else None,
                execution_time_ms=execution_time
            )
            
        except SyntaxError as e:
            execution_time = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=False,
                output="",
                error=f"Syntax Error: {e}",
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = traceback.format_exc()
            
            # Truncate error if too long
            if len(error_msg) > self.max_output_length:
                error_msg = error_msg[:self.max_output_length] + f"\n... (error truncated)"
            
            return ExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=error_msg,
                execution_time_ms=execution_time
            )
    
    def _is_dangerous(self, code: str) -> bool:
        """Check if code contains dangerous patterns."""
        dangerous_patterns = [
            "import os",
            "import sys",
            "import subprocess",
            "import socket",
            "import requests",
            "import urllib",
            "import http",
            "from os",
            "from sys",
            "from subprocess",
            "open(",
            "__import__",
            "eval(",
            "exec(",
            "compile(",
            "getattr(",
            "setattr(",
            "delattr(",
            "globals(",
            "locals(",
            "vars(",
            "memoryview(",
            "buffer(",
        ]
        
        code_lower = code.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in code_lower:
                return True
        
        return False


class CodeExecutionTool(Tool):
    """Tool for executing Python code."""
    
    def __init__(self, executor: CodeExecutor = None):
        super().__init__(
            name="execute_code",
            description="Execute Python code and return the output. Use this for calculations, data processing, or running algorithms. Returns stdout, stderr, and execution time.",
        )
        self.executor = executor or CodeExecutor()
    
    def _get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. Only standard library modules are available. Do not use imports like os, sys, subprocess, or any network requests."
                },
                "language": {
                    "type": "string",
                    "description": "Programming language (currently only 'python' is supported)",
                    "enum": ["python"],
                    "default": "python"
                }
            },
            "required": ["code"]
        }
    
    async def execute(self, code: str, language: str = "python") -> ToolResult:
        """Execute Python code."""
        result = self.executor.execute(code, language)
        
        if result.success:
            output = result.output
            if result.error:
                output += f"\n\nstderr:\n{result.error}"
            
            return ToolResult(
                tool_call_id="",
                content=f"Code executed successfully in {result.execution_time_ms:.2f}ms:\n\n{output}" if output else f"Code executed successfully in {result.execution_time_ms:.2f}ms (no output)"
            )
        else:
            return ToolResult(
                tool_call_id="",
                content="",
                is_error=True,
                error_message=f"Execution failed after {result.execution_time_ms:.2f}ms:\n{result.error}"
            )


# Create a singleton instance
code_executor = CodeExecutor()
code_execution_tool = CodeExecutionTool(code_executor)
