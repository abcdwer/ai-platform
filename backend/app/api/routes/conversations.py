"""Conversations API routes with JWT authentication and comprehensive API documentation."""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas.conversation import (
    ConversationCreate, ConversationUpdate, ConversationResponse, ConversationListResponse
)
from app.services.conversation_service import ConversationService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/api/conversations", 
    tags=["Conversations"],
    summary="Conversation Management",
    description="""
    Manage chat conversations with AI models.
    
    Features:
    - Create, read, update, delete conversations
    - Archive and pin conversations
    - Search conversation history
    - Export conversations to various formats (Markdown, JSON, PDF, HTML)
    
    Each conversation can contain multiple messages exchanged between 
    the user and AI assistant, with support for tool calls and function execution.
    """
)


@router.post(
    "",
    response_model=ConversationResponse,
    summary="Create Conversation",
    description="Create a new chat conversation with optional AI agent and model configuration",
    responses={
        201: {"description": "Conversation created successfully"},
        401: {"description": "Authentication required"},
    }
)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new conversation.
    
    - **title**: Optional conversation title (auto-generated if not provided)
    - **agent_id**: Optional AI agent ID to use for this conversation
    - **model**: Model name to use (default: llama2)
    - **model_provider**: Model provider (default: ollama)
    
    Returns the created conversation with empty messages array.
    """
    service = ConversationService(db)
    conversation = await service.create(
        user_id=current_user.id,
        title=conversation_data.title or "New Chat",
        agent_id=conversation_data.agent_id,
        model=conversation_data.model or "llama2",
        model_provider=conversation_data.model_provider or "ollama"
    )
    return conversation


@router.get(
    "",
    response_model=ConversationListResponse,
    summary="List Conversations",
    description="Get paginated list of conversations with optional filtering",
    responses={
        200: {"description": "List of conversations"},
        401: {"description": "Authentication required"},
    }
)
async def list_conversations(
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    include_archived: bool = Query(False, description="Include archived conversations"),
    search: Optional[str] = Query(None, description="Search query for conversation titles"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all conversations for the current user with pagination.
    
    - **page**: Page number for pagination
    - **page_size**: Number of items per page
    - **include_archived**: Whether to include archived conversations
    - **search**: Optional search filter for conversation titles
    
    Returns paginated list of conversations sorted by update time (newest first).
    """
    service = ConversationService(db)
    conversations, total = await service.get_all(
        current_user.id, page, page_size, include_archived, search
    )
    
    return ConversationListResponse(
        items=[ConversationResponse.model_validate(c) for c in conversations],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get(
    "/search",
    summary="Search Conversations",
    description="Quick search for conversations by title or content",
    responses={
        200: {"description": "Search results"},
        401: {"description": "Authentication required"},
    }
)
async def search_conversations(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search conversations by title or content keywords.
    
    - **q**: Search query string (minimum 1 character)
    - **limit**: Maximum number of results (1-50, default 10)
    
    Returns matching conversations with relevance scoring.
    """
    service = ConversationService(db)
    results = await service.search(current_user.id, q, limit)
    return {"results": results}


@router.get(
    "/stats",
    summary="Get Conversation Statistics",
    description="Get statistics about user's conversations",
    responses={
        200: {"description": "Conversation statistics"},
        401: {"description": "Authentication required"},
    }
)
async def get_conversation_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get conversation statistics for the current user.
    
    Returns counts of:
    - Total conversations
    - Archived conversations
    - Pinned conversations
    - Total messages
    """
    service = ConversationService(db)
    stats = await service.get_stats(current_user.id)
    return stats


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get Conversation",
    description="Retrieve a conversation by ID with all its messages",
    responses={
        200: {"description": "Conversation details with messages"},
        401: {"description": "Authentication required"},
        404: {"description": "Conversation not found"},
    }
)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a conversation by ID with all its messages.
    
    - **conversation_id**: Unique identifier of the conversation
    
    Returns the conversation object including all messages sorted by creation time.
    """
    service = ConversationService(db)
    conversation = await service.get(conversation_id, current_user.id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation


@router.put(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Update Conversation",
    description="Update conversation metadata (title, pinned status, archived status)",
    responses={
        200: {"description": "Updated conversation"},
        401: {"description": "Authentication required"},
        404: {"description": "Conversation not found"},
    }
)
async def update_conversation(
    conversation_id: str,
    conversation_data: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update conversation metadata.
    
    - **conversation_id**: Unique identifier of the conversation
    - **title**: New conversation title (optional)
    - **is_pinned**: Pin/unpin the conversation (optional)
    - **is_archived**: Archive/unarchive the conversation (optional)
    
    Only provided fields will be updated.
    """
    service = ConversationService(db)
    update_data = conversation_data.model_dump(exclude_unset=True)
    conversation = await service.update(conversation_id, current_user.id, **update_data)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation


@router.patch(
    "/{conversation_id}/title",
    response_model=ConversationResponse,
    summary="Update Conversation Title",
    description="Update or auto-generate conversation title",
    responses={
        200: {"description": "Updated conversation"},
        401: {"description": "Authentication required"},
        404: {"description": "Conversation not found"},
    }
)
async def update_conversation_title(
    conversation_id: str,
    title: Optional[str] = Query(None, description="New title (auto-generated if not provided)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update conversation title with optional auto-generation.
    
    - **conversation_id**: Unique identifier of the conversation
    - **title**: New title (if not provided, title will be auto-generated from first message)
    """
    service = ConversationService(db)
    conversation = await service.update_title(conversation_id, current_user.id, title)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation


@router.delete(
    "/{conversation_id}",
    summary="Delete Conversation",
    description="Permanently delete a conversation and all its messages",
    responses={
        200: {"description": "Conversation deleted successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Conversation not found"},
    }
)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a conversation permanently.
    
    - **conversation_id**: Unique identifier of the conversation
    
    This action cannot be undone. All messages in the conversation will be deleted.
    """
    service = ConversationService(db)
    deleted = await service.delete(conversation_id, current_user.id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"message": "Conversation deleted successfully"}


@router.post(
    "/{conversation_id}/archive",
    response_model=ConversationResponse,
    summary="Archive Conversation",
    description="Move conversation to archived status",
    responses={
        200: {"description": "Conversation archived"},
        401: {"description": "Authentication required"},
        404: {"description": "Conversation not found"},
    }
)
async def archive_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Archive a conversation.
    
    - **conversation_id**: Unique identifier of the conversation
    
    Archived conversations are hidden from the main list but can be retrieved 
    using the `include_archived=true` parameter.
    """
    service = ConversationService(db)
    conversation = await service.archive(conversation_id, current_user.id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation


@router.post(
    "/{conversation_id}/unarchive",
    response_model=ConversationResponse,
    summary="Unarchive Conversation",
    description="Restore an archived conversation",
    responses={
        200: {"description": "Conversation restored"},
        401: {"description": "Authentication required"},
        404: {"description": "Conversation not found"},
    }
)
async def unarchive_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Restore an archived conversation.
    
    - **conversation_id**: Unique identifier of the conversation
    
    The conversation will reappear in the main conversation list.
    """
    service = ConversationService(db)
    conversation = await service.unarchive(conversation_id, current_user.id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation


@router.post(
    "/{conversation_id}/pin",
    response_model=ConversationResponse,
    summary="Toggle Pin Status",
    description="Pin or unpin a conversation",
    responses={
        200: {"description": "Pin status toggled"},
        401: {"description": "Authentication required"},
        404: {"description": "Conversation not found"},
    }
)
async def toggle_pin_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Toggle pin status of a conversation.
    
    - **conversation_id**: Unique identifier of the conversation
    
    Pinned conversations appear at the top of the conversation list.
    """
    service = ConversationService(db)
    conversation = await service.toggle_pin(conversation_id, current_user.id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation
