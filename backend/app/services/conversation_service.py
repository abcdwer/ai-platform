"""Conversation service."""
import uuid
import re
from typing import Optional, List, AsyncIterator, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from app.models.conversation import Conversation, Message


class ConversationService:
    """Service for managing conversations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        user_id: str,
        title: str = "New Conversation",
        agent_id: Optional[str] = None,
        model: str = "llama2",
        model_provider: str = "ollama"
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            agent_id=agent_id,
            model=model,
            model_provider=model_provider,
        )
        self.db.add(conversation)
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation
    
    async def get(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """Get a conversation by ID with messages."""
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        include_archived: bool = False,
        search_query: Optional[str] = None
    ) -> tuple[List[Conversation], int]:
        """Get all conversations for a user with optional search."""
        query = select(Conversation).where(Conversation.user_id == user_id)
        
        if not include_archived:
            query = query.where(Conversation.is_archived == False)
        
        # Apply search filter
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.where(Conversation.title.ilike(search_pattern))
        
        # Count total
        count_query = select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
        if not include_archived:
            count_query = count_query.where(Conversation.is_archived == False)
        if search_query:
            count_query = count_query.where(Conversation.title.ilike(f"%{search_query}%"))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Order by pinned first, then by updated_at
        query = query.order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        conversations = result.scalars().all()
        
        return list(conversations), total
    
    async def search(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search conversations and messages."""
        search_pattern = f"%{query}%"
        
        # Search in conversations
        conv_query = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.title.ilike(search_pattern)
        ).limit(limit)
        
        conv_result = await self.db.execute(conv_query)
        conversations = conv_result.scalars().all()
        
        results = []
        for conv in conversations:
            results.append({
                "id": conv.id,
                "type": "conversation",
                "title": conv.title,
                "snippet": conv.title,
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "relevance": 1.0
            })
        
        return results[:limit]
    
    async def update(
        self,
        conversation_id: str,
        user_id: str,
        **kwargs
    ) -> Optional[Conversation]:
        """Update a conversation."""
        conversation = await self.get(conversation_id, user_id)
        if not conversation:
            return None
        
        for key, value in kwargs.items():
            if hasattr(conversation, key) and value is not None:
                setattr(conversation, key, value)
        
        conversation.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation
    
    async def update_title(
        self,
        conversation_id: str,
        user_id: str,
        title: Optional[str] = None
    ) -> Optional[Conversation]:
        """Update conversation title, auto-generate if not provided."""
        conversation = await self.get(conversation_id, user_id)
        if not conversation:
            return None
        
        if title:
            conversation.title = title
        elif not conversation.title or conversation.title == "New Chat":
            # Auto-generate title from first message
            conversation.title = await self._generate_title(conversation)
        
        conversation.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation
    
    async def _generate_title(self, conversation: Conversation) -> str:
        """Generate a title from the conversation's first message."""
        # Get the first user message
        for msg in conversation.messages:
            if msg.role == "user":
                content = msg.content.strip()
                # Take first 50 characters, clean up
                title = content[:50]
                if len(content) > 50:
                    title = title.rsplit(' ', 1)[0] + "..."
                return title or "New Chat"
        
        return "New Chat"
    
    async def delete(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation."""
        conversation = await self.get(conversation_id, user_id)
        if not conversation:
            return False
        
        await self.db.delete(conversation)
        await self.db.flush()
        return True
    
    async def archive(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """Archive a conversation."""
        return await self.update(conversation_id, user_id, is_archived=True)
    
    async def unarchive(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """Unarchive a conversation."""
        return await self.update(conversation_id, user_id, is_archived=False)
    
    async def toggle_pin(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """Toggle pin status."""
        conversation = await self.get(conversation_id, user_id)
        if not conversation:
            return None
        
        conversation.is_pinned = not conversation.is_pinned
        conversation.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation
    
    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Get conversation statistics for a user."""
        # Total conversations
        total_query = select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0
        
        # Active conversations (not archived)
        active_query = select(func.count(Conversation.id)).where(
            Conversation.user_id == user_id,
            Conversation.is_archived == False
        )
        active_result = await self.db.execute(active_query)
        active = active_result.scalar() or 0
        
        # Pinned conversations
        pinned_query = select(func.count(Conversation.id)).where(
            Conversation.user_id == user_id,
            Conversation.is_pinned == True
        )
        pinned_result = await self.db.execute(pinned_query)
        pinned = pinned_result.scalar() or 0
        
        return {
            "total": total,
            "active": active,
            "archived": total - active,
            "pinned": pinned
        }
