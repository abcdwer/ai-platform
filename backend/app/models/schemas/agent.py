"""Agent schemas."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Tool definition schema."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: dict = Field(default_factory=dict, description="JSON Schema for tool parameters")


class AgentBase(BaseModel):
    """Base agent schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    system_prompt: str = Field(default="You are a helpful AI assistant.")
    model: str = Field(default="llama2")
    model_provider: str = Field(default="ollama")
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=1, le=32768)
    top_p: Optional[float] = Field(default=0.9, ge=0, le=1)


class AgentCreate(AgentBase):
    """Schema for creating an agent."""
    tools: Optional[list[ToolDefinition]] = Field(default_factory=list)
    is_public: bool = Field(default=False)


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    model_provider: Optional[str] = None
    tools: Optional[list[ToolDefinition]] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=32768)
    top_p: Optional[float] = Field(None, ge=0, le=1)
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class AgentResponse(AgentBase):
    """Schema for agent response."""
    id: str
    user_id: str
    tools: Optional[list] = None
    is_active: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """Schema for paginated agent list response."""
    items: list[AgentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
