"""Multi-Agent collaboration models."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class CollaborationMode(str, Enum):
    """Collaboration mode types."""
    SEQUENTIAL = "sequential"      # 按固定顺序执行
    PARALLEL = "parallel"          # 多Agent同时工作，结果汇总
    DEBATE = "debate"              # 正反方+裁判
    HIERARCHICAL = "hierarchical"  # 主管+下属执行
    ROUND_ROBIN = "round_robin"    # 循环轮流发言


class SessionStatus(str, Enum):
    """Collaboration session status."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MemberRole(str, Enum):
    """Agent member role in a group."""
    LEADER = "leader"              # 领导者/协调者
    MEMBER = "member"              # 普通成员
    SUPPORTER = "supporter"        # 支持者
    OPPONENT = "opponent"          # 反对方（辩论模式）
    JUDGE = "judge"                # 裁判（辩论模式）


class MessageType(str, Enum):
    """Message type in collaboration."""
    USER_INPUT = "user_input"      # 用户输入
    AGENT_OUTPUT = "agent_output"  # Agent输出
    SYSTEM_MESSAGE = "system"       # 系统消息
    AGENT_REFERENCE = "reference"  # 引用其他Agent的回复


class AgentGroup(Base):
    """Agent Group model for multi-agent collaboration."""
    
    __tablename__ = "agent_groups"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Collaboration mode configuration
    mode: Mapped[str] = mapped_column(
        String(50), 
        default=CollaborationMode.SEQUENTIAL.value
    )
    
    # Mode-specific configuration (JSON)
    # For hierarchical: {"max_depth": 3}
    # For debate: {"rounds": 3, "allow_rebuttal": true}
    # For round_robin: {"max_turns": 10}
    mode_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    
    # Default settings for all members
    default_model: Mapped[str] = mapped_column(String(100), default="llama2")
    default_provider: Mapped[str] = mapped_column(String(50), default="ollama")
    
    # Orchestrator settings
    enable_orchestrator: Mapped[bool] = mapped_column(Boolean, default=True)
    orchestrator_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Termination conditions
    max_iterations: Mapped[int] = mapped_column(Integer, default=10)
    termination_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="agent_groups")
    members: Mapped[list["AgentMember"]] = relationship(
        "AgentMember",
        back_populates="group",
        cascade="all, delete-orphan"
    )
    sessions: Mapped[list["CollaborationSession"]] = relationship(
        "CollaborationSession",
        back_populates="group",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<AgentGroup(id={self.id}, name={self.name}, mode={self.mode})>"


class AgentMember(Base):
    """Agent Member model for group members."""
    
    __tablename__ = "agent_members"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    group_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("agent_groups.id"), 
        nullable=False,
        index=True
    )
    
    # Member identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default=MemberRole.MEMBER.value)
    
    # System prompt for this member
    system_prompt: Mapped[str] = mapped_column(
        Text, 
        nullable=False, 
        default="You are a helpful AI assistant."
    )
    
    # Execution order (for sequential mode)
    execution_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Model settings (overrides group defaults if set)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    temperature: Mapped[float] = mapped_column(default=0.7)
    max_tokens: Mapped[int] = mapped_column(default=4096)
    
    # Tool permissions (JSON array of tool definitions)
    tools: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    
    # Icon/color for UI visualization
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Behavior settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    group: Mapped["AgentGroup"] = relationship("AgentGroup", back_populates="members")
    messages: Mapped[list["AgentMessage"]] = relationship(
        "AgentMessage",
        back_populates="member",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<AgentMember(id={self.id}, name={self.name}, role={self.role})>"
    
    def get_effective_model(self) -> str:
        """Get effective model (member setting or group default)."""
        return self.model or self.group.default_model if self.group else self.model
    
    def get_effective_provider(self) -> str:
        """Get effective provider (member setting or group default)."""
        return self.model_provider or self.group.default_provider if self.group else self.model_provider


class CollaborationSession(Base):
    """Collaboration Session model for tracking collaboration runs."""
    
    __tablename__ = "collaboration_sessions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    group_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("agent_groups.id"), 
        nullable=False,
        index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Session status
    status: Mapped[str] = mapped_column(
        String(20), 
        default=SessionStatus.CREATED.value
    )
    
    # User input that started this session
    initial_input: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Current context/state (JSON)
    context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    
    # Session outputs
    final_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Execution tracking
    current_turn: Mapped[int] = mapped_column(Integer, default=0)
    completed_iterations: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    group: Mapped["AgentGroup"] = relationship(
        "AgentGroup", 
        back_populates="sessions"
    )
    messages: Mapped[list["AgentMessage"]] = relationship(
        "AgentMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AgentMessage.created_at"
    )
    
    def __repr__(self) -> str:
        return f"<CollaborationSession(id={self.id}, group_id={self.group_id}, status={self.status})>"


class AgentMessage(Base):
    """Agent Message model for tracking messages in a session."""
    
    __tablename__ = "agent_messages"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("collaboration_sessions.id"), 
        nullable=False,
        index=True
    )
    member_id: Mapped[Optional[str]] = mapped_column(
        String(36), 
        ForeignKey("agent_members.id"), 
        nullable=True,
        index=True
    )
    
    # Message content
    message_type: Mapped[str] = mapped_column(
        String(50), 
        default=MessageType.AGENT_OUTPUT.value
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # References
    referenced_message_id: Mapped[Optional[str]] = mapped_column(
        String(36), 
        nullable=True
    )
    
    # For tool calls in the message
    tool_calls: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    tool_results: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Execution metadata
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Turn and iteration tracking
    turn: Mapped[int] = mapped_column(Integer, default=0)
    iteration: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session: Mapped["CollaborationSession"] = relationship(
        "CollaborationSession", 
        back_populates="messages"
    )
    member: Mapped[Optional["AgentMember"]] = relationship(
        "AgentMember", 
        back_populates="messages"
    )
    
    def __repr__(self) -> str:
        return f"<AgentMessage(id={self.id}, member_id={self.member_id}, type={self.message_type})>"
