"""MCP (Model Context Protocol) service."""
import json
import uuid
import asyncio
import logging
from typing import Optional, Any, AsyncIterator
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.mcp import MCPServer, MCPTool, MCPConnection, MCPLog

logger = logging.getLogger(__name__)


class TransportType(str, Enum):
    """MCP transport types."""
    SSE = "sse"
    STDIO = "stdio"
    HTTP_STREAM = "http_stream"


class ConnectionStatus(str, Enum):
    """Connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"


@dataclass
class ToolCallResult:
    """Result of a tool call."""
    success: bool
    result: Optional[Any]
    error: Optional[str]
    execution_time_ms: int


class MCPService:
    """Service for managing MCP servers and tools."""
    
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        
        # In-memory connection management
        self._connections: dict[str, dict] = {}
        self._processes: dict[str, asyncio.subprocess.Process] = {}
    
    # ============== Server Management ==============
    
    async def create_server(
        self,
        name: str,
        transport_type: str,
        description: Optional[str] = None,
        # SSE config
        sse_url: Optional[str] = None,
        sse_endpoint: Optional[str] = None,
        # Stdio config
        stdio_command: Optional[str] = None,
        stdio_args: Optional[list] = None,
        stdio_env: Optional[dict] = None,
        # HTTP config
        http_url: Optional[str] = None,
        http_headers: Optional[dict] = None,
        # Auth
        auth_type: Optional[str] = None,
        auth_config: Optional[dict] = None,
        # Settings
        timeout: int = 30,
        max_retries: int = 3,
    ) -> MCPServer:
        """Create a new MCP server."""
        server_id = str(uuid.uuid4())
        
        server = MCPServer(
            id=server_id,
            user_id=self.user_id,
            name=name,
            description=description,
            transport_type=transport_type,
            sse_url=sse_url,
            sse_endpoint=sse_endpoint,
            stdio_command=stdio_command,
            stdio_args=stdio_args,
            stdio_env=stdio_env,
            http_url=http_url,
            http_headers=http_headers,
            auth_type=auth_type,
            auth_config=auth_config,
            timeout=timeout,
            max_retries=max_retries,
        )
        
        self.db.add(server)
        await self.db.commit()
        await self.db.refresh(server)
        
        return server
    
    async def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get server by ID."""
        result = await self.db.execute(
            select(MCPServer).where(
                MCPServer.id == server_id,
                MCPServer.user_id == self.user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def list_servers(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[MCPServer], int]:
        """List all servers."""
        count_query = select(func.count(MCPServer.id)).where(
            MCPServer.user_id == self.user_id
        )
        total = (await self.db.execute(count_query)).scalar()
        
        query = select(MCPServer).where(
            MCPServer.user_id == self.user_id
        ).order_by(MCPServer.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        servers = result.scalars().all()
        
        return list(servers), total
    
    async def update_server(
        self,
        server_id: str,
        **updates,
    ) -> Optional[MCPServer]:
        """Update server configuration."""
        server = await self.get_server(server_id)
        if not server:
            return None
        
        for key, value in updates.items():
            if hasattr(server, key):
                setattr(server, key, value)
        
        await self.db.commit()
        await self.db.refresh(server)
        
        return server
    
    async def delete_server(self, server_id: str) -> bool:
        """Delete a server."""
        server = await self.get_server(server_id)
        if not server:
            return False
        
        # Disconnect if connected
        if server.is_connected:
            await self.disconnect_server(server_id)
        
        await self.db.delete(server)
        await self.db.commit()
        
        return True
    
    # ============== Connection Management ==============
    
    async def connect_server(self, server_id: str) -> dict:
        """Connect to an MCP server."""
        server = await self.get_server(server_id)
        if not server:
            raise ValueError(f"Server not found: {server_id}")
        
        connection_id = str(uuid.uuid4())
        
        try:
            # Mark as connecting
            server.connection_error = None
            await self.db.commit()
            
            # Perform connection based on transport type
            if server.transport_type == TransportType.SSE.value:
                result = await self._connect_sse(server)
            elif server.transport_type == TransportType.STDIO.value:
                result = await self._connect_stdio(server)
            elif server.transport_type == TransportType.HTTP_STREAM.value:
                result = await self._connect_http(server)
            else:
                raise ValueError(f"Unknown transport type: {server.transport_type}")
            
            # Update server status
            server.is_connected = True
            server.last_connected_at = datetime.utcnow()
            server.connection_error = None
            await self.db.commit()
            
            # Store connection
            self._connections[server_id] = {
                "id": connection_id,
                "server_id": server_id,
                "status": ConnectionStatus.CONNECTED.value,
                "connected_at": datetime.utcnow(),
                "session_id": result.get("session_id"),
            }
            
            # Discover tools
            await self._discover_tools(server)
            
            return {
                "connection_id": connection_id,
                "session_id": result.get("session_id"),
                "status": ConnectionStatus.CONNECTED.value,
            }
            
        except Exception as e:
            server.is_connected = False
            server.connection_error = str(e)
            await self.db.commit()
            
            raise
    
    async def disconnect_server(self, server_id: str) -> bool:
        """Disconnect from an MCP server."""
        server = await self.get_server(server_id)
        if not server:
            return False
        
        # Close process if stdio
        if server_id in self._processes:
            proc = self._processes.pop(server_id)
            proc.terminate()
            try:
                await proc.wait(timeout=5)
            except asyncio.TimeoutError:
                proc.kill()
        
        # Update server
        server.is_connected = False
        await self.db.commit()
        
        # Remove connection
        self._connections.pop(server_id, None)
        
        return True
    
    async def test_connection(self, server_id: str) -> dict:
        """Test server connection."""
        server = await self.get_server(server_id)
        if not server:
            raise ValueError(f"Server not found: {server_id}")
        
        try:
            # Try to connect briefly
            result = await self.connect_server(server_id)
            
            # Disconnect immediately after test
            await self.disconnect_server(server_id)
            
            return {
                "success": True,
                "message": "Connection successful",
                "server_id": server_id,
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "server_id": server_id,
            }
    
    async def _connect_sse(self, server: MCPServer) -> dict:
        """Connect via SSE."""
        # In production, this would establish SSE connection
        session_id = str(uuid.uuid4())
        
        # Simulate connection
        await asyncio.sleep(0.5)
        
        return {"session_id": session_id}
    
    async def _connect_stdio(self, server: MCPServer) -> dict:
        """Connect via stdio."""
        if not server.stdio_command:
            raise ValueError("Stdio command not configured")
        
        # Start the process
        proc = await asyncio.create_subprocess_exec(
            server.stdio_command,
            *(server.stdio_args or []),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**({"PATH": "/usr/local/bin:/usr/bin:/bin"}), **(server.stdio_env or {})},
        )
        
        self._processes[server.id] = proc
        session_id = str(uuid.uuid4())
        
        return {"session_id": session_id}
    
    async def _connect_http(self, server: MCPServer) -> dict:
        """Connect via HTTP stream."""
        # In production, this would establish HTTP connection
        session_id = str(uuid.uuid4())
        
        # Simulate connection
        await asyncio.sleep(0.3)
        
        return {"session_id": session_id}
    
    # ============== Tool Management ==============
    
    async def _discover_tools(self, server: MCPServer) -> list[MCPTool]:
        """Discover tools from a connected server."""
        # In production, this would call the server's tools/list method
        # For now, we simulate discovery
        
        discovered_tools = []
        
        # Simulate tool discovery
        sample_tools = [
            {"name": "search", "description": "Search for information", "category": "search"},
            {"name": "calculate", "description": "Perform calculations", "category": "utilities"},
        ]
        
        for tool_data in sample_tools:
            tool = await self.create_tool(
                server_id=server.id,
                name=tool_data["name"],
                description=tool_data["description"],
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                category=tool_data.get("category"),
            )
            tool.is_discovered = True
            tool.discovered_at = datetime.utcnow()
            await self.db.commit()
            discovered_tools.append(tool)
        
        return discovered_tools
    
    async def create_tool(
        self,
        server_id: str,
        name: str,
        input_schema: dict,
        description: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[list] = None,
    ) -> MCPTool:
        """Create a tool definition."""
        tool_id = str(uuid.uuid4())
        
        tool = MCPTool(
            id=tool_id,
            server_id=server_id,
            name=name,
            description=description,
            input_schema=input_schema,
            category=category,
            tags=tags,
        )
        
        self.db.add(tool)
        await self.db.commit()
        await self.db.refresh(tool)
        
        return tool
    
    async def get_tool(self, tool_id: str) -> Optional[MCPTool]:
        """Get tool by ID."""
        result = await self.db.execute(
            select(MCPTool).where(MCPTool.id == tool_id)
        )
        return result.scalar_one_or_none()
    
    async def list_server_tools(
        self,
        server_id: str,
    ) -> list[MCPTool]:
        """List all tools for a server."""
        query = select(MCPTool).where(MCPTool.server_id == server_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def call_tool(
        self,
        tool_id: str,
        parameters: dict,
    ) -> ToolCallResult:
        """Call a tool on a connected server."""
        import time
        
        tool = await self.get_tool(tool_id)
        if not tool:
            raise ValueError(f"Tool not found: {tool_id}")
        
        server = await self.get_server(tool.server_id)
        if not server or not server.is_connected:
            raise ValueError("Server is not connected")
        
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Log the call
            log = MCPLog(
                id=str(uuid.uuid4()),
                server_id=server.id,
                tool_id=tool.id,
                user_id=self.user_id,
                request_id=request_id,
                method="tools/call",
                request_body={"name": tool.name, "arguments": parameters},
            )
            self.db.add(log)
            
            # In production, this would send the actual request
            # For now, simulate the call
            await asyncio.sleep(0.2)
            
            result = {"result": "simulated_result"}
            
            # Update log
            log.response_body = result
            log.success = True
            log.status_code = 200
            log.latency_ms = int((time.time() - start_time) * 1000)
            
            # Update tool stats
            tool.total_calls += 1
            tool.success_count += 1
            
            await self.db.commit()
            
            return ToolCallResult(
                success=True,
                result=result,
                error=None,
                execution_time_ms=log.latency_ms,
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            
            # Update log
            log.error_message = str(e)
            log.success = False
            log.status_code = 500
            log.latency_ms = execution_time
            
            # Update tool stats
            tool.total_calls += 1
            tool.failure_count += 1
            
            await self.db.commit()
            
            return ToolCallResult(
                success=False,
                result=None,
                error=str(e),
                execution_time_ms=execution_time,
            )
    
    # ============== Logging ==============
    
    async def get_logs(
        self,
        server_id: Optional[str] = None,
        tool_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[MCPLog], int]:
        """Get MCP call logs."""
        query = select(MCPLog).where(MCPLog.user_id == self.user_id)
        count_query = select(func.count(MCPLog.id)).where(MCPLog.user_id == self.user_id)
        
        if server_id:
            query = query.where(MCPLog.server_id == server_id)
            count_query = count_query.where(MCPLog.server_id == server_id)
        
        if tool_id:
            query = query.where(MCPLog.tool_id == tool_id)
            count_query = count_query.where(MCPLog.tool_id == tool_id)
        
        total = (await self.db.execute(count_query)).scalar()
        
        query = query.order_by(MCPLog.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return list(logs), total
    
    # ============== Connection State ==============
    
    async def get_connection_status(self, server_id: str) -> Optional[dict]:
        """Get connection status for a server."""
        server = await self.get_server(server_id)
        if not server:
            return None
        
        connection = self._connections.get(server_id, {})
        
        return {
            "server_id": server_id,
            "is_connected": server.is_connected,
            "last_connected_at": server.last_connected_at.isoformat() if server.last_connected_at else None,
            "connection_error": server.connection_error,
            "session_id": connection.get("session_id"),
        }
