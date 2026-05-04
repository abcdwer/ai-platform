"""Multi-Agent collaboration schemas."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# ============== Agent Group Schemas ==============

class AgentMemberBase(BaseModel):
    """Base schema for agent member."""
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="member", description="Member role: leader, member, supporter, opponent, judge")
    system_prompt: str = Field(default="You are a helpful AI assistant.")
    execution_order: int = Field(default=0, ge=0)
    model: Optional[str] = Field(None, description="Override group default model")
    model_provider: Optional[str] = Field(None, description="Override group default provider")
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=1, le=32768)
    tools: Optional[list] = Field(default_factory=list)
    icon: Optional[str] = Field(None, description="Icon name for UI")
    color: Optional[str] = Field(None, description="Color for UI visualization")


class AgentMemberCreate(AgentMemberBase):
    """Schema for creating an agent member."""
    pass


class AgentMemberUpdate(BaseModel):
    """Schema for updating an agent member."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = None
    system_prompt: Optional[str] = None
    execution_order: Optional[int] = Field(None, ge=0)
    model: Optional[str] = None
    model_provider: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=32768)
    tools: Optional[list] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


class AgentMemberResponse(AgentMemberBase):
    """Schema for agent member response."""
    id: str
    group_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AgentGroupBase(BaseModel):
    """Base schema for agent group."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    mode: str = Field(default="sequential", description="Collaboration mode")
    mode_config: Optional[dict] = Field(default_factory=dict)
    default_model: str = Field(default="llama2")
    default_provider: str = Field(default="ollama")
    enable_orchestrator: bool = Field(default=True)
    orchestrator_prompt: Optional[str] = None
    max_iterations: int = Field(default=10, ge=1, le=100)
    termination_prompt: Optional[str] = None


class AgentGroupCreate(AgentGroupBase):
    """Schema for creating an agent group."""
    members: Optional[list[AgentMemberCreate]] = Field(default_factory=list)


class AgentGroupUpdate(BaseModel):
    """Schema for updating an agent group."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    mode: Optional[str] = None
    mode_config: Optional[dict] = None
    default_model: Optional[str] = None
    default_provider: Optional[str] = None
    enable_orchestrator: Optional[bool] = None
    orchestrator_prompt: Optional[str] = None
    max_iterations: Optional[int] = Field(None, ge=1, le=100)
    termination_prompt: Optional[str] = None
    is_active: Optional[bool] = None


class AgentGroupResponse(AgentGroupBase):
    """Schema for agent group response."""
    id: str
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    members: Optional[list[AgentMemberResponse]] = None
    
    class Config:
        from_attributes = True


class AgentGroupListResponse(BaseModel):
    """Schema for paginated agent group list response."""
    items: list[AgentGroupResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============== Session Schemas ==============

class SessionStart(BaseModel):
    """Schema for starting a collaboration session."""
    initial_input: str = Field(..., min_length=1)
    context: Optional[dict] = Field(default_factory=dict)


class SessionUpdate(BaseModel):
    """Schema for updating a session."""
    status: Optional[str] = None
    context: Optional[dict] = None
    final_output: Optional[str] = None
    summary: Optional[str] = None


class AgentMessageBase(BaseModel):
    """Base schema for agent message."""
    message_type: str = Field(default="agent_output")
    content: str
    referenced_message_id: Optional[str] = None
    tool_calls: Optional[list] = None
    tool_results: Optional[list] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    execution_time_ms: Optional[int] = None
    turn: int = Field(default=0)
    iteration: int = Field(default=0)


class AgentMessageCreate(AgentMessageBase):
    """Schema for creating an agent message."""
    member_id: Optional[str] = None


class AgentMessageResponse(AgentMessageBase):
    """Schema for agent message response."""
    id: str
    session_id: str
    member_id: Optional[str] = None
    member_name: Optional[str] = None
    member_color: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """Schema for collaboration session response."""
    id: str
    group_id: str
    user_id: str
    status: str
    initial_input: str
    context: Optional[dict] = None
    final_output: Optional[str] = None
    summary: Optional[str] = None
    current_turn: int
    completed_iterations: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    messages: Optional[list[AgentMessageResponse]] = None
    
    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Schema for paginated session list response."""
    items: list[SessionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============== Execution Schemas ==============

class SessionExecuteRequest(BaseModel):
    """Schema for executing a collaboration session."""
    user_input: Optional[str] = Field(None, description="Additional user input")
    continue_session: bool = Field(default=True, description="Continue existing session or create new")


class SessionExecuteResponse(BaseModel):
    """Schema for session execution response."""
    session_id: str
    status: str
    current_turn: int
    messages: list[AgentMessageResponse]
    final_output: Optional[str] = None
    is_complete: bool = False


# ============== Mode Configuration Schemas ==============

class SequentialModeConfig(BaseModel):
    """Configuration for sequential mode."""
    stop_on_first_success: bool = Field(default=False)


class ParallelModeConfig(BaseModel):
    """Configuration for parallel mode."""
    max_parallel: int = Field(default=3)
    aggregation_method: str = Field(default="merge", description="merge, vote, or first")


class DebateModeConfig(BaseModel):
    """Configuration for debate mode."""
    rounds: int = Field(default=3, ge=1, le=10)
    allow_rebuttal: bool = Field(default=True)
    judge_model: Optional[str] = Field(None, description="Model for judge agent")


class HierarchicalModeConfig(BaseModel):
    """Configuration for hierarchical mode."""
    max_depth: int = Field(default=3, ge=1, le=5)
    delegate_threshold: float = Field(default=0.5, description="Confidence threshold to delegate")


class RoundRobinModeConfig(BaseModel):
    """Configuration for round robin mode."""
    max_turns: int = Field(default=10, ge=1, le=50)
    allow_skip: bool = Field(default=True)
