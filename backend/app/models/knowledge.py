"""Knowledge base data model."""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, DateTime, Integer, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    pass  # Forward references handled at runtime


class KnowledgeBase(Base):
    """Knowledge base model with user data isolation."""
    
    __tablename__ = "knowledge_bases"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Embedding configuration
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False, default="nomic-embed-text")
    embedding_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="ollama")  # ollama, openai
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    chunk_overlap: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    chunking_strategy: Mapped[str] = mapped_column(String(50), nullable=False, default="paragraph")  # paragraph, fixed, semantic
    
    # Retrieval configuration
    top_k: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    similarity_threshold: Mapped[float] = mapped_column(Integer, nullable=False, default=0.7)
    
    # Tags for organization
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True, default=list)
    
    # Statistics
    document_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vector_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="knowledge_base", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<KnowledgeBase(id={self.id}, name={self.name})>"
