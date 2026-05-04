"""MCP (Model Context Protocol) models."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Boolean, Text, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class MCPServer(Base):
    """MCP Server configuration."""
    
    __tablename__ = "mcp_servers"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Server identity
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Connection type
    transport_type: Mapped[str] = mapped_column(String(20), nullable=False, default="sse")  # sse, stdio, http_stream
    
    # SSE configuration
    sse_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    sse_endpoint: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Stdio configuration
    stdio_command: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    stdio_args: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    stdio_env: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # HTTP Stream configuration
    http_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    http_headers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Authentication
    auth_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # none, bearer, api_key
    auth_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Connection state
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    last_connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    connection_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Settings
    timeout: Mapped[int] = mapped_column(Integer, default=30)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="mcp_servers")
    tools: Mapped[list["MCPTool"]] = relationship("MCPTool", back_populates="server", cascade="all, delete-orphan")
    logs: Mapped[list["MCPLog"]] = relationship("MCPLog", back_populates="server", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<MCPServer(id={self.id}, name={self.name}, connected={self.is_connected})>"


class MCPTool(Base):
    """MCP Tool definition."""
    
    __tablename__ = "mcp_tools"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    server_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Tool identity
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Tool schema (JSON Schema for input parameters)
    input_schema: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Metadata
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Usage statistics
    total_calls: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_execution_time: Mapped[float] = mapped_column(Integer, default=0)  # milliseconds
    
    # Discovery info
    is_discovered: Mapped[bool] = mapped_column(Boolean, default=False)
    discovered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    server: Mapped["MCPServer"] = relationship("MCPServer", back_populates="tools")
    logs: Mapped[list["MCPLog"]] = relationship("MCPLog", back_populates="tool", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<MCPTool(id={self.id}, name={self.name})>"
    
    def get_success_rate(self) -> float:
        """Get success rate percentage."""
        if self.total_calls == 0:
            return 0.0
        return (self.success_count / self.total_calls) * 100


class MCPConnection(Base):
    """MCP Connection state tracking (in-memory or cached)."""
    
    __tablename__ = "mcp_connections"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    server_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Connection state
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="disconnected")  # connected, disconnected, connecting, error
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Timestamps
    connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    disconnected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Statistics
    messages_sent: Mapped[int] = mapped_column(Integer, default=0)
    messages_received: Mapped[int] = mapped_column(Integer, default=0)
    tools_called: Mapped[int] = mapped_column(Integer, default=0)
    
    # Error tracking
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<MCPConnection(id={self.id}, server_id={self.server_id}, status={self.status})>"


class MCPLog(Base):
    """MCP API call logs."""
    
    __tablename__ = "mcp_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    server_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    tool_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Request info
    request_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(50), nullable=False)  # tools/call, tools/list, etc.
    
    # Request/Response
    request_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    request_body: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    response_body: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timing (milliseconds)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Error
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Context
    conversation_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    server: Mapped["MCPServer"] = relationship("MCPServer", back_populates="logs")
    tool: Mapped[Optional["MCPTool"]] = relationship("MCPTool", back_populates="logs")
    
    def __repr__(self) -> str:
        return f"<MCPLog(id={self.id}, method={self.method}, success={self.success})>"
