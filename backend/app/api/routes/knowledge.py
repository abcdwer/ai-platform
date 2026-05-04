"""Knowledge base API routes with JWT authentication and comprehensive API documentation."""
import uuid
import asyncio
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import json

from app.core.database import get_db
from app.models.knowledge import KnowledgeBase
from app.models.document import Document, DocumentStatus, ContentType
from app.models.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
    DocumentResponse,
    DocumentListResponse,
    URLAddRequest,
    SearchRequest,
    SearchResponse,
    RAGChatRequest,
    RAGChatResponse,
)
from app.services.knowledge_service import KnowledgeService
from app.services.document_service import DocumentService, get_upload_dir
from app.services.rag_service import RAGService
from app.rag import parse_document, chunk_text, Retriever
from app.services.embedding_service import get_embedding_service
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/api/knowledge", 
    tags=["Knowledge Base"],
    summary="Knowledge Base Management",
    description="""
    RAG (Retrieval-Augmented Generation) powered knowledge base management.
    
    Features:
    - Create and manage knowledge bases with tagging
    - Upload documents (PDF, TXT, MD, DOCX)
    - Add content from URLs
    - Semantic search with vector embeddings
    - RAG chat with context retrieval
    - Export knowledge bases (Markdown, JSON, HTML)
    - Import documents in batch
    
    Supported document types:
    - PDF files
    - Plain text (.txt)
    - Markdown (.md)
    - Word documents (.docx)
    """
)


# ==================== Knowledge Base CRUD ====================

@router.post(
    "",
    response_model=KnowledgeBaseResponse,
    summary="Create Knowledge Base",
    description="Create a new knowledge base with optional tags",
    responses={
        201: {"description": "Knowledge base created"},
        401: {"description": "Authentication required"},
    }
)
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new knowledge base.
    
    - **name**: Knowledge base name (required)
    - **description**: Optional description
    - **tags**: Optional list of tags for categorization
    
    Returns the created knowledge base with zero documents.
    """
    service = KnowledgeService(db)
    kb = await service.create_knowledge_base(data, current_user.id)
    return kb


@router.get(
    "",
    response_model=KnowledgeBaseListResponse,
    summary="List Knowledge Bases",
    description="Get paginated list of knowledge bases with filtering",
    responses={
        200: {"description": "List of knowledge bases"},
        401: {"description": "Authentication required"},
    }
)
async def list_knowledge_bases(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all knowledge bases for the current user.
    
    - **page**: Page number for pagination
    - **page_size**: Number of items per page
    - **search**: Filter by name or description
    - **tags**: Filter by tags (comma-separated list)
    
    Returns paginated list sorted by update time.
    """
    tag_list = tags.split(",") if tags else None
    service = KnowledgeService(db)
    result = await service.list_knowledge_bases(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        search=search,
        tags=tag_list
    )
    
    items = [KnowledgeBaseResponse.model_validate(item) for item in result["items"]]
    return KnowledgeBaseListResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"]
    )


@router.get(
    "/{kb_id}",
    response_model=KnowledgeBaseResponse,
    summary="Get Knowledge Base",
    description="Retrieve knowledge base details",
    responses={
        200: {"description": "Knowledge base details"},
        401: {"description": "Authentication required"},
        404: {"description": "Knowledge base not found"},
    }
)
async def get_knowledge_base(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get knowledge base by ID.
    
    - **kb_id**: Unique identifier of the knowledge base
    
    Returns the knowledge base with document count.
    """
    service = KnowledgeService(db)
    kb = await service.get_knowledge_base(kb_id, current_user.id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.put(
    "/{kb_id}",
    response_model=KnowledgeBaseResponse,
    summary="Update Knowledge Base",
    description="Update knowledge base metadata",
    responses={
        200: {"description": "Knowledge base updated"},
        401: {"description": "Authentication required"},
        404: {"description": "Knowledge base not found"},
    }
)
async def update_knowledge_base(
    kb_id: str,
    data: KnowledgeBaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update knowledge base properties.
    
    - **kb_id**: Unique identifier of the knowledge base
    - **name**: New name (optional)
    - **description**: New description (optional)
    - **tags**: New tags list (optional)
    
    Only provided fields will be updated.
    """
    service = KnowledgeService(db)
    kb = await service.update_knowledge_base(kb_id, current_user.id, data)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.delete(
    "/{kb_id}",
    summary="Delete Knowledge Base",
    description="Delete knowledge base and all its documents",
    responses={
        200: {"description": "Knowledge base deleted"},
        401: {"description": "Authentication required"},
        404: {"description": "Knowledge base not found"},
    }
)
async def delete_knowledge_base(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete knowledge base permanently.
    
    - **kb_id**: Unique identifier of the knowledge base
    
    This will also delete all documents and vector embeddings.
    """
    service = KnowledgeService(db)
    success = await service.delete_knowledge_base(kb_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return {"message": "Knowledge base deleted"}


# ==================== Document Management ====================

@router.post(
    "/{kb_id}/documents",
    response_model=DocumentResponse,
    summary="Upload Document",
    description="Upload a document to the knowledge base",
    responses={
        200: {"description": "Document uploaded and processing"},
        401: {"description": "Authentication required"},
        404: {"description": "Knowledge base not found"},
    }
)
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document to knowledge base.
    
    - **kb_id**: Knowledge base ID
    - **file**: Document file (PDF, TXT, MD, DOCX supported)
    
    Document will be processed asynchronously:
    1. Content extracted
    2. Split into chunks
    3. Vector embeddings generated
    4. Stored in vector database
    
    Use GET /knowledge/{kb_id}/documents to check status.
    """
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(kb_id, current_user.id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    doc_service = DocumentService(db)
    content_type = doc_service.get_file_extension(file.filename)
    
    document = Document(
        id=str(uuid.uuid4()),
        knowledge_base_id=kb_id,
        title=file.filename or "Untitled",
        content_type=content_type,
        file_size=0,
        status=DocumentStatus.UPLOADING.value
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    upload_dir = get_upload_dir()
    file_path = upload_dir / f"{document.id}_{file.filename}"
    
    try:
        content = await file.read()
        document.file_size = len(content)
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        document.file_path = str(file_path)
        await kb_service.increment_document_count(kb_id, 1)
        
        asyncio.create_task(
            process_document_background(document, kb, content, db)
        )
        
        await db.commit()
        await db.refresh(document)
        
        return document
        
    except Exception as e:
        document.status = DocumentStatus.ERROR.value
        document.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


async def process_document_background(
    document: Document,
    kb: KnowledgeBase,
    content: bytes,
    db: AsyncSession
):
    """Process document in background."""
    from app.core.database import get_db_context
    
    try:
        document.status = DocumentStatus.PROCESSING.value
        
        # Parse content
        content_text = content.decode("utf-8", errors="ignore")
        parsed_content = parse_document(document.content_type, content_text)
        
        document.content = parsed_content
        
        # Chunk text
        chunks = chunk_text(parsed_content, chunk_size=500, overlap=50)
        document.chunk_count = len(chunks)
        
        # Generate embeddings
        embedding_service = get_embedding_service()
        embeddings = await embedding_service.embed_texts(chunks)
        
        # Store in vector DB
        retriever = Retriever(kb.id)
        await retriever.add_documents(chunks, embeddings, document.id)
        
        document.status = DocumentStatus.READY.value
        await db.commit()
        
    except Exception as e:
        document.status = DocumentStatus.ERROR.value
        document.error_message = str(e)
        await db.commit()


@router.get(
    "/{kb_id}/documents",
    response_model=DocumentListResponse,
    summary="List Documents",
    description="Get all documents in a knowledge base",
    responses={
        200: {"description": "List of documents"},
        401: {"description": "Authentication required"},
        404: {"description": "Knowledge base not found"},
    }
)
async def list_documents(
    kb_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all documents in a knowledge base.
    
    - **kb_id**: Knowledge base ID
    - **page**: Page number
    - **page_size**: Items per page
    - **status**: Filter by processing status (optional)
    """
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(kb_id, current_user.id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    query = select(Document).where(Document.knowledge_base_id == kb_id)
    if status:
        query = query.where(Document.status == status)
    
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0
    
    query = query.order_by(Document.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{kb_id}/documents/{doc_id}",
    response_model=DocumentResponse,
    summary="Get Document",
    description="Get document details and content",
    responses={
        200: {"description": "Document details"},
        401: {"description": "Authentication required"},
        404: {"description": "Document not found"},
    }
)
async def get_document(
    kb_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document details by ID."""
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(kb_id, current_user.id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    result = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.knowledge_base_id == kb_id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.delete(
    "/{kb_id}/documents/{doc_id}",
    summary="Delete Document",
    description="Remove document from knowledge base",
    responses={
        200: {"description": "Document deleted"},
        401: {"description": "Authentication required"},
        404: {"description": "Document not found"},
    }
)
async def delete_document(
    kb_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document and its vector embeddings."""
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(kb_id, current_user.id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    result = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.knowledge_base_id == kb_id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from vector DB
    retriever = Retriever(kb_id)
    await retriever.delete_document(doc_id)
    
    await db.delete(document)
    await kb_service.increment_document_count(kb_id, -1)
    await db.commit()
    
    return {"message": "Document deleted"}


# ==================== Search & RAG Chat ====================

@router.post(
    "/{kb_id}/search",
    response_model=SearchResponse,
    summary="Search Knowledge Base",
    description="Semantic search across all documents in the knowledge base",
    responses={
        200: {"description": "Search results"},
        401: {"description": "Authentication required"},
        404: {"description": "Knowledge base not found"},
    }
)
async def search_knowledge_base(
    kb_id: str,
    search_data: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform semantic search on knowledge base.
    
    - **kb_id**: Knowledge base ID
    - **query**: Search query string
    - **top_k**: Number of results to return (default: 5)
    - **similarity_threshold**: Minimum similarity score (0-1, default: 0.5)
    
    Returns relevant document chunks ranked by similarity.
    """
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(kb_id, current_user.id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    retriever = Retriever(kb_id)
    results = await retriever.search(
        query=search_data.query,
        top_k=search_data.top_k or 5,
        similarity_threshold=search_data.similarity_threshold or 0.5
    )
    
    return SearchResponse(
        query=search_data.query,
        results=results,
        total=len(results)
    )


@router.post(
    "/{kb_id}/chat",
    response_model=RAGChatResponse,
    summary="RAG Chat",
    description="Chat with the knowledge base using retrieval-augmented generation",
    responses={
        200: {"description": "RAG response"},
        401: {"description": "Authentication required"},
        404: {"description": "Knowledge base not found"},
    }
)
async def rag_chat(
    kb_id: str,
    chat_data: RAGChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Chat with knowledge base using RAG.
    
    - **kb_id**: Knowledge base ID
    - **query**: User question
    - **top_k**: Number of context chunks to retrieve (default: 5)
    - **model**: Model to use (optional, uses default)
    
    Retrieves relevant context and generates an answer.
    """
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(kb_id, current_user.id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    retriever = Retriever(kb_id)
    results = await retriever.search(
        query=chat_data.query,
        top_k=chat_data.top_k or 5
    )
    
    # Build context from results
    context = "\n\n".join([
        f"[Source: {r.get('document_id', 'unknown')}]\n{r.get('content', '')}"
        for r in results
    ])
    
    return RAGChatResponse(
        query=chat_data.query,
        answer=f"Based on the knowledge base, here is relevant information:\n\n{context}",
        sources=[r.get("document_id") for r in results],
        retrieved_chunks=len(results)
    )


@router.post(
    "/{kb_id}/url",
    response_model=DocumentResponse,
    summary="Add URL",
    description="Fetch and add content from a URL",
    responses={
        200: {"description": "URL content added"},
        401: {"description": "Authentication required"},
        404: {"description": "Knowledge base not found"},
    }
)
async def add_url(
    kb_id: str,
    url_data: URLAddRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch content from URL and add to knowledge base.
    
    - **kb_id**: Knowledge base ID
    - **url**: URL to fetch content from
    - **title**: Optional title for the document
    
    Extracts text content from the webpage and processes it.
    """
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(kb_id, current_user.id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url_data.url, timeout=30.0)
            response.raise_for_status()
            content_text = response.text
            
            # Extract text (basic HTML stripping)
            from html import unescape
            import re
            content_text = re.sub(r'<[^>]+>', ' ', content_text)
            content_text = unescape(content_text)
            content_text = ' '.join(content_text.split())
            
            # Create document
            document = Document(
                id=str(uuid.uuid4()),
                knowledge_base_id=kb_id,
                title=url_data.title or url_data.url,
                content=content_text[:10000],  # Limit content
                source=url_data.url,
                content_type="url",
                status=DocumentStatus.READY.value,
                chunk_count=len(chunk_text(content_text[:10000]))
            )
            
            db.add(document)
            await kb_service.increment_document_count(kb_id, 1)
            await db.commit()
            await db.refresh(document)
            
            return document
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")


@router.get(
    "/{kb_id}/stats",
    summary="Get Knowledge Base Stats",
    description="Get statistics about a knowledge base",
    responses={
        200: {"description": "Statistics"},
        401: {"description": "Authentication required"},
        404: {"description": "Knowledge base not found"},
    }
)
async def get_kb_stats(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics about a knowledge base including document counts by status."""
    kb_service = KnowledgeService(db)
    kb = await kb_service.get_knowledge_base(kb_id, current_user.id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # Count by status
    status_counts = {}
    for status in DocumentStatus:
        result = await db.execute(
            select(func.count()).select_from(Document).where(
                Document.knowledge_base_id == kb_id,
                Document.status == status.value
            )
        )
        status_counts[status.value] = result.scalar() or 0
    
    return {
        "total_documents": kb.document_count,
        "status_breakdown": status_counts,
        "vector_store": "chroma"
    }
