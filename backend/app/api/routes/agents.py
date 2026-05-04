"""Agents API routes with JWT authentication."""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas.agent import (
    AgentCreate, AgentUpdate, AgentResponse, AgentListResponse
)
from app.services.agent_service import AgentService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/agents", tags=["Agents"])


@router.post("", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new agent."""
    service = AgentService(db)
    agent = await service.create_agent(current_user.id, agent_data)
    return agent


@router.get("", response_model=AgentListResponse)
async def list_agents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_public: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all agents for the current user."""
    service = AgentService(db)
    agents, total = await service.get_agents(current_user.id, page, page_size, include_public)
    
    return AgentListResponse(
        items=[AgentResponse.model_validate(a) for a in agents],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get an agent by ID."""
    service = AgentService(db)
    agent = await service.get_agent(agent_id, current_user.id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an agent."""
    service = AgentService(db)
    agent = await service.update_agent(agent_id, current_user.id, agent_data)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or not authorized")
    
    return agent


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an agent."""
    service = AgentService(db)
    deleted = await service.delete_agent(agent_id, current_user.id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found or not authorized")
    
    return {"message": "Agent deleted successfully"}


@router.post("/{agent_id}/toggle")
async def toggle_agent(
    agent_id: str,
    is_active: bool = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle agent active status."""
    service = AgentService(db)
    agent = await service.toggle_agent_active(agent_id, current_user.id, is_active)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or not authorized")
    
    return {"message": f"Agent {'activated' if is_active else 'deactivated'}"}
