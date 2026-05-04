"""Knowledge base service with user data isolation."""
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.knowledge import KnowledgeBase
from app.models.document import Document
from app.models.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
)
from app.rag import init_chroma_collection


class KnowledgeService:
    """Service for knowledge base operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize knowledge service."""
        self.db = db
    
    async def create_knowledge_base(
        self,
        data: KnowledgeBaseCreate,
        user_id: str
    ) -> KnowledgeBase:
        """Create a new knowledge base."""
        kb = KnowledgeBase(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=data.name,
            description=data.description,
            embedding_model=data.embedding_model,
            embedding_provider=data.embedding_provider,
            chunk_size=data.chunk_size,
            chunk_overlap=data.chunk_overlap,
            chunking_strategy=data.chunking_strategy,
            top_k=data.top_k,
            similarity_threshold=data.similarity_threshold,
            tags=data.tags or [],
        )
        
        self.db.add(kb)
        await self.db.commit()
        await self.db.refresh(kb)
        
        # Create ChromaDB collection
        try:
            init_chroma_collection(kb.id)
        except Exception as e:
            logger.warning(f"Failed to create ChromaDB collection: {e}")
        
        logger.info(f"Created knowledge base: {kb.id} for user: {user_id}")
        return kb
    
    async def get_knowledge_base(
        self,
        kb_id: str,
        user_id: Optional[str] = None
    ) -> Optional[KnowledgeBase]:
        """Get knowledge base by ID with optional user check."""
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = result.scalar_one_or_none()
        
        # Check user ownership if user_id provided
        if kb and user_id and kb.user_id != user_id:
            return None
        
        return kb
    
    async def list_knowledge_bases(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """List knowledge bases for a specific user with pagination."""
        query = select(KnowledgeBase).where(
            KnowledgeBase.is_active == True,
            KnowledgeBase.user_id == user_id
        )
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                KnowledgeBase.name.ilike(search_pattern) |
                KnowledgeBase.description.ilike(search_pattern)
            )
        
        if tags:
            # Filter by tags (JSON array contains)
            for tag in tags:
                query = query.where(KnowledgeBase.tags.contains([tag]))
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(KnowledgeBase.updated_at.desc())
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return {
            "items": list(items),
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    
    async def update_knowledge_base(
        self,
        kb_id: str,
        user_id: str,
        data: KnowledgeBaseUpdate
    ) -> Optional[KnowledgeBase]:
        """Update knowledge base with user ownership check."""
        kb = await self.get_knowledge_base(kb_id, user_id)
        if not kb:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(kb, key, value)
        
        await self.db.commit()
        await self.db.refresh(kb)
        
        logger.info(f"Updated knowledge base: {kb_id}")
        return kb
    
    async def delete_knowledge_base(
        self,
        kb_id: str,
        user_id: str
    ) -> bool:
        """Delete knowledge base with user ownership check."""
        kb = await self.get_knowledge_base(kb_id, user_id)
        if not kb:
            return False
        
        # Delete ChromaDB collection
        try:
            from app.rag import get_chroma_client
            client = get_chroma_client()
            client.delete_collection(f"kb_{kb_id}")
        except Exception as e:
            logger.warning(f"Failed to delete ChromaDB collection: {e}")
        
        # Delete from database (cascades to documents)
        await self.db.delete(kb)
        await self.db.commit()
        
        logger.info(f"Deleted knowledge base: {kb_id}")
        return True
    
    async def update_stats(
        self,
        kb_id: str,
        document_count: Optional[int] = None,
        vector_count: Optional[int] = None
    ):
        """Update knowledge base statistics."""
        kb = await self.get_knowledge_base(kb_id)
        if kb:
            if document_count is not None:
                kb.document_count = document_count
            if vector_count is not None:
                kb.vector_count = vector_count
            await self.db.commit()
    
    async def increment_document_count(self, kb_id: str, delta: int = 1):
        """Increment document count."""
        kb = await self.get_knowledge_base(kb_id)
        if kb:
            kb.document_count += delta
            await self.db.commit()
    
    async def increment_vector_count(self, kb_id: str, delta: int = 1):
        """Increment vector count."""
        kb = await self.get_knowledge_base(kb_id)
        if kb:
            kb.vector_count += delta
            await self.db.commit()
