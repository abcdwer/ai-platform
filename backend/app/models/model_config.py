"""Model configuration model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ModelConfig(Base):
    """Model configuration for different providers."""
    
    __tablename__ = "model_configs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # ollama, openai, anthropic, etc.
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)  # Model identifier (e.g., llama2, gpt-4)
    
    # API Configuration
    api_base: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Custom API base URL
    api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Encrypted in production
    
    # Model Capabilities
    supports_streaming: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_function_calling: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_vision: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Default Parameters
    default_temperature: Mapped[float] = mapped_column(Float, default=0.7)
    default_max_tokens: Mapped[int] = mapped_column(default=4096)
    default_top_p: Mapped[float] = mapped_column(Float, default=0.9)
    
    # Context Limits
    max_context_tokens: Mapped[int] = mapped_column(default=4096)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<ModelConfig(id={self.id}, name={self.name}, provider={self.provider})>"
    
    @property
    def display_name(self) -> str:
        """Get display name for the model."""
        return f"{self.provider.title()}/{self.model_id}"
