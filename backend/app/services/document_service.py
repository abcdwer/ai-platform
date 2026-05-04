"""Document processing service."""
import uuid
import os
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
import httpx
from loguru import logger

from app.models.document import Document, DocumentStatus, ContentType
from app.models.knowledge import KnowledgeBase
from app.rag import parse_document, chunk_text, Retriever
from app.services.embedding_service import get_embedding_service


class DocumentService:
    """Service for document processing."""
    
    def __init__(self, db: Any = None):
        """Initialize document service."""
        self.db = db
    
    async def process_document(
        self,
        document: Document,
        knowledge_base: KnowledgeBase,
        content: bytes
    ) -> Document:
        """Process a document: parse, chunk, and embed."""
        try:
            # Update status to parsing
            document.status = DocumentStatus.PARSING.value
            await self._save_document(document)
            
            # Parse document
            parsed = await self._parse_content(content, document.content_type, document.url)
            document.content = parsed["content"]
            document.metadata = parsed
            
            # Update status to embedding
            document.status = DocumentStatus.EMBEDDING.value
            await self._save_document(document)
            
            # Chunk text
            chunks = chunk_text(
                document.content,
                strategy=knowledge_base.chunking_strategy,
                chunk_size=knowledge_base.chunk_size,
                overlap=knowledge_base.chunk_overlap
            )
            document.chunk_count = len(chunks)
            
            # Generate embeddings
            embedding_service = get_embedding_service(
                provider=knowledge_base.embedding_provider,
                model=knowledge_base.embedding_model
            )
            
            chunk_texts = [c["content"] for c in chunks]
            embeddings = await embedding_service.embed(chunk_texts)
            
            # Store in vector database
            retriever = Retriever(
                knowledge_base_id=knowledge_base.id,
                embedding_service=embedding_service
            )
            retriever.add_documents(
                document_id=document.id,
                document_title=document.title,
                chunks=chunks,
                embeddings=embeddings
            )
            
            # Update status to ready
            document.status = DocumentStatus.READY.value
            await self._save_document(document)
            
            logger.info(f"Document {document.id} processed successfully with {len(chunks)} chunks")
            return document
            
        except Exception as e:
            logger.error(f"Failed to process document {document.id}: {e}")
            document.status = DocumentStatus.ERROR.value
            document.error_message = str(e)
            await self._save_document(document)
            raise
    
    async def process_document_async(
        self,
        document: Document,
        knowledge_base: KnowledgeBase,
        content: bytes
    ):
        """Process document in background task."""
        asyncio.create_task(
            self.process_document(document, knowledge_base, content)
        )
    
    async def _parse_content(
        self,
        content: bytes,
        content_type: str,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Parse document content."""
        if content_type == ContentType.URL.value and url:
            from app.rag import URLParser
            parser = URLParser()
            return await parser.parse_async(url)
        else:
            return await parse_document(content, content_type, url)
    
    async def fetch_url_content(self, url: str) -> bytes:
        """Fetch content from URL."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    
    async def _save_document(self, document: Document):
        """Save document to database."""
        if self.db:
            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)
    
    async def delete_document_vectors(
        self,
        document_id: str,
        knowledge_base_id: str
    ):
        """Delete document vectors from vector database."""
        retriever = Retriever(knowledge_base_id=knowledge_base_id)
        retriever.delete_document(document_id)
    
    def get_file_extension(self, filename: str) -> str:
        """Get content type from file extension."""
        ext = Path(filename).suffix.lower().lstrip(".")
        type_map = {
            "pdf": ContentType.PDF.value,
            "docx": ContentType.WORD.value,
            "doc": ContentType.WORD.value,
            "txt": ContentType.TEXT.value,
            "md": ContentType.MARKDOWN.value,
            "markdown": ContentType.MARKDOWN.value,
            "csv": ContentType.CSV.value,
            "html": ContentType.HTML.value,
            "htm": ContentType.HTML.value,
        }
        return type_map.get(ext, ContentType.TEXT.value)


def generate_document_id() -> str:
    """Generate unique document ID."""
    return str(uuid.uuid4())


def get_upload_dir() -> Path:
    """Get upload directory path."""
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    return upload_dir
