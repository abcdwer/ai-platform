"""Knowledge base Pydantic schemas."""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# Knowledge Base Schemas
class KnowledgeBaseBase(BaseModel):
    """Base knowledge base schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    embedding_model: str = Field(default="nomic-embed-text")
    embedding_provider: Literal["ollama", "openai"] = Field(default="ollama")
    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)
    chunking_strategy: Literal["paragraph", "fixed", "semantic"] = Field(default="paragraph")
    top_k: int = Field(default=5, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    tags: Optional[List[str]] = []


class KnowledgeBaseCreate(KnowledgeBaseBase):
    """Schema for creating a knowledge base."""
    pass


class KnowledgeBaseUpdate(BaseModel):
    """Schema for updating a knowledge base."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_provider: Optional[Literal["ollama", "openai"]] = None
    chunk_size: Optional[int] = Field(None, ge=100, le=2000)
    chunk_overlap: Optional[int] = Field(None, ge=0, le=500)
    chunking_strategy: Optional[Literal["paragraph", "fixed", "semantic"]] = None
    top_k: Optional[int] = Field(None, ge=1, le=50)
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class KnowledgeBaseResponse(KnowledgeBaseBase):
    """Schema for knowledge base response."""
    id: str
    document_count: int
    vector_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class KnowledgeBaseListResponse(BaseModel):
    """Schema for paginated knowledge base list."""
    items: List[KnowledgeBaseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Document Schemas
class DocumentBase(BaseModel):
    """Base document schema."""
    title: str = Field(..., min_length=1, max_length=500)


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    id: str
    knowledge_base_id: str
    content_type: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    url: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    chunk_count: int
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for document list."""
    items: List[DocumentResponse]
    total: int


class URLAddRequest(BaseModel):
    """Schema for adding document via URL."""
    url: str = Field(..., min_length=1)
    title: Optional[str] = Field(None, max_length=500)


# Search Schemas
class SearchRequest(BaseModel):
    """Schema for knowledge base search."""
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(None, ge=1, le=50)
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)


class SearchResult(BaseModel):
    """Schema for a single search result."""
    content: str
    document_id: str
    document_title: str
    chunk_index: int
    score: float
    metadata: Optional[dict] = None


class SearchResponse(BaseModel):
    """Schema for search response."""
    results: List[SearchResult]
    query: str
    total: int


# RAG Chat Schemas
class RAGChatRequest(BaseModel):
    """Schema for RAG chat request."""
    message: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(None, ge=1, le=50)
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    include_sources: bool = Field(default=True)


class RAGSource(BaseModel):
    """Schema for RAG source/citation."""
    content: str
    document_id: str
    document_title: str
    chunk_index: int
    score: float


class RAGChatResponse(BaseModel):
    """Schema for RAG chat response."""
    message: str
    sources: List[RAGSource]
    conversation_id: Optional[str] = None
