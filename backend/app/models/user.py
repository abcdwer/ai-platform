"""User model."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import String, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.agent import Agent
    from app.models.workflow import Workflow
    from app.models.knowledge import KnowledgeBase
    from app.models.multi_agent import AgentGroup
    from app.models.finetune import FineTuneJob
    from app.models.mcp import MCPServer


class User(Base):
    """User model for authentication and data isolation."""
    
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # User preferences (stored as JSON string for simplicity)
    preferences: Mapped[Optional[dict]] = mapped_column(default=None)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships - cascade delete ensures data isolation
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    agents: Mapped[List["Agent"]] = relationship(
        "Agent", back_populates="user", cascade="all, delete-orphan"
    )
    knowledge_bases: Mapped[List["KnowledgeBase"]] = relationship(
        "KnowledgeBase", back_populates="user", cascade="all, delete-orphan"
    )
    workflows: Mapped[List["Workflow"]] = relationship(
        "Workflow", back_populates="user", cascade="all, delete-orphan"
    )
    agent_groups: Mapped[List["AgentGroup"]] = relationship(
        "AgentGroup", back_populates="user", cascade="all, delete-orphan"
    )
    finetune_jobs: Mapped[List["FineTuneJob"]] = relationship(
        "FineTuneJob", back_populates="user", cascade="all, delete-orphan"
    )
    mcp_servers: Mapped[List["MCPServer"]] = relationship(
        "MCPServer", back_populates="user", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"
    
    @property
    def display_name(self) -> str:
        """Get display name for the user."""
        return self.full_name or self.username
