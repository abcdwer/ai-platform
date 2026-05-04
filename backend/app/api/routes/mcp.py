"""MCP (Model Context Protocol) API routes."""
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.mcp_service import MCPService

router = APIRouter(prefix="/api/mcp", tags=["MCP"])


async def get_user_id() -> str:
    return "default-user"


# ============== Server Routes ==============

@router.post("/servers")
async def create_server(
    name: str = Form(...),
    transport_type: str = Form(...),
    description: Optional[str] = Form(default=None),
    sse_url: Optional[str] = Form(default=None),
    sse_endpoint: Optional[str] = Form(default="/sse"),
    stdio_command: Optional[str] = Form(default=None),
    stdio_args: Optional[str] = Form(default=None),  # JSON string
    stdio_env: Optional[str] = Form(default=None),  # JSON string
    http_url: Optional[str] = Form(default=None),
    http_headers: Optional[str] = Form(default=None),  # JSON string
    auth_type: Optional[str] = Form(default=None),
    auth_config: Optional[str] = Form(default=None),  # JSON string
    timeout: int = Form(default=30),
    max_retries: int = Form(default=3),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Create a new MCP server."""
    try:
        # Parse JSON fields
        stdio_args_parsed = json.loads(stdio_args) if stdio_args else None
        stdio_env_parsed = json.loads(stdio_env) if stdio_env else None
        http_headers_parsed = json.loads(http_headers) if http_headers else None
        auth_config_parsed = json.loads(auth_config) if auth_config else None
        
        service = MCPService(db, user_id)
        server = await service.create_server(
            name=name,
            transport_type=transport_type,
            description=description,
            sse_url=sse_url,
            sse_endpoint=sse_endpoint,
            stdio_command=stdio_command,
            stdio_args=stdio_args_parsed,
            stdio_env=stdio_env_parsed,
            http_url=http_url,
            http_headers=http_headers_parsed,
            auth_type=auth_type,
            auth_config=auth_config_parsed,
            timeout=timeout,
            max_retries=max_retries,
        )
        
        return {
            "id": server.id,
            "name": server.name,
            "transport_type": server.transport_type,
            "is_connected": server.is_connected,
            "created_at": server.created_at.isoformat(),
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers")
async def list_servers(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """List all MCP servers."""
    service = MCPService(db, user_id)
    servers, total = await service.list_servers(skip, limit)
    
    return {
        "items": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "transport_type": s.transport_type,
                "is_connected": s.is_connected,
                "last_connected_at": s.last_connected_at.isoformat() if s.last_connected_at else None,
                "created_at": s.created_at.isoformat(),
            }
            for s in servers
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/servers/{server_id}")
async def get_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Get server details."""
    service = MCPService(db, user_id)
    server = await service.get_server(server_id)
    
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Get connection status
    connection_status = await service.get_connection_status(server_id)
    
    return {
        "id": server.id,
        "name": server.name,
        "description": server.description,
        "transport_type": server.transport_type,
        "sse_url": server.sse_url,
        "sse_endpoint": server.sse_endpoint,
        "stdio_command": server.stdio_command,
        "stdio_args": server.stdio_args,
        "http_url": server.http_url,
        "auth_type": server.auth_type,
        "timeout": server.timeout,
        "max_retries": server.max_retries,
        "is_connected": server.is_connected,
        "last_connected_at": server.last_connected_at.isoformat() if server.last_connected_at else None,
        "connection_error": server.connection_error,
        "connection": connection_status,
        "created_at": server.created_at.isoformat(),
        "updated_at": server.updated_at.isoformat(),
    }


@router.patch("/servers/{server_id}")
async def update_server(
    server_id: str,
    name: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    sse_url: Optional[str] = Form(default=None),
    sse_endpoint: Optional[str] = Form(default=None),
    stdio_command: Optional[str] = Form(default=None),
    stdio_args: Optional[str] = Form(default=None),
    http_url: Optional[str] = Form(default=None),
    http_headers: Optional[str] = Form(default=None),
    timeout: Optional[int] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Update server configuration."""
    try:
        service = MCPService(db, user_id)
        
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if sse_url is not None:
            updates["sse_url"] = sse_url
        if sse_endpoint is not None:
            updates["sse_endpoint"] = sse_endpoint
        if stdio_command is not None:
            updates["stdio_command"] = stdio_command
        if stdio_args is not None:
            updates["stdio_args"] = json.loads(stdio_args)
        if http_url is not None:
            updates["http_url"] = http_url
        if http_headers is not None:
            updates["http_headers"] = json.loads(http_headers)
        if timeout is not None:
            updates["timeout"] = timeout
        
        server = await service.update_server(server_id, **updates)
        
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")
        
        return {"id": server.id, "updated": True}
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")


@router.delete("/servers/{server_id}")
async def delete_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Delete a server."""
    service = MCPService(db, user_id)
    deleted = await service.delete_server(server_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Server not found")
    
    return {"status": "deleted"}


# ============== Connection Routes ==============

@router.post("/servers/{server_id}/connect")
async def connect_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Connect to a server."""
    try:
        service = MCPService(db, user_id)
        result = await service.connect_server(server_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/servers/{server_id}/disconnect")
async def disconnect_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Disconnect from a server."""
    service = MCPService(db, user_id)
    result = await service.disconnect_server(server_id)
    
    return {"disconnected": result}


@router.post("/servers/{server_id}/test")
async def test_connection(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Test server connection."""
    service = MCPService(db, user_id)
    result = await service.test_connection(server_id)
    return result


# ============== Tool Routes ==============

@router.get("/servers/{server_id}/tools")
async def list_server_tools(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """List tools for a server."""
    service = MCPService(db, user_id)
    
    # Verify server exists
    server = await service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    tools = await service.list_server_tools(server_id)
    
    return {
        "items": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
                "category": t.category,
                "tags": t.tags,
                "is_discovered": t.is_discovered,
                "total_calls": t.total_calls,
                "success_rate": t.get_success_rate(),
                "avg_execution_time_ms": t.avg_execution_time,
                "created_at": t.created_at.isoformat(),
            }
            for t in tools
        ],
        "total": len(tools),
    }


@router.get("/tools/{tool_id}")
async def get_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Get tool details."""
    service = MCPService(db, user_id)
    tool = await service.get_tool(tool_id)
    
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return {
        "id": tool.id,
        "server_id": tool.server_id,
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.input_schema,
        "category": tool.category,
        "tags": tool.tags,
        "is_discovered": tool.is_discovered,
        "total_calls": tool.total_calls,
        "success_count": tool.success_count,
        "failure_count": tool.failure_count,
        "success_rate": tool.get_success_rate(),
        "avg_execution_time_ms": tool.avg_execution_time,
        "discovered_at": tool.discovered_at.isoformat() if tool.discovered_at else None,
        "created_at": tool.created_at.isoformat(),
    }


@router.post("/tools/{tool_id}/call")
async def call_tool(
    tool_id: str,
    parameters: str = Form(default="{}"),  # JSON string
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Call a tool."""
    try:
        params = json.loads(parameters) if parameters else {}
        
        service = MCPService(db, user_id)
        result = await service.call_tool(tool_id, params)
        
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "execution_time_ms": result.execution_time_ms,
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters JSON: {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Log Routes ==============

@router.get("/logs")
async def get_logs(
    server_id: Optional[str] = Query(default=None),
    tool_id: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """Get MCP call logs."""
    service = MCPService(db, user_id)
    logs, total = await service.get_logs(server_id, tool_id, skip, limit)
    
    return {
        "items": [
            {
                "id": log.id,
                "server_id": log.server_id,
                "tool_id": log.tool_id,
                "request_id": log.request_id,
                "method": log.method,
                "status_code": log.status_code,
                "success": log.success,
                "latency_ms": log.latency_ms,
                "error_message": log.error_message,
                "conversation_id": log.conversation_id,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }
