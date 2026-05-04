"""Multi-Agent API routes with JWT authentication."""
import math
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.multi_agent_service import MultiAgentService
from app.models.schemas.multi_agent import (
    AgentGroupCreate, AgentGroupUpdate, AgentGroupResponse, AgentGroupListResponse,
    AgentMemberCreate, AgentMemberUpdate, AgentMemberResponse,
    SessionStart, SessionUpdate, SessionResponse, SessionListResponse,
    SessionExecuteRequest, SessionExecuteResponse,
    AgentMessageResponse
)
from app.models.multi_agent import SessionStatus
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/multi-agent", tags=["Multi-Agent"])


# ============== Agent Group Routes ==============

@router.post("/groups", response_model=AgentGroupResponse)
async def create_group(
    group_data: AgentGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new agent group."""
    service = MultiAgentService(db)
    group = await service.create_group(current_user.id, group_data)
    return AgentGroupResponse.model_validate(group)


@router.get("/groups", response_model=AgentGroupListResponse)
async def list_groups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all agent groups for the current user."""
    service = MultiAgentService(db)
    groups, total = await service.get_groups(current_user.id, page, page_size)
    
    return AgentGroupListResponse(
        items=[AgentGroupResponse.model_validate(g) for g in groups],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/groups/{group_id}", response_model=AgentGroupResponse)
async def get_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get an agent group by ID."""
    service = MultiAgentService(db)
    group = await service.get_group(group_id, current_user.id)
    
    if not group:
        raise HTTPException(status_code=404, detail="Agent group not found")
    
    return AgentGroupResponse.model_validate(group)


@router.put("/groups/{group_id}", response_model=AgentGroupResponse)
async def update_group(
    group_id: str,
    group_data: AgentGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an agent group."""
    service = MultiAgentService(db)
    group = await service.update_group(group_id, current_user.id, group_data)
    
    if not group:
        raise HTTPException(status_code=404, detail="Agent group not found or not authorized")
    
    return AgentGroupResponse.model_validate(group)


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an agent group."""
    service = MultiAgentService(db)
    deleted = await service.delete_group(group_id, current_user.id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent group not found or not authorized")
    
    return {"message": "Agent group deleted successfully"}


# ============== Agent Member Routes ==============

@router.post("/groups/{group_id}/members", response_model=AgentMemberResponse)
async def add_member(
    group_id: str,
    member_data: AgentMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a member to an agent group."""
    service = MultiAgentService(db)
    member = await service.add_member(group_id, current_user.id, member_data)
    
    if not member:
        raise HTTPException(status_code=404, detail="Agent group not found or not authorized")
    
    return AgentMemberResponse.model_validate(member)


@router.put("/groups/{group_id}/members/{member_id}", response_model=AgentMemberResponse)
async def update_member(
    group_id: str,
    member_id: str,
    member_data: AgentMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a member in an agent group."""
    service = MultiAgentService(db)
    member = await service.update_member(member_id, current_user.id, member_data)
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found or not authorized")
    
    return AgentMemberResponse.model_validate(member)


@router.delete("/groups/{group_id}/members/{member_id}")
async def delete_member(
    group_id: str,
    member_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a member from an agent group."""
    service = MultiAgentService(db)
    deleted = await service.delete_member(member_id, current_user.id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Member not found or not authorized")
    
    return {"message": "Member deleted successfully"}


# ============== Session Routes ==============

@router.post("/groups/{group_id}/sessions", response_model=SessionResponse)
async def start_session(
    group_id: str,
    session_data: SessionStart,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new collaboration session."""
    service = MultiAgentService(db)
    session = await service.start_session(group_id, current_user.id, session_data)
    
    if not session:
        raise HTTPException(status_code=404, detail="Agent group not found or not authorized")
    
    return SessionResponse.model_validate(session)


@router.get("/groups/{group_id}/sessions", response_model=SessionListResponse)
async def list_sessions(
    group_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all sessions for a group."""
    service = MultiAgentService(db)
    sessions, total = await service.get_sessions(group_id, current_user.id, page, page_size)
    
    return SessionListResponse(
        items=[SessionResponse.model_validate(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/groups/{group_id}/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    group_id: str,
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a session by ID."""
    service = MultiAgentService(db)
    session = await service.get_session(session_id, current_user.id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or not authorized")
    
    return SessionResponse.model_validate(session)


@router.delete("/groups/{group_id}/sessions/{session_id}")
async def delete_session(
    group_id: str,
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a session."""
    service = MultiAgentService(db)
    deleted = await service.delete_session(session_id, current_user.id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found or not authorized")
    
    return {"message": "Session deleted successfully"}


# ============== Execution Routes ==============

@router.post("/groups/{group_id}/sessions/{session_id}/execute", response_model=SessionExecuteResponse)
async def execute_session(
    group_id: str,
    session_id: str,
    request: SessionExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute a collaboration session."""
    service = MultiAgentService(db)
    
    try:
        result = await service.execute_session(session_id, current_user.id, request.user_input)
        return SessionExecuteResponse(
            session_id=session_id,
            messages=result.get("messages", []),
            final_output=result.get("final_output"),
            iterations=result.get("iterations", 0),
            status="completed"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/sessions/{session_id}/messages", response_model=list[AgentMessageResponse])
async def get_session_messages(
    group_id: str,
    session_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get messages from a session."""
    service = MultiAgentService(db)
    messages = await service.get_messages(session_id, current_user.id, limit)
    
    return [AgentMessageResponse.model_validate(m) for m in messages]


@router.post("/groups/{group_id}/sessions/{session_id}/reset")
async def reset_session(
    group_id: str,
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reset a session's messages."""
    service = MultiAgentService(db)
    success = await service.reset_session(session_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or not authorized")
    
    return {"message": "Session reset successfully"}
