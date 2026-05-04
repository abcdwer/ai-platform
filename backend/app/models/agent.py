"""Agent model."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    pass  # Forward reference handled at runtime


class Agent(Base):
    """Agent model for custom AI agents with tools."""
    
    __tablename__ = "agents"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="You are a helpful AI assistant.")
    model: Mapped[str] = mapped_column(String(100), nullable=False, default="llama2")
    model_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="ollama")
    
    # Tools configuration (JSON array of tool definitions)
    tools: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    
    # Agent settings
    temperature: Mapped[float] = mapped_column(default=0.7)
    max_tokens: Mapped[int] = mapped_column(default=4096)
    top_p: Mapped[Optional[float]] = mapped_column(default=0.9)
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name})>"
    
    def get_available_tools(self) -> list[dict]:
        """Get list of available tools for this agent."""
        return self.tools or []
