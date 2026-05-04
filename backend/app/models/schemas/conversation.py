"""Conversation and Chat schemas."""
from datetime import datetime
from typing import Optional, Any, Literal
from pydantic import BaseModel, Field


# Conversation Schemas
class ConversationBase(BaseModel):
    """Base conversation schema."""
    title: str = Field(default="New Conversation", max_length=255)
    agent_id: Optional[str] = None
    model: str = Field(default="llama2")
    model_provider: str = Field(default="ollama")


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""
    pass


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = Field(None, max_length=255)
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None


class MessageBase(BaseModel):
    """Base message schema."""
    role: str
    content: str


class ConversationResponse(ConversationBase):
    """Schema for conversation response."""
    id: str
    user_id: str
    is_pinned: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    messages: list["MessageResponse"] = []
    
    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Schema for paginated conversation list response."""
    items: list[ConversationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Message Schemas
class MessageResponse(MessageBase):
    """Schema for message response."""
    id: str
    conversation_id: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[dict] = None
    tokens_used: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Chat Request/Response Schemas
class ChatMessage(BaseModel):
    """Chat message schema for request."""
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    name: Optional[str] = None
    tool_calls: Optional[list[dict]] = None
    tool_call_id: Optional[str] = None


class ToolCall(BaseModel):
    """Tool call schema."""
    id: str = Field(..., description="Tool call ID")
    type: str = Field(default="function", description="Tool call type")
    function: dict = Field(..., description="Function details")


class ToolResult(BaseModel):
    """Tool execution result."""
    tool_call_id: str
    content: str
    is_error: bool = False


class ChatRequest(BaseModel):
    """Schema for chat request."""
    conversation_id: Optional[str] = None
    messages: list[ChatMessage] = Field(..., min_length=1)
    model: Optional[str] = None
    model_provider: Optional[str] = None
    agent_id: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=32768)
    stream: bool = Field(default=True)
    tools: Optional[list[dict]] = None  # Override agent's tools if provided


class ChatStreamResponse(BaseModel):
    """Schema for streaming chat response."""
    type: Literal["message", "tool_call", "done", "error"]
    content: Optional[str] = None
    tool_call: Optional[dict] = None
    tool_calls: Optional[list[dict]] = None
    usage: Optional[dict] = None
    error: Optional[str] = None


class ChatResponse(BaseModel):
    """Schema for non-streaming chat response."""
    message: MessageResponse
    conversation_id: str
    usage: Optional[dict] = None
