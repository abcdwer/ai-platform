"""Document data model."""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum

if TYPE_CHECKING:
    from app.models.knowledge import KnowledgeBase


class DocumentStatus(str, enum.Enum):
    """Document processing status."""
    UPLOADING = "uploading"
    PARSING = "parsing"
    EMBEDDING = "embedding"
    READY = "ready"
    ERROR = "error"


class ContentType(str, enum.Enum):
    """Document content type."""
    PDF = "pdf"
    WORD = "docx"
    TEXT = "txt"
    MARKDOWN = "md"
    CSV = "csv"
    HTML = "html"
    URL = "url"


class Document(Base):
    """Document model."""
    
    __tablename__ = "documents"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    knowledge_base_id: Mapped[str] = mapped_column(String(36), ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    
    # Document info
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, docx, txt, md, csv, html, url
    file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)  # Local file path for uploaded files
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # File size in bytes
    url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)  # Original URL for web content
    
    # Content (extracted text)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Processing status
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=DocumentStatus.UPLOADING.value)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Vectorization stats
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    knowledge_base: Mapped["KnowledgeBase"] = relationship("KnowledgeBase", back_populates="documents")
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title}, status={self.status})>"
