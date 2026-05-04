"""Chat API routes with JWT authentication."""
import json
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas.conversation import ChatRequest, ChatResponse, MessageResponse
from app.services.model_dispatcher import get_model_dispatcher
from app.services.chat_service import ChatService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """Process a non-streaming chat request."""
    dispatcher = get_model_dispatcher()
    chat_service = ChatService(db, dispatcher)
    
    try:
        conversation, message = await chat_service.chat(request, current_user.id)
        
        return ChatResponse(
            message=MessageResponse.model_validate(message),
            conversation_id=conversation.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process a streaming chat request with SSE."""
    dispatcher = get_model_dispatcher()
    chat_service = ChatService(db, dispatcher)
    
    async def event_generator():
        try:
            async for chunk in chat_service.chat_stream(request, current_user.id):
                if chunk["type"] == "conversation_id":
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif chunk["type"] == "message":
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif chunk["type"] == "tool_call":
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif chunk["type"] == "done":
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif chunk["type"] == "error":
                    yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chat"}
