"""RAG service for knowledge base queries."""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.knowledge import KnowledgeBase
from app.rag.retriever import Retriever


class RAGService:
    """Service for Retrieval-Augmented Generation operations."""
    
    def __init__(self):
        self.retriever = Retriever()
    
    async def query(
        self,
        knowledge_base_id: str,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Query a knowledge base with a question.
        
        Args:
            knowledge_base_id: ID of the knowledge base to query
            query: The query text
            top_k: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of relevant document chunks with scores
        """
        if not knowledge_base_id:
            return []
        
        try:
            results = await self.retriever.retrieve(
                knowledge_base_id=knowledge_base_id,
                query=query,
                top_k=top_k,
                threshold=similarity_threshold
            )
            return results
        except Exception as e:
            # Return empty results on error
            return []
    
    async def add_document(
        self,
        knowledge_base_id: str,
        document_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a document to a knowledge base.
        
        Args:
            knowledge_base_id: ID of the knowledge base
            document_id: ID of the document
            text: Document text
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            from app.services.embedding_service import EmbeddingService
            from app.rag.chunker import TextChunker
            
            # Chunk the text
            chunker = TextChunker()
            chunks = chunker.chunk(text)
            
            # Generate embeddings
            embedding_service = EmbeddingService()
            embeddings = await embedding_service.embed_batch(chunks)
            
            # Store in vector database
            await self.retriever.store(
                knowledge_base_id=knowledge_base_id,
                document_id=document_id,
                chunks=chunks,
                embeddings=embeddings,
                metadata=metadata
            )
            
            return True
        except Exception as e:
            return False
