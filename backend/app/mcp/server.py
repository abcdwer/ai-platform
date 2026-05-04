"""MCP (Model Context Protocol) server management."""
import asyncio
import json
import logging
from typing import Optional, Any, Callable, AsyncIterator
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """MCP message types."""
    # JSON-RPC 2.0
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    
    # MCP specific
    INITIALIZE = "initialize"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    PROMPTS_LIST = "prompts/list"
    SAMPLING_CREATE = "sampling/create"


class MCPProtocol:
    """
    MCP Protocol implementation.
    
    Handles message formatting, parsing, and protocol compliance.
    """
    
    VERSION = "2024-11-05"
    
    @staticmethod
    def format_request(
        method: str,
        params: Optional[dict] = None,
        request_id: Optional[str] = None,
    ) -> dict:
        """Format a JSON-RPC 2.0 request."""
        message = {
            "jsonrpc": "2.0",
            "method": method,
        }
        
        if params:
            message["params"] = params
        
        if request_id:
            message["id"] = request_id
        
        return message
    
    @staticmethod
    def format_response(
        result: Any,
        request_id: str,
    ) -> dict:
        """Format a JSON-RPC 2.0 success response."""
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id,
        }
    
    @staticmethod
    def format_error(
        code: int,
        message: str,
        request_id: Optional[str] = None,
        data: Optional[Any] = None,
    ) -> dict:
        """Format a JSON-RPC 2.0 error response."""
        error = {
            "code": code,
            "message": message,
        }
        
        if data is not None:
            error["data"] = data
        
        response = {
            "jsonrpc": "2.0",
            "error": error,
        }
        
        if request_id:
            response["id"] = request_id
        
        return response
    
    @staticmethod
    def parse_message(message: dict) -> dict:
        """Parse and validate an MCP message."""
        if message.get("jsonrpc") != "2.0":
            raise ValueError("Invalid JSON-RPC version")
        
        return message


class MCPErrorCodes:
    """Standard MCP error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # Server errors
    SERVER_ERROR = -32000
    CONNECTION_FAILED = -32001
    TIMEOUT = -32002
    TOOL_NOT_FOUND = -32003
    TOOL_EXECUTION_FAILED = -32004
    RESOURCE_NOT_FOUND = -32005


class ServerManager:
    """
    Manages MCP server lifecycle and connections.
    """
    
    def __init__(self):
        self._servers: dict[str, "MCPServerInstance"] = {}
    
    async def create_server(
        self,
        server_id: str,
        transport_type: str,
        config: dict,
    ) -> "MCPServerInstance":
        """Create and register a server instance."""
        if transport_type == "sse":
            server = SSEServerInstance(server_id, config)
        elif transport_type == "stdio":
            server = StdioServerInstance(server_id, config)
        elif transport_type == "http_stream":
            server = HTTPStreamServerInstance(server_id, config)
        else:
            raise ValueError(f"Unknown transport type: {transport_type}")
        
        self._servers[server_id] = server
        return server
    
    def get_server(self, server_id: str) -> Optional["MCPServerInstance"]:
        """Get a server instance."""
        return self._servers.get(server_id)
    
    async def remove_server(self, server_id: str) -> bool:
        """Remove a server instance."""
        server = self._servers.pop(server_id, None)
        if server:
            await server.disconnect()
            return True
        return False


class MCPServerInstance:
    """Base class for MCP server instances."""
    
    def __init__(self, server_id: str, config: dict):
        self.server_id = server_id
        self.config = config
        self._is_connected = False
        self._session_id: Optional[str] = None
    
    async def connect(self) -> dict:
        """Connect to the server."""
        raise NotImplementedError
    
    async def disconnect(self) -> None:
        """Disconnect from the server."""
        raise NotImplementedError
    
    async def send_message(self, message: dict) -> dict:
        """Send a message to the server."""
        raise NotImplementedError
    
    async def receive_messages(self) -> AsyncIterator[dict]:
        """Receive messages from the server."""
        raise NotImplementedError
    
    async def initialize(self) -> dict:
        """Send initialize request."""
        request = MCPProtocol.format_request(
            method="initialize",
            params={
                "protocolVersion": MCPProtocol.VERSION,
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {},
                },
                "clientInfo": {
                    "name": "ai-platform",
                    "version": "1.0.0",
                },
            },
        )
        
        response = await self.send_message(request)
        
        if "error" in response:
            raise RuntimeError(f"Initialize failed: {response['error']}")
        
        self._is_connected = True
        return response.get("result", {})
    
    async def list_tools(self) -> list[dict]:
        """List available tools."""
        request = MCPProtocol.format_request(
            method="tools/list",
            params={},
        )
        
        response = await self.send_message(request)
        
        if "error" in response:
            raise RuntimeError(f"List tools failed: {response['error']}")
        
        result = response.get("result", {})
        return result.get("tools", [])
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
    ) -> dict:
        """Call a tool."""
        request = MCPProtocol.format_request(
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments,
            },
        )
        
        response = await self.send_message(request)
        
        if "error" in response:
            raise RuntimeError(f"Tool call failed: {response['error']}")
        
        return response.get("result", {})


class SSEServerInstance(MCPServerInstance):
    """SSE transport implementation."""
    
    def __init__(self, server_id: str, config: dict):
        super().__init__(server_id, config)
        self.url = config.get("url")
        self.endpoint = config.get("endpoint", "/sse")
        self._session: Optional[Any] = None
    
    async def connect(self) -> dict:
        """Connect via SSE."""
        # In production, use httpx or aiohttp
        # For now, simulate connection
        self._session_id = "sse-session-123"
        self._is_connected = True
        
        return {
            "session_id": self._session_id,
            "transport": "sse",
        }
    
    async def disconnect(self) -> None:
        """Disconnect SSE session."""
        if self._session:
            await self._session.aclose()
        self._is_connected = False
    
    async def send_message(self, message: dict) -> dict:
        """Send message via SSE POST."""
        # In production, POST to the SSE endpoint
        logger.info(f"SSE send: {message}")
        return MCPProtocol.format_response({"status": "ok"}, "1")
    
    async def receive_messages(self) -> AsyncIterator[dict]:
        """Receive messages from SSE stream."""
        # In production, this would read from the SSE stream
        while self._is_connected:
            await asyncio.sleep(1)
            yield {}


class StdioServerInstance(MCPServerInstance):
    """Stdio transport implementation."""
    
    def __init__(self, server_id: str, config: dict):
        super().__init__(server_id, config)
        self.command = config.get("command")
        self.args = config.get("args", [])
        self.env = config.get("env", {})
        self._process: Optional[asyncio.subprocess.Process] = None
    
    async def connect(self) -> dict:
        """Start stdio process."""
        self._process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**({"PATH": "/usr/local/bin:/usr/bin:/bin"}), **self.env},
        )
        
        self._session_id = str(self._process.pid)
        self._is_connected = True
        
        return {
            "session_id": self._session_id,
            "transport": "stdio",
            "pid": self._process.pid,
        }
    
    async def disconnect(self) -> None:
        """Stop the process."""
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
                await self._process.wait()
        self._is_connected = False
    
    async def send_message(self, message: dict) -> dict:
        """Send message via stdin."""
        if not self._process or not self._is_connected:
            raise RuntimeError("Not connected")
        
        line = json.dumps(message) + "\n"
        self._process.stdin.write(line.encode())
        await self._process.stdin.drain()
        
        # Read response
        response_line = await self._process.stdout.readline()
        if response_line:
            return json.loads(response_line.decode())
        
        return MCPProtocol.format_error(
            MCPErrorCodes.INTERNAL_ERROR,
            "No response from server"
        )
    
    async def receive_messages(self) -> AsyncIterator[dict]:
        """Read messages from stdout."""
        if not self._process:
            return
        
        while self._is_connected:
            try:
                line = await asyncio.wait_for(
                    self._process.stdout.readline(),
                    timeout=30.0,
                )
                if line:
                    yield json.loads(line.decode())
            except asyncio.TimeoutError:
                continue


class HTTPStreamServerInstance(MCPServerInstance):
    """HTTP Stream transport implementation."""
    
    def __init__(self, server_id: str, config: dict):
        super().__init__(server_id, config)
        self.url = config.get("url")
        self.headers = config.get("headers", {})
        self._session: Optional[Any] = None
    
    async def connect(self) -> dict:
        """Connect via HTTP stream."""
        # In production, establish HTTP/2 connection
        self._session_id = "http-session-123"
        self._is_connected = True
        
        return {
            "session_id": self._session_id,
            "transport": "http_stream",
        }
    
    async def disconnect(self) -> None:
        """Close HTTP connection."""
        if self._session:
            await self._session.aclose()
        self._is_connected = False
    
    async def send_message(self, message: dict) -> dict:
        """Send message via HTTP POST."""
        # In production, POST to the HTTP endpoint
        logger.info(f"HTTP send: {message}")
        return MCPProtocol.format_response({"status": "ok"}, "1")
    
    async def receive_messages(self) -> AsyncIterator[dict]:
        """Receive messages from HTTP stream."""
        while self._is_connected:
            await asyncio.sleep(1)
            yield {}


# Global server manager
_server_manager = ServerManager()


def get_server_manager() -> ServerManager:
    """Get the global server manager."""
    return _server_manager
