"""Multi-Agent service for managing agent groups and sessions."""
import uuid
from typing import Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.multi_agent import (
    AgentGroup, AgentMember, CollaborationSession, AgentMessage,
    SessionStatus, MessageType
)
from app.models.schemas.multi_agent import (
    AgentGroupCreate, AgentGroupUpdate, AgentGroupResponse,
    AgentMemberCreate, AgentMemberUpdate,
    SessionStart, SessionUpdate, SessionExecuteResponse,
    AgentMessageResponse
)


class MultiAgentService:
    """Service for managing multi-agent collaboration."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============== Agent Group Operations ==============
    
    async def create_group(
        self,
        user_id: str,
        group_data: AgentGroupCreate
    ) -> AgentGroup:
        """Create a new agent group with members."""
        group = AgentGroup(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=group_data.name,
            description=group_data.description,
            mode=group_data.mode,
            mode_config=group_data.mode_config,
            default_model=group_data.default_model,
            default_provider=group_data.default_provider,
            enable_orchestrator=group_data.enable_orchestrator,
            orchestrator_prompt=group_data.orchestrator_prompt,
            max_iterations=group_data.max_iterations,
            termination_prompt=group_data.termination_prompt,
        )
        
        self.db.add(group)
        
        # Add members if provided
        if group_data.members:
            for i, member_data in enumerate(group_data.members):
                member = AgentMember(
                    id=str(uuid.uuid4()),
                    group_id=group.id,
                    name=member_data.name,
                    role=member_data.role,
                    system_prompt=member_data.system_prompt,
                    execution_order=member_data.execution_order or i,
                    model=member_data.model,
                    model_provider=member_data.model_provider,
                    temperature=member_data.temperature,
                    max_tokens=member_data.max_tokens,
                    tools=member_data.tools,
                    icon=member_data.icon,
                    color=member_data.color,
                )
                self.db.add(member)
        
        await self.db.flush()
        await self.db.refresh(group)
        return group
    
    async def get_group(
        self, 
        group_id: str, 
        user_id: str = None,
        include_members: bool = True
    ) -> Optional[AgentGroup]:
        """Get an agent group by ID."""
        query = select(AgentGroup).where(AgentGroup.id == group_id)
        
        if user_id:
            query = query.where(AgentGroup.user_id == user_id)
        
        if include_members:
            query = query.options(selectinload(AgentGroup.members))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_groups(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[AgentGroup], int]:
        """Get paginated agent groups for a user."""
        # Count query
        count_query = select(func.count(AgentGroup.id)).where(
            AgentGroup.user_id == user_id
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Data query
        query = (
            select(AgentGroup)
            .where(AgentGroup.user_id == user_id)
            .options(selectinload(AgentGroup.members))
            .order_by(AgentGroup.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        
        result = await self.db.execute(query)
        groups = result.scalars().all()
        
        return groups, total
    
    async def update_group(
        self,
        group_id: str,
        user_id: str,
        group_data: AgentGroupUpdate
    ) -> Optional[AgentGroup]:
        """Update an agent group."""
        group = await self.get_group(group_id, user_id)
        if not group:
            return None
        
        update_data = group_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(group, key) and value is not None:
                setattr(group, key, value)
        
        group.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(group)
        return group
    
    async def delete_group(self, group_id: str, user_id: str) -> bool:
        """Delete an agent group."""
        group = await self.get_group(group_id, user_id, include_members=False)
        if not group:
            return False
        
        await self.db.delete(group)
        await self.db.flush()
        return True
    
    # ============== Agent Member Operations ==============
    
    async def add_member(
        self,
        group_id: str,
        user_id: str,
        member_data: AgentMemberCreate
    ) -> Optional[AgentMember]:
        """Add a member to an agent group."""
        group = await self.get_group(group_id, user_id, include_members=False)
        if not group:
            return None
        
        member = AgentMember(
            id=str(uuid.uuid4()),
            group_id=group_id,
            name=member_data.name,
            role=member_data.role,
            system_prompt=member_data.system_prompt,
            execution_order=member_data.execution_order,
            model=member_data.model,
            model_provider=member_data.model_provider,
            temperature=member_data.temperature,
            max_tokens=member_data.max_tokens,
            tools=member_data.tools,
            icon=member_data.icon,
            color=member_data.color,
        )
        
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member
    
    async def get_member(
        self,
        member_id: str,
        user_id: str = None
    ) -> Optional[AgentMember]:
        """Get a member by ID."""
        query = select(AgentMember).where(AgentMember.id == member_id)
        
        if user_id:
            query = query.join(AgentGroup).where(AgentGroup.user_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_member(
        self,
        member_id: str,
        user_id: str,
        member_data: AgentMemberUpdate
    ) -> Optional[AgentMember]:
        """Update a member."""
        member = await self.get_member(member_id, user_id)
        if not member:
            return None
        
        update_data = member_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(member, key) and value is not None:
                setattr(member, key, value)
        
        member.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(member)
        return member
    
    async def delete_member(self, member_id: str, user_id: str) -> bool:
        """Delete a member from a group."""
        member = await self.get_member(member_id, user_id)
        if not member:
            return False
        
        await self.db.delete(member)
        await self.db.flush()
        return True
    
    async def reorder_members(
        self,
        group_id: str,
        user_id: str,
        member_orders: List[dict]
    ) -> bool:
        """Reorder members in a group."""
        group = await self.get_group(group_id, user_id, include_members=True)
        if not group:
            return False
        
        for order_data in member_orders:
            member_id = order_data.get("id")
            new_order = order_data.get("order", 0)
            for member in group.members:
                if member.id == member_id:
                    member.execution_order = new_order
                    break
        
        await self.db.flush()
        return True
    
    # ============== Session Operations ==============
    
    async def create_session(
        self,
        group_id: str,
        user_id: str,
        session_data: SessionStart
    ) -> Optional[CollaborationSession]:
        """Create a new collaboration session."""
        group = await self.get_group(group_id, user_id)
        if not group:
            return None
        
        session = CollaborationSession(
            id=str(uuid.uuid4()),
            group_id=group_id,
            user_id=user_id,
            status=SessionStatus.CREATED.value,
            initial_input=session_data.initial_input,
            context=session_data.context or {},
        )
        
        # Add initial user message
        initial_message = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=session.id,
            member_id=None,
            message_type=MessageType.USER_INPUT.value,
            content=session_data.initial_input,
            turn=0,
            iteration=0,
        )
        
        self.db.add(session)
        self.db.add(initial_message)
        
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def get_session(
        self,
        session_id: str,
        user_id: str = None,
        include_messages: bool = True
    ) -> Optional[CollaborationSession]:
        """Get a session by ID."""
        query = select(CollaborationSession).where(
            CollaborationSession.id == session_id
        )
        
        if user_id:
            query = query.where(CollaborationSession.user_id == user_id)
        
        if include_messages:
            query = query.options(
                selectinload(CollaborationSession.messages)
                .selectinload(AgentMessage.member)
            )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_sessions(
        self,
        group_id: str,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        include_messages: bool = False
    ) -> tuple[List[CollaborationSession], int]:
        """Get paginated sessions for a group."""
        base_filter = [CollaborationSession.group_id == group_id]
        if user_id:
            base_filter.append(CollaborationSession.user_id == user_id)
        
        # Count query
        count_query = select(func.count(CollaborationSession.id)).where(*base_filter)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Data query
        query = (
            select(CollaborationSession)
            .where(*base_filter)
            .order_by(CollaborationSession.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        
        if include_messages:
            query = query.options(
                selectinload(CollaborationSession.messages)
                .selectinload(AgentMessage.member)
            )
        
        result = await self.db.execute(query)
        sessions = result.scalars().all()
        
        return sessions, total
    
    async def update_session(
        self,
        session_id: str,
        user_id: str,
        session_data: SessionUpdate
    ) -> Optional[CollaborationSession]:
        """Update a session."""
        session = await self.get_session(session_id, user_id, include_messages=False)
        if not session:
            return None
        
        update_data = session_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(session, key) and value is not None:
                setattr(session, key, value)
        
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def add_message(
        self,
        session_id: str,
        member_id: Optional[str],
        message_type: str,
        content: str,
        turn: int = 0,
        iteration: int = 0,
        referenced_message_id: Optional[str] = None,
        tool_calls: Optional[list] = None,
        tool_results: Optional[list] = None,
        model_used: Optional[str] = None,
        tokens_used: Optional[int] = None,
        execution_time_ms: Optional[int] = None,
    ) -> AgentMessage:
        """Add a message to a session."""
        message = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            member_id=member_id,
            message_type=message_type,
            content=content,
            referenced_message_id=referenced_message_id,
            tool_calls=tool_calls,
            tool_results=tool_results,
            model_used=model_used,
            tokens_used=tokens_used,
            execution_time_ms=execution_time_ms,
            turn=turn,
            iteration=iteration,
        )
        
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message
    
    async def get_session_messages(
        self,
        session_id: str,
        user_id: str = None,
        member_id: Optional[str] = None
    ) -> List[AgentMessage]:
        """Get messages for a session."""
        session = await self.get_session(session_id, user_id)
        if not session:
            return []
        
        messages = session.messages
        if member_id:
            messages = [m for m in messages if m.member_id == member_id]
        
        return messages
    
    async def get_group_with_members(self, group_id: str, user_id: str = None) -> Optional[dict]:
        """Get group with its members for execution."""
        group = await self.get_group(group_id, user_id, include_members=True)
        if not group:
            return None
        
        return {
            "id": group.id,
            "name": group.name,
            "mode": group.mode,
            "mode_config": group.mode_config or {},
            "default_model": group.default_model,
            "default_provider": group.default_provider,
            "enable_orchestrator": group.enable_orchestrator,
            "orchestrator_prompt": group.orchestrator_prompt,
            "max_iterations": group.max_iterations,
            "termination_prompt": group.termination_prompt,
            "members": [
                {
                    "id": m.id,
                    "name": m.name,
                    "role": m.role,
                    "system_prompt": m.system_prompt,
                    "execution_order": m.execution_order,
                    "model": m.model or group.default_model,
                    "model_provider": m.model_provider or group.default_provider,
                    "temperature": m.temperature,
                    "max_tokens": m.max_tokens,
                    "tools": m.tools or [],
                    "icon": m.icon,
                    "color": m.color,
                }
                for m in sorted(group.members, key=lambda x: x.execution_order)
            ]
        }
