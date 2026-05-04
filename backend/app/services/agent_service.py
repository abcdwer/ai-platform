"""Agent service for managing agents."""
import uuid
from typing import Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.agent import Agent
from app.models.schemas.agent import AgentCreate, AgentUpdate


class AgentService:
    """Service for managing agents."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_agent(
        self,
        user_id: str,
        agent_data: AgentCreate
    ) -> Agent:
        """Create a new agent."""
        # Convert tools to dict format
        tools_dict = None
        if agent_data.tools:
            tools_dict = [t.model_dump() for t in agent_data.tools]
        
        agent = Agent(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=agent_data.name,
            description=agent_data.description,
            system_prompt=agent_data.system_prompt,
            model=agent_data.model,
            model_provider=agent_data.model_provider,
            tools=tools_dict,
            temperature=agent_data.temperature,
            max_tokens=agent_data.max_tokens,
            top_p=agent_data.top_p,
            is_public=agent_data.is_public,
        )
        
        self.db.add(agent)
        await self.db.flush()
        await self.db.refresh(agent)
        return agent
    
    async def get_agent(self, agent_id: str, user_id: str = None) -> Optional[Agent]:
        """Get an agent by ID."""
        query = select(Agent).where(Agent.id == agent_id)
        
        if user_id:
            query = query.where(
                (Agent.user_id == user_id) | (Agent.is_public == True)
            )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_agents(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        include_public: bool = True
    ) -> tuple[List[Agent], int]:
        """Get paginated agents for a user."""
        query = select(Agent)
        
        if include_public:
            query = query.where((Agent.user_id == user_id) | (Agent.is_public == True))
        else:
            query = query.where(Agent.user_id == user_id)
        
        # Get total count
        count_query = select(Agent.id)
        if include_public:
            count_query = count_query.where((Agent.user_id == user_id) | (Agent.is_public == True))
        else:
            count_query = count_query.where(Agent.user_id == user_id)
        
        count_result = await self.db.execute(count_query)
        total = len(count_result.scalars().all())
        
        # Get paginated results
        query = query.order_by(Agent.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        agents = result.scalars().all()
        
        return agents, total
    
    async def update_agent(
        self,
        agent_id: str,
        user_id: str,
        agent_data: AgentUpdate
    ) -> Optional[Agent]:
        """Update an agent."""
        agent = await self.get_agent(agent_id, user_id)
        if not agent:
            return None
        
        # Only allow owner to update
        if agent.user_id != user_id:
            return None
        
        update_data = agent_data.model_dump(exclude_unset=True)
        
        # Handle tools specially
        if "tools" in update_data:
            if update_data["tools"] is not None:
                update_data["tools"] = [t.model_dump() if hasattr(t, "model_dump") else t for t in update_data["tools"]]
        
        for key, value in update_data.items():
            if hasattr(agent, key) and value is not None:
                setattr(agent, key, value)
        
        agent.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(agent)
        return agent
    
    async def delete_agent(self, agent_id: str, user_id: str) -> bool:
        """Delete an agent."""
        agent = await self.get_agent(agent_id, user_id)
        if not agent:
            return False
        
        # Only allow owner to delete
        if agent.user_id != user_id:
            return False
        
        await self.db.delete(agent)
        await self.db.flush()
        return True
    
    async def toggle_agent_active(
        self,
        agent_id: str,
        user_id: str,
        is_active: bool
    ) -> Optional[Agent]:
        """Toggle agent active status."""
        agent = await self.get_agent(agent_id, user_id)
        if not agent or agent.user_id != user_id:
            return None
        
        agent.is_active = is_active
        agent.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(agent)
        return agent
